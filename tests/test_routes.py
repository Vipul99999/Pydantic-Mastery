"""Integration tests for FastAPI endpoints."""
import pytest

class TestLabEndpoints:
    def test_health_check(self, client):
        res = client.get("/api/lab/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"

    def test_basics_validation(self, client, sample_user_payload):
        res = client.post("/api/lab/basics/user", json=sample_user_payload)
        assert res.status_code == 200
        assert res.json()["username"] == "test_user"

    def test_playground_validate_success(self, client):
        payload = {"id": 1, "username": "playground_user", "email": "pg@test.com"}
        res = client.post("/api/lab/playground/validate?model=basics.user", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is True
        assert "schema" in data

    def test_playground_validate_failure(self, client):
        payload = {"id": 1, "username": "bad", "email": "invalid"}
        res = client.post("/api/lab/playground/validate?model=basics.user", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["valid"] is False
        assert data["error_count"] > 0
        assert "field_errors" in data

    def test_schema_export(self, client):
        res = client.get("/api/lab/playground/schema/basics.user")
        assert res.status_code == 200
        schema = res.json()
        assert "properties" in schema["schema"]
        assert "username" in schema["schema"]["properties"]