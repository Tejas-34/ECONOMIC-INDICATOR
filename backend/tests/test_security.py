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


def test_sql_injection_in_indicator_slug(auth_client):
    """Verify indicator routes reject malicious SQL injection slugs with 404."""
    malicious_slug = "gdp-growth' OR 1=1--"
    resp = auth_client.get(f"/api/indicators/{malicious_slug}")
    assert resp.status_code == 404


def test_cors_origin_locking(client):
    """Verify CORS headers permit FRONTEND_ORIGIN."""
    resp = client.options("/health", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET"
    })
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_startup_guard_fails_with_defaults():
    """Verify startup guard rejects default/insecure secrets in live mode (I9)."""
    from backend.app.config import Settings, validate_startup_secrets

    insecure_settings = Settings(
        DATA_MODE="live",
        ALLOW_INSECURE_DEFAULTS=False,
        JWT_SECRET="c2VjdXJlX2p3dF9zZWNyZXRfa2V5X2Zvcl9lY29ub21pY19pbmRpY2F0b3JfZGFzaGJvYXJkXzIwMjY=",
        EVAL_PASSWORD="Analyst@2026",
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/economic_indicators"
    )
    with pytest.raises(RuntimeError) as exc_info:
        validate_startup_secrets(insecure_settings)
    
    msg = str(exc_info.value)
    assert "[Startup Guard] FATAL: Refusing to start in live mode with insecure defaults" in msg
    assert "Insecure or default JWT_SECRET detected" in msg
    assert "Default EVAL_PASSWORD" in msg
    assert "Insecure default password detected in DATABASE_URL" in msg


def test_startup_guard_passes_with_allow_insecure_defaults():
    """Verify ALLOW_INSECURE_DEFAULTS=true permits startup in development."""
    from backend.app.config import Settings, validate_startup_secrets

    dev_settings = Settings(
        DATA_MODE="live",
        ALLOW_INSECURE_DEFAULTS=True,
        JWT_SECRET="c2VjdXJlX2p3dF9zZWNyZXRfa2V5X2Zvcl9lY29ub21pY19pbmRpY2F0b3JfZGFzaGJvYXJkXzIwMjY=",
        EVAL_PASSWORD="Analyst@2026"
    )
    # Should not raise exception
    validate_startup_secrets(dev_settings)


def test_startup_guard_passes_with_secure_secrets():
    """Verify validate_startup_secrets succeeds when production secrets are supplied."""
    from backend.app.config import Settings, validate_startup_secrets

    prod_settings = Settings(
        DATA_MODE="live",
        ALLOW_INSECURE_DEFAULTS=False,
        JWT_SECRET="a_very_secure_custom_production_jwt_secret_token_2026_xyz!",
        EVAL_PASSWORD="CustomProductionAnalystPassword@2026!",
        DATABASE_URL="postgresql://analyst:CustomProductionPgPass2026!@proddb:5432/economic_indicators"
    )
    validate_startup_secrets(prod_settings)


def test_rate_limiting_keys_on_real_client_ip(client):
    """Verify rate limiter extracts and keys on X-Forwarded-For client IP rather than proxy IP."""
    proxy_ip = "10.0.0.1"
    client_a = "198.51.100.1"
    client_b = "198.51.100.2"

    # Client A exhausts 5 attempts
    for i in range(5):
        resp = client.post(
            "/api/auth/login",
            json={"username": f"user_a_{i}", "password": "pwd"},
            headers={"X-Forwarded-For": f"{client_a}, {proxy_ip}"}
        )
        assert resp.status_code == 401

    # Client A 6th attempt is blocked with 429
    blocked_resp = client.post(
        "/api/auth/login",
        json={"username": "user_a_blocked", "password": "pwd"},
        headers={"X-Forwarded-For": f"{client_a}, {proxy_ip}"}
    )
    assert blocked_resp.status_code == 429

    # Client B through the same proxy has a distinct client IP and is NOT blocked
    client_b_resp = client.post(
        "/api/auth/login",
        json={"username": "user_b_ok", "password": "pwd"},
        headers={"X-Forwarded-For": f"{client_b}, {proxy_ip}"}
    )
    assert client_b_resp.status_code == 401  # 401 invalid creds, not 429 blocked!


