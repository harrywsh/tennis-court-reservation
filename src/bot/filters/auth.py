from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.config import Settings
from src.bot.db.repository import is_allowed


class AllowlistFilter(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        session: AsyncSession,
        settings: Settings,
    ) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        if user_id == settings.admin_id:
            return True
        return await is_allowed(session, user_id)


class AdminFilter(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        settings: Settings,
    ) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        return user_id == settings.admin_id
