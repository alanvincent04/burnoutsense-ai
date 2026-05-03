#!/usr/bin/env python3
"""
BurnoutSense AI — Inference Module
Load trained model and run predictions.
"""
import numpy as np
import joblib
import os

FEATURE_ORDER = [
    "typing_speed_variation",
    "idle_time_pct",
    "session_duration_hrs",
    "break_irregularity_index",
    "work_hour_deviation",
    "task_completion_rate",
]

_model = None
_scaler = None


def _load():
    global _model, _scaler
    if _model is None:
        base = os.path.dirname(__file__)
        _model = joblib.load(os.path.join(base, "burnout_model.pkl"))
        _scaler = joblib.load(os.path.join(base, "scaler.pkl"))


def predict(features: dict) -> dict:
    """
    Predict burnout risk from a feature dictionary.

    Args:
        features: dict with keys matching FEATURE_ORDER

    Returns:
        dict: {score, level, confidence, probabilities}
    """
    _load()
    X = np.array([[features.get(f, 0) for f in FEATURE_ORDER]])
    X_scaled = _scaler.transform(X)
    proba = _model.predict_proba(X_scaled)[0]
    label = _model.predict(X_scaled)[0]
    class_map = dict(zip(_model.classes_, proba))
    score = int(
        class_map.get("High", 0) * 95 +
        class_map.get("Medium", 0) * 55 +
        class_map.get("Low", 0) * 15
    )
    return {
        "score": score,
        "level": label,
        "confidence": round(float(max(proba)), 3),
        "probabilities": {k: round(float(v), 3) for k, v in class_map.items()},
    }


if __name__ == "__main__":
    # Example prediction
    example = {
        "typing_speed_variation": 35.0,
        "idle_time_pct": 72.0,
        "session_duration_hrs": 11.5,
        "break_irregularity_index": 8.2,
        "work_hour_deviation": 3.0,
        "task_completion_rate": 42.0,
    }
    result = predict(example)
    print(f"Risk Level: {result['level']}")
    print(f"Burnout Score: {result['score']}/100")
    print(f"Confidence: {result['confidence']*100:.1f}%")
    print(f"Probabilities: {result['probabilities']}")
