"""Sliding-window in-memory rate limiter for protecting API write endpoints."""

from collections import defaultdict, deque
import math
import time

from fastapi import HTTPException, Request, status

from shorty_api.core.config import settings


class SlidingWindowRateLimiter:
    """Tracks recent request timestamps per client key inside a rolling window."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, client_key: str) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds) for the given client_key."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        timestamps = self._requests[client_key]

        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if not timestamps:
            self._requests.pop(client_key, None)
            timestamps = self._requests[client_key]

        if len(timestamps) >= self.max_requests:
            retry_after = max(1, math.ceil(self.window_seconds - (now - timestamps[0])))
            return False, retry_after

        timestamps.append(now)
        return True, 0

    def reset(self) -> None:
        """Clear all tracked client windows (useful in isolated tests)."""
        self._requests.clear()


rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


def _extract_client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency that blocks requests exceeding the configured rate limit."""
    client_ip = _extract_client_ip(request)
    allowed, retry_after = rate_limiter.check(client_ip)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Demasiadas peticiones. Intenta nuevamente en {retry_after} segundo(s)."
            ),
            headers={"Retry-After": str(retry_after)},
        )
