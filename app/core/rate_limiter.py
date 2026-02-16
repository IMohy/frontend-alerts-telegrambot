import time
from collections import defaultdict


class RateLimiter:
    """Sliding window rate limiter to prevent Telegram API spam."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str = "global") -> bool:
        now = time.time()
        window_start = now - self.window_seconds

        self._requests[key] = [
            ts for ts in self._requests[key] if ts > window_start
        ]

        if len(self._requests[key]) >= self.max_requests:
            return False

        self._requests[key].append(now)
        return True

    def remaining(self, key: str = "global") -> int:
        now = time.time()
        window_start = now - self.window_seconds
        self._requests[key] = [
            ts for ts in self._requests[key] if ts > window_start
        ]
        return max(0, self.max_requests - len(self._requests[key]))

    def reset_time(self, key: str = "global") -> float | None:
        if not self._requests[key]:
            return None
        return self._requests[key][0] + self.window_seconds
