from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from backend.app.config import settings
from backend.app.schemas.auth import AuthUser, LoginCredentials, LoginResponse
from backend.app.schemas.ticker import StreamTicketResponse
from backend.app.security.dependencies import get_current_user
from backend.app.security.jwt import create_access_token, generate_stream_ticket
from backend.app.security.passwords import verify_password
from backend.app.security.rate_limit import limiter

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


_eval_hash: str | None = None


def get_eval_hash() -> str:
    global _eval_hash
    if _eval_hash is None:
        from backend.app.security.passwords import hash_password
        _eval_hash = hash_password(settings.EVAL_PASSWORD)
    return _eval_hash


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Authenticate analyst and issue 60-minute JWT Bearer token"
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: LoginCredentials
) -> LoginResponse:
    identity = credentials.username or credentials.email
    if not identity or not credentials.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )

    # In mock mode, validate against eval user using password verification
    if settings.DATA_MODE == "mock":
        is_eval_user = (identity == settings.EVAL_USERNAME or identity == "analyst@adityabirla.com")
        valid_eval_pw = verify_password(credentials.password, get_eval_hash())
        if not (is_eval_user and valid_eval_pw):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        user_profile = AuthUser(
            id="usr_mock_001",
            username=identity,
            email=identity,
            name="Lead Macro Analyst",
            role="admin"
        )
        token = create_access_token({
            "sub": user_profile.id,
            "username": user_profile.username,
            "role": user_profile.role
        })
        return LoginResponse(
            user=user_profile,
            accessToken=token,
            expiresInSeconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    # In live mode, query database
    from backend.app.db import fetch_one
    row = await fetch_one(
        "SELECT id, username, password_hash, role FROM users WHERE username = %s LIMIT 1;",
        (identity,)
    )
    if not row or not verify_password(credentials.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    user_profile = AuthUser(
        id=str(row["id"]),
        username=row["username"],
        email=row["username"],
        role=row["role"]
    )
    token = create_access_token({
        "sub": user_profile.id,
        "username": user_profile.username,
        "role": user_profile.role
    })
    return LoginResponse(
        user=user_profile,
        accessToken=token,
        expiresInSeconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get(
    "/me",
    response_model=AuthUser,
    summary="Get authenticated analyst profile"
)
async def get_me(user: AuthUser = Depends(get_current_user)) -> AuthUser:
    return user


@router.post(
    "/stream-ticket",
    response_model=StreamTicketResponse,
    summary="Acquire a single-use 30-second ticket for SSE ticker connection"
)
async def acquire_stream_ticket(
    user: AuthUser = Depends(get_current_user)
) -> StreamTicketResponse:
    ticket = generate_stream_ticket()
    return StreamTicketResponse(
        ticket=ticket,
        expires_in_seconds=settings.STREAM_TICKET_EXPIRE_SECONDS
    )


@router.post(
    "/logout",
    summary="Analyst sign-out cleanup"
)
async def logout(response: Response):
    return {"status": "ok", "message": "Session terminated successfully"}
