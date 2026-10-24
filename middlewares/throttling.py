import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message


class ThrottlingMiddleware(BaseMiddleware):
    """Bir foydalanuvchidan juda tez kelgan xabarlarni tashlab yuboradi."""

    def __init__(self, rate: float = 0.4) -> None:
        self.rate = rate
        self._last: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        user = event.from_user
        # Albomlar (media_group) bir vaqtda keladi — ularni cheklamaymiz
        if user is not None and event.media_group_id is None:
            now = time.monotonic()
            if now - self._last.get(user.id, 0) < self.rate:
                return None
            self._last[user.id] = now
        return await handler(event, data)
