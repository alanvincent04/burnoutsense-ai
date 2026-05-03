#!/usr/bin/env python3
"""
BurnoutSense AI — ML Model Training Pipeline
Trains a Random Forest classifier on behavioral features.
"""
import numpy as np
import pandas as pd
import joblib
import logging
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

np.random.seed(42)

# ── FEATURE DEFINITIONS ───────────────────────────────────────────────────────
FEATURES = [
    "typing_speed_variation",   # WPM spread — cognitive fatigue indicator
    "idle_time_pct",            # % of session inactive
    "session_duration_hrs",     # continuous hours worked
    "break_irregularity_index", # 0-10 scale
    "work_hour_deviation",      # hours from 9AM baseline
    "task_completion_rate",     # 0-100%
]

LABELS = ["Low", "Medium", "High"]


def generate_synthetic_dataset(n_low=1800, n_medium=800, n_high=400) -> pd.DataFrame:
    """
    Generate synthetic behavioral data with realistic distributions.
    Replace with real employee logs in production.
    """
    rows, labels = [], []

    def sample(level):
        if level == "Low":
            return [
                np.random.normal(38, 12),        # typing variation
                np.random.uniform(5, 28),         # idle pct
                np.random.uniform(4.5, 7.5),      # session hrs
                np.random.uniform(0.5, 3.0),      # break irregularity
                np.random.uniform(0, 1.5),         # hr deviation
                np.random.uniform(68, 100),        # task rate
            ]
        elif level == "Medium":
            return [
                np.random.normal(24, 10),
                np.random.uniform(28, 58),
                np.random.uniform(7.5, 10.5),
                np.random.uniform(3.0, 6.5),
                np.random.uniform(1.5, 3.5),
                np.random.uniform(38, 68),
            ]
        else:  # High
            return [
                np.random.normal(14, 8),
                np.random.uniform(58, 92),
                np.random.uniform(10.5, 15.5),
                np.random.uniform(6.5, 10.0),
                np.random.uniform(3.5, 6.0),
                np.random.uniform(8, 38),
            ]

    for label, n in [("Low", n_low), ("Medium", n_medium), ("High", n_high)]:
        for _ in range(n):
            rows.append(sample(label))
            labels.append(label)

    df = pd.DataFrame(rows, columns=FEATURES)
    df["label"] = labels
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    logger.info(f"Dataset: {len(df)} samples — {df.label.value_counts().to_dict()}")
    return df


def train_model(df: pd.DataFrame):
    """Full training pipeline with grid search and cross-validation."""
    X, y = df[FEATURES], df["label"]

    # Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Feature scaling
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Hyperparameter search
    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [None, 10, 20],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
        "max_features": ["sqrt", "log2"],
    }

    logger.info("Running GridSearchCV (this may take a few minutes)...")
    rf = GridSearchCV(
        RandomForestClassifier(random_state=42, class_weight="balanced"),
        param_grid,
        cv=5,
        scoring="f1_weighted",
        n_jobs=-1,
        verbose=1
    )
    rf.fit(X_train_s, y_train)

    best_model = rf.best_estimator_
    logger.info(f"Best params: {rf.best_params_}")

    # Cross-validation
    cv_scores = cross_val_score(best_model, X_train_s, y_train, cv=5, scoring="accuracy")
    logger.info(f"CV Accuracy: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    # Final evaluation
    y_pred = best_model.predict(X_test_s)
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    print(classification_report(y_test, y_pred, target_names=LABELS))

    print("CONFUSION MATRIX")
    print(confusion_matrix(y_test, y_pred, labels=LABELS))

    # Feature importance
    print("\nFEATURE IMPORTANCE")
    for feat, imp in sorted(zip(FEATURES, best_model.feature_importances_),
                             key=lambda x: -x[1]):
        print(f"  {feat:35s}: {imp:.3f} ({imp*100:.1f}%)")

    return best_model, scaler


def save_model(model, scaler, model_path="burnout_model.pkl", scaler_path="scaler.pkl"):
    """Save trained model and scaler to disk."""
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    logger.info(f"Model saved: {model_path}")
    logger.info(f"Scaler saved: {scaler_path}")


if __name__ == "__main__":
    logger.info("Starting BurnoutSense AI training pipeline...")
    df = generate_synthetic_dataset()
    model, scaler = train_model(df)
    save_model(model, scaler)
    logger.info("Training complete!")
