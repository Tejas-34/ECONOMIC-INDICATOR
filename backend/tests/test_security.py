import pytest
from backend.app.config import settings


def test_sql_injection_payload_in_login(client):
    """Verify SQL injection payloads in login input are safely handled as string literals."""
    payloads = [
        "' OR '1'='1",
        "admin' --",
        "'; DROP TABLE users; --",
        "' UNION SELECT 1, 'admin', 'hash', 'admin', NOW() --"
    ]
    for p in payloads:
        resp = client.post("/api/auth/login", json={"username": p, "password": "password"})
        assert resp.status_code == 401
        assert "Invalid username or password" in resp.json()["detail"]


def test_rate_limiting_exceeded_on_login(client):
    """Verify 6th request within 1 minute from same IP returns HTTP 429."""
    for i in range(5):
        resp = client.post("/api/auth/login", json={"username": f"user_{i}", "password": "pwd"})
        assert resp.status_code == 401

    # 6th attempt trips rate limit
    blocked_resp = client.post("/api/auth/login", json={"username": "user_blocked", "password": "pwd"})
    assert blocked_resp.status_code == 429


def test_sql_injection_in_indicator_slug(client):
    """Verify indicator routes reject malicious SQL injection slugs with 404."""
    malicious_slug = "gdp-growth' OR 1=1--"
    resp = client.get(f"/api/indicators/{malicious_slug}")
    assert resp.status_code == 404


def test_cors_origin_locking(client):
    """Verify CORS headers permit FRONTEND_ORIGIN."""
    resp = client.options("/health", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    })
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
