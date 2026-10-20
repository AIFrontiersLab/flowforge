"""
Tests for Flowforge MVP

Covers startup, happy path, and failure path scenarios.
"""
import pytest
from fastapi.testclient import TestClient
from main import app, process_workflow, WorkflowPayload, db_high_priority, db_logs

client = TestClient(app)

def test_startup():
    """Test that the app starts and health endpoint works."""
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"

def test_happy_path_standard():
    """Test standard workflow classification and logging."""
    payload = WorkflowPayload(data="Regular user request")
    response = client.post("/webhook", json=payload.dict())
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["classification"] == "standard"
    assert "logged_to_local_db" in data["action_taken"]
    assert len(db_logs) > 0

def test_happy_path_high_priority():
    """Test high priority workflow routing."""
    payload = WorkflowPayload(data="Urgent: System down")
    response = client.post("/webhook", json=payload.dict())
    
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "high_priority"
    assert "sent_to_external_api" in data["action_taken"]
    assert len(db_high_priority) > 0

def test_failure_path_empty_data():
    """Test handling of missing data field."""
    response = client.post("/webhook", json={"data": ""})
    assert response.status_code == 400

def test_failure_path_invalid_payload():
    """Test handling of invalid JSON payload."""
    response = client.post("/webhook", content="not json", headers={"content-type": "application/json"})
    assert response.status_code == 422