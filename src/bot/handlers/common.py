from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.config import Settings
from src.bot.db.repository import is_allowed

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, settings: Settings) -> None:
    user_id = message.from_user.id if message.from_user else 0
    is_admin = user_id == settings.admin_id
    allowed = is_admin or await is_allowed(session, user_id)

    if is_admin:
        text = (
            "Welcome, admin! You manage this tennis court.\n\n"
            "Use /help to see available commands."
        )
    elif allowed:
        text = (
            "Welcome! You have access to book the tennis court.\n\n"
            "Use /help to see available commands."
        )
    else:
        text = (
            "Hi! You don't have access to book yet.\n"
            f"Your Telegram ID is <code>{user_id}</code>.\n"
            "Send this to the court owner to get access."
        )
    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession, settings: Settings) -> None:
    user_id = message.from_user.id if message.from_user else 0
    is_admin = user_id == settings.admin_id
    allowed = is_admin or await is_allowed(session, user_id)

    lines = ["<b>Available commands:</b>\n"]
    if allowed:
        lines.append("/book — Reserve a time slot")
        lines.append("/mybookings — View your upcoming bookings")
    if is_admin:
        lines.append("\n<b>Admin commands:</b>")
        lines.append("/toggle — Enable/disable reservations")
        lines.append("/allbookings — View all bookings")
        lines.append("/adduser &lt;id&gt; &lt;name&gt; — Add user to allowlist")
        lines.append("/removeuser &lt;id&gt; — Remove user")
        lines.append("/users — List allowed users")
    if not allowed:
        lines.append("You don't have access yet. Send your Telegram ID to the owner.")

    await message.answer("\n".join(lines))
