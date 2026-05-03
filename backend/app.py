#!/usr/bin/env python3
"""
BurnoutSense AI — Flask REST API
Provides endpoints for data ingestion, ML prediction, and dashboard data.
"""
import os
import logging
from datetime import datetime
from functools import wraps

import jwt
import numpy as np
import joblib
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "*").split(","))

# ── Database connection ──────────────────────────────────────────────────────
mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
db = mongo_client["burnout_db"]

# ── ML Model loading ─────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../ml/burnout_model.pkl")
SCALER_PATH = os.path.join(os.path.dirname(__file__), "../ml/scaler.pkl")

try:
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    logger.info("ML model and scaler loaded successfully")
except FileNotFoundError:
    logger.warning("Model not found. Run ml/train.py first.")
    model, scaler = None, None

# ── Authentication ────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-prod")
JWT_ALGO = "HS256"


def require_auth(f):
    """JWT authentication decorator."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            g.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": f"Invalid token: {e}"}), 401
        return f(*args, **kwargs)
    return decorated


def require_role(*roles):
    """Role-based access control decorator."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, "current_user"):
                return jsonify({"error": "Not authenticated"}), 401
            if g.current_user.get("role") not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── ML Inference ─────────────────────────────────────────────────────────────
FEATURE_ORDER = [
    "typing_speed_variation",
    "idle_time_pct",
    "session_duration_hrs",
    "break_irregularity_index",
    "work_hour_deviation",
    "task_completion_rate",
]


def predict_burnout_score(data: dict) -> dict:
    """
    Run ML inference on behavioral feature data.
    Returns: score (0-100), risk level, confidence.
    """
    if model is None or scaler is None:
        return {"score": 0, "level": "Unknown", "confidence": 0.0,
                "error": "Model not loaded"}

    features = np.array([[data.get(f, 0) for f in FEATURE_ORDER]])
    scaled = scaler.transform(features)

    proba = model.predict_proba(scaled)[0]
    label = model.predict(scaled)[0]

    # Map class probabilities to a 0-100 score
    # Assumes class order: High, Low, Medium (alphabetical by sklearn)
    class_order = sorted(model.classes_)
    proba_map = dict(zip(class_order, proba))

    score = int(
        proba_map.get("High", 0) * 95 +
        proba_map.get("Medium", 0) * 55 +
        proba_map.get("Low", 0) * 15
    )

    return {
        "score": score,
        "level": label,
        "confidence": round(float(max(proba)), 3),
        "probabilities": {k: round(float(v), 3) for k, v in proba_map.items()}
    }


def check_and_send_alerts(employee_id: str, score: dict):
    """Trigger alerts for medium and high risk employees."""
    if score["level"] in ("High", "Medium"):
        alert = {
            "employee_id": employee_id,
            "level": score["level"].lower(),
            "score": score["score"],
            "message": (
                f"{score['level']} burnout risk detected "
                f"(score: {score['score']}, confidence: {score['confidence']})"
            ),
            "timestamp": datetime.utcnow(),
            "read": False,
        }
        db.alerts.insert_one(alert)

        if score["level"] == "High":
            logger.warning(
                f"HIGH RISK ALERT: Employee {employee_id} — Score {score['score']}"
            )
            # TODO: Integrate AWS SES for email notification
            # send_email_alert(employee_id, score)


# ── API ROUTES ────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    """Health check endpoint for load balancer."""
    return jsonify({"status": "healthy", "model_loaded": model is not None}), 200


@app.route("/api/v1/activity/log", methods=["POST"])
def log_activity():
    """
    Ingest behavioral activity data from client agent.
    Triggers ML prediction and stores burnout score.
    """
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # Validate required fields
    required = ["employee_id"] + FEATURE_ORDER[:4]  # At minimum need 4 features
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    # Store raw activity log
    data["logged_at"] = datetime.utcnow()
    db.activity_logs.insert_one(data)

    # Run prediction
    score = predict_burnout_score(data)

    # Store burnout score
    db.burnout_scores.insert_one({
        "employee_id": data["employee_id"],
        "score": score["score"],
        "risk_level": score["level"],
        "confidence": score["confidence"],
        "timestamp": datetime.utcnow(),
    })

    # Trigger alerts if needed
    check_and_send_alerts(data["employee_id"], score)

    return jsonify({"status": "logged", "risk": score}), 201


@app.route("/api/v1/burnout/score/<emp_id>")
@require_auth
def get_score(emp_id):
    """Get the latest burnout score for an employee."""
    # Employees can only access their own scores
    if g.current_user.get("role") == "employee" and g.current_user.get("sub") != emp_id:
        return jsonify({"error": "Access denied"}), 403

    latest = db.burnout_scores.find_one(
        {"employee_id": emp_id},
        sort=[("timestamp", -1)],
        projection={"_id": 0}
    )
    if not latest:
        return jsonify({"error": "No data found"}), 404
    return jsonify(latest), 200


@app.route("/api/v1/burnout/predict", methods=["POST"])
def predict():
    """Run burnout prediction on provided feature data (no logging)."""
    data = request.json
    result = predict_burnout_score(data)
    return jsonify(result), 200


@app.route("/api/v1/employees/list")
@require_auth
@require_role("manager", "admin")
def list_employees():
    """Get paginated employee list with latest risk levels (managers/admins only)."""
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 50))
    department = request.args.get("department")

    query = {}
    if department:
        query["department"] = department

    employees = list(db.employees.find(query, projection={"_id": 0, "password_hash": 0})
                     .skip((page-1)*per_page).limit(per_page))

    # Attach latest scores
    for emp in employees:
        score = db.burnout_scores.find_one(
            {"employee_id": emp["employee_id"]},
            sort=[("timestamp", -1)],
            projection={"_id": 0}
        )
        emp["latest_score"] = score

    return jsonify({
        "employees": employees,
        "page": page,
        "per_page": per_page,
        "total": db.employees.count_documents(query)
    }), 200


@app.route("/api/v1/alerts/active")
@require_auth
@require_role("manager", "admin")
def get_alerts():
    """Get unread burnout alerts (managers/admins only)."""
    alerts = list(db.alerts.find(
        {"read": False},
        projection={"_id": 0},
        sort=[("timestamp", -1)],
        limit=100
    ))
    return jsonify({"alerts": alerts, "count": len(alerts)}), 200


@app.route("/api/v1/employees/<emp_id>/threshold", methods=["PUT"])
@require_auth
@require_role("admin")
def update_threshold(emp_id):
    """Update custom risk thresholds for an employee (admins only)."""
    data = request.json
    medium = data.get("medium", 45)
    high = data.get("high", 70)

    if not (0 <= medium < high <= 100):
        return jsonify({"error": "Invalid thresholds: must be 0 <= medium < high <= 100"}), 400

    db.employees.update_one(
        {"employee_id": emp_id},
        {"$set": {"custom_threshold": {"medium": medium, "high": high}}}
    )
    return jsonify({"status": "updated", "employee_id": emp_id,
                    "threshold": {"medium": medium, "high": high}}), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
