"""In-memory rate limiter (token bucket per user)."""
import time
from config import RATE_LIMIT_SECONDS


class RateLimiter:
    def __init__(self, cooldown: float = RATE_LIMIT_SECONDS):
        self._last_call: dict[int, float] = {}
        self._cooldown = cooldown

    def is_allowed(self, user_id: int) -> bool:
        """Check if user can make a request."""
        now = time.monotonic()
        last = self._last_call.get(user_id, 0)
        if now - last >= self._cooldown:
            self._last_call[user_id] = now
            return True
        return False

    def remaining(self, user_id: int) -> float:
        """Seconds until user can make another request."""
        now = time.monotonic()
        last = self._last_call.get(user_id, 0)
        elapsed = now - last
        return max(0, self._cooldown - elapsed)
