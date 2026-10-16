from datetime import datetime, timedelta, timezone
import secrets
import time
from typing import Any, Dict, Optional
import jwt
from backend.app.config import settings

# In-memory single-use tickets registry: ticket -> expiration_time_float
_active_tickets: Dict[str, float] = {}


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Issue a signed JWT access token using HMAC-SHA256."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp())
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify signature and expiration of a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except (jwt.PyJWTError, Exception):
        return None


def generate_stream_ticket() -> str:
    """Generate a single-use 30-second validity ticket for SSE ticker stream authorization."""
    _purge_expired_tickets()
    ticket = secrets.token_urlsafe(32)
    expires_at = time.time() + settings.STREAM_TICKET_EXPIRE_SECONDS
    _active_tickets[ticket] = expires_at
    return ticket


def consume_stream_ticket(ticket: str) -> bool:
    """Verify and immediately consume a single-use stream ticket.

    Returns True if ticket was valid and consumed, False otherwise.
    """
    _purge_expired_tickets()
    expires_at = _active_tickets.pop(ticket, None)
    if expires_at is None:
        return False
    return time.time() <= expires_at


def _purge_expired_tickets() -> None:
    """Remove expired tickets from memory."""
    now = time.time()
    expired = [t for t, exp in _active_tickets.items() if exp < now]
    for t in expired:
        _active_tickets.pop(t, None)
