from typing import Callable, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.app.config import settings
from backend.app.schemas.auth import AuthUser
from backend.app.security.jwt import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AuthUser:
    """Validate Bearer JWT access token and return authenticated AuthUser profile."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = str(payload.get("sub", ""))
    username = str(payload.get("username", ""))
    role = str(payload.get("role", "viewer"))

    if settings.DATA_MODE == "mock":
        return AuthUser(
            id=user_id or "usr_mock_001",
            username=username or settings.EVAL_USERNAME,
            email=username or settings.EVAL_USERNAME,
            name="Lead Macro Analyst",
            role=role
        )

    # In live mode, verify user existence in database
    from backend.app.db import fetch_one
    row = await fetch_one(
        "SELECT id, username, role FROM users WHERE username = %s LIMIT 1;",
        (username,)
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthUser(
        id=str(row["id"]),
        username=row["username"],
        email=row["username"],
        role=row["role"]
    )


def require_role(required_role: str) -> Callable[[AuthUser], AuthUser]:
    """Dependency factory checking that the authenticated user possesses the required role."""
    def role_checker(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role != required_role and user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{required_role}' privileges"
            )
        return user
    return role_checker
