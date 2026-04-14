"""Tests for Request ID middleware."""
import pytest
import re

class TestRequestIDMiddleware:
    def test_generates_id_when_missing(self, client):
        res = client.get("/api/lab/health")
        assert "x-request-id" in res.headers
        assert re.match(r'^[a-f0-9]{8}$', res.headers["x-request-id"])

    def test_preserves_client_id(self, client):
        custom_id = "test-trace-12345"
        res = client.get("/api/lab/health", headers={"X-Request-ID": custom_id})
        assert res.headers["x-request-id"] == custom_id