"""Kullanıcı-bazlı rate limit (in-memory sabit pencere).

MVP'de Redis YOK; süreç-içi sayaç yeterli. Her endpoint bu bağımlılığı kullanır.
"""

import time
from collections import defaultdict

from fastapi import Depends, HTTPException, status

from ..config import get_settings
from ..domain.models import User
from .deps import get_current_user


class UserRateLimiter:
    """Dakikalık sabit pencere: kullanıcı başına istek sayar."""

    def __init__(self, limit_per_minute: int) -> None:
        self.limit = limit_per_minute
        self._hits: dict[int, list[float]] = defaultdict(list)

    def check(self, user_id: int) -> None:
        now = time.monotonic()
        window_start = now - 60.0
        hits = [t for t in self._hits[user_id] if t >= window_start]
        if len(hits) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="İstek limiti aşıldı. Lütfen biraz bekle.",
                headers={"Retry-After": "60"},
            )
        hits.append(now)
        self._hits[user_id] = hits

    def reset(self) -> None:
        self._hits.clear()


_limiter = UserRateLimiter(get_settings().rate_limit_per_minute)


def get_rate_limiter() -> UserRateLimiter:
    return _limiter


async def enforce_rate_limit(
    user: User = Depends(get_current_user),
    limiter: UserRateLimiter = Depends(get_rate_limiter),
) -> None:
    limiter.check(user.id)
