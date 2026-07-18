# File: app/ai/validator/rate_limiter.py
"""
(`Guardrails: Rate Limiting`)
In-memory rate limiting to prevent API abuse.
Tracks requests per user/IP within time windows.
"""
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from threading import Lock

logger = logging.getLogger("app.ai.validator.rate_limiter")


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_in_seconds: float
    limit_type: str = "minute"


class RateLimiter:
    """
    Token-bucket style rate limiter using sliding window.
    Tracks requests per key (user_id or IP) within minute and hour windows.
    """

    def __init__(self, per_minute: int = 60, per_hour: int = 1000):
        self.per_minute = per_minute
        self.per_hour = per_hour
        self._minute_window: Dict[str, list] = defaultdict(list)
        self._hour_window: Dict[str, list] = defaultdict(list)
        self._lock = Lock()

    def _cleanup_old_timestamps(self, timestamps: list, window_seconds: float) -> None:
        """Remove timestamps outside the window."""
        now = time.time()
        cutoff = now - window_seconds
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)

    def check(self, key: str) -> RateLimitResult:
        """
        Check if request is allowed. Returns (allowed, remaining, reset_time).
        """
        with self._lock:
            now = time.time()
            minute_cutoff = now - 60
            hour_cutoff = now - 3600

            minute_requests = [t for t in self._minute_window[key] if t > minute_cutoff]
            hour_requests = [t for t in self._hour_window[key] if t > hour_cutoff]

            self._minute_window[key] = minute_requests
            self._hour_window[key] = hour_requests

            if len(minute_requests) >= self.per_minute:
                oldest = min(minute_requests)
                reset_time = 60 - (now - oldest)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_in_seconds=max(0, reset_time),
                    limit_type="minute"
                )

            if len(hour_requests) >= self.per_hour:
                oldest = min(hour_requests)
                reset_time = 3600 - (now - oldest)
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_in_seconds=max(0, reset_time),
                    limit_type="hour"
                )

            minute_requests.append(now)
            hour_requests.append(now)

            return RateLimitResult(
                allowed=True,
                remaining=self.per_minute - len(minute_requests),
                reset_in_seconds=60.0,
                limit_type="minute"
            )

    def reset(self, key: str) -> None:
        """Reset rate limits for a specific key."""
        with self._lock:
            self._minute_window.pop(key, None)
            self._hour_window.pop(key, None)


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter(per_minute: int = 60, per_hour: int = 1000) -> RateLimiter:
    """Returns singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(per_minute=per_minute, per_hour=per_hour)
    return _rate_limiter


def check_rate_limit(user_id: str, per_minute: int = 60, per_hour: int = 1000) -> RateLimitResult:
    """Convenience function to check rate limit for a user."""
    limiter = get_rate_limiter(per_minute=per_minute, per_hour=per_hour)
    return limiter.check(user_id)