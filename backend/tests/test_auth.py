from datetime import timedelta
import pytest
from backend.app.config import settings
from backend.app.security.jwt import create_access_token, generate_stream_ticket, consume_stream_ticket


def test_login_success(client):
    response = client.post("/api/auth/login", json={
        "username": settings.EVAL_USERNAME,
        "password": "Analyst@2026"
    })
    assert response.status_code == 200
    data = response.json()
    assert "accessToken" in data
    assert data["user"]["username"] == settings.EVAL_USERNAME
    assert data["expiresInSeconds"] == 3600


def test_login_invalid_password(client):
    response = client.post("/api/auth/login", json={
        "username": settings.EVAL_USERNAME,
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


def test_auth_me_protected(client):
    # Unauthenticated
    unauth_resp = client.get("/api/auth/me")
    assert unauth_resp.status_code == 401

    # Authenticated
    login_resp = client.post("/api/auth/login", json={
        "username": settings.EVAL_USERNAME,
        "password": "Analyst@2026"
    })
    token = login_resp.json()["accessToken"]

    auth_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert auth_resp.status_code == 200
    assert auth_resp.json()["username"] == settings.EVAL_USERNAME


def test_expired_jwt_token(client):
    expired_token = create_access_token(
        {"sub": "usr_test", "username": "analyst@adityabirla.com", "role": "admin"},
        expires_delta=timedelta(seconds=-10)
    )
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    assert "Invalid or expired access token" in resp.json()["detail"]


def test_single_use_stream_ticket():
    ticket = generate_stream_ticket()
    assert isinstance(ticket, str) and len(ticket) > 16

    # First consumption succeeds
    assert consume_stream_ticket(ticket) is True

    # Replay/second consumption fails
    assert consume_stream_ticket(ticket) is False
