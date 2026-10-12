#!/usr/bin/env python3
"""Test suite for the Flask app — should pass after all 3 bugs are fixed."""
import json
import os
import sys
import pytest

# Add parent dir to path
sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture
def client():
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_status(client):
    """GET /api/status should return ok."""
    rv = client.get("/api/status")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "ok"
    assert "version" in data


def test_greet_default(client):
    """GET /api/greet without name should greet World."""
    rv = client.get("/api/greet")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert "Hello, World!" in data["greeting"]


def test_greet_named(client):
    """GET /api/greet?name=Alice should greet Alice."""
    rv = client.get("/api/greet?name=Alice")
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert "Alice" in data["greeting"]


def test_log(client):
    """GET /api/log should log and not leak file handles."""
    import resource
    before = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    for _ in range(10):
        rv = client.get("/api/log?msg=test")
        assert rv.status_code == 200

    # Check the log file exists and has content
    log_path = os.path.join(os.path.dirname(__file__), "app.log")
    assert os.path.isfile(log_path)
    with open(log_path) as f:
        lines = f.readlines()
    assert len(lines) >= 10
