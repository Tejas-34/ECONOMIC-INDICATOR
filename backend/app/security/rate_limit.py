from starlette.requests import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_real_client_ip(request: Request) -> str:
    """Extract real client IP from X-Forwarded-For or X-Real-IP headers behind reverse proxy."""
    forwarded_for = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip") or request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return get_remote_address(request)


# Global IP-based rate limiter using real client IP behind proxy
limiter = Limiter(key_func=get_real_client_ip)

