from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from database.queries import admins


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user is not None and admins.is_admin(event.from_user.id)


class SuperAdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        return event.from_user is not None and admins.is_super(event.from_user.id)
