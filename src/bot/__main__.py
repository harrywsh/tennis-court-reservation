import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from src.bot.config import Settings
from src.bot.db.engine import init_db
from src.bot.handlers import register_routers
from src.bot.middlewares.db import DbSessionMiddleware


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = Settings()

    session_factory = await init_db(settings.db_path)

    # Seed admin into allowed_users
    from src.bot.db.repository import ensure_user

    async with session_factory() as session:
        await ensure_user(session, settings.admin_id, "Admin")
        await session.commit()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()
    dp["settings"] = settings
    dp.update.middleware(DbSessionMiddleware(session_factory))

    register_routers(dp)

    logging.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
