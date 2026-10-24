from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from keyboards.reply import ADMIN_BUTTONS, MAIN_BUTTONS

MENU_TEXTS = set(ADMIN_BUTTONS) | set(MAIN_BUTTONS)


class MenuResetMiddleware(BaseMiddleware):
    """Menyu tugmasi bosilsa, tugallanmagan kiritish (FSM) bekor qilinadi —
    tugma matni hech qachon maydon qiymati sifatida saqlanib qolmaydi."""

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if event.text in MENU_TEXTS and data.get("raw_state") is not None:
            await data["state"].clear()
            data["raw_state"] = None
        return await handler(event, data)
