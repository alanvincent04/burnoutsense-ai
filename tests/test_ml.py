#!/usr/bin/env python3
"""ML model unit tests."""
import pytest
import numpy as np
from ml.predict import predict, FEATURE_ORDER


def make_features(level="low"):
    """Generate features for a given risk level."""
    if level == "low":
        return dict(zip(FEATURE_ORDER, [10, 15, 6, 1.5, 0.5, 90]))
    elif level == "medium":
        return dict(zip(FEATURE_ORDER, [25, 45, 9, 5.0, 2.0, 55]))
    else:
        return dict(zip(FEATURE_ORDER, [40, 80, 13, 8.5, 4.5, 25]))


def test_low_risk_prediction():
    result = predict(make_features("low"))
    assert result["level"] in ("Low", "Medium")
    assert result["score"] < 60


def test_high_risk_prediction():
    result = predict(make_features("high"))
    assert result["level"] in ("Medium", "High")
    assert result["score"] > 40


def test_score_range():
    for level in ("low", "medium", "high"):
        result = predict(make_features(level))
        assert 0 <= result["score"] <= 100, f"Score out of range for {level}"


def test_confidence_range():
    result = predict(make_features("medium"))
    assert 0.0 <= result["confidence"] <= 1.0


def test_missing_features_handled():
    """Missing features should use 0 as default without crashing."""
    result = predict({"idle_time_pct": 50})
    assert "score" in result
    assert "level" in result
