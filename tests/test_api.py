#!/usr/bin/env python3
"""
BurnoutSense AI — API Test Suite
Run with: pytest tests/ -v
"""
import pytest
import json
from backend.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers():
    from backend.auth import generate_token
    token = generate_token("test_emp_001", "employee")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def manager_headers():
    from backend.auth import generate_token
    token = generate_token("test_mgr_001", "manager")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def test_health_check(client):
    """Health endpoint returns 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["status"] == "healthy"


def test_log_activity_unauthenticated(client):
    """Unauthenticated requests are rejected."""
    resp = client.post("/api/v1/activity/log", json={"employee_id": "test"})
    assert resp.status_code == 401


def test_log_activity_valid(client, auth_headers):
    """Valid activity data is accepted and scored."""
    payload = {
        "employee_id": "test_emp_001",
        "typing_speed_variation": 15.0,
        "idle_time_pct": 72.0,
        "session_duration_hrs": 10.5,
        "break_irregularity_index": 8.0,
        "work_hour_deviation": 3.0,
        "task_completion_rate": 42.0,
    }
    resp = client.post("/api/v1/activity/log", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert "risk" in data
    assert data["risk"]["level"] in ("Low", "Medium", "High")
    assert 0 <= data["risk"]["score"] <= 100


def test_predict_endpoint(client, auth_headers):
    """Prediction endpoint returns valid risk assessment."""
    payload = {
        "typing_speed_variation": 40.0,
        "idle_time_pct": 25.0,
        "session_duration_hrs": 6.0,
        "break_irregularity_index": 2.0,
        "work_hour_deviation": 0.5,
        "task_completion_rate": 85.0,
    }
    resp = client.post("/api/v1/burnout/predict", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["level"] in ("Low", "Medium", "High")
    assert 0.0 <= data["confidence"] <= 1.0


def test_employee_cannot_access_others(client, auth_headers):
    """Employees cannot access other employees\' scores."""
    resp = client.get("/api/v1/burnout/score/other_emp_999", headers=auth_headers)
    assert resp.status_code == 403


def test_alerts_require_manager(client, auth_headers):
    """Alert endpoint requires manager role."""
    resp = client.get("/api/v1/alerts/active", headers=auth_headers)
    assert resp.status_code == 403


def test_alerts_accessible_by_manager(client, manager_headers):
    """Managers can access alerts."""
    resp = client.get("/api/v1/alerts/active", headers=manager_headers)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "alerts" in data
    assert "count" in data
