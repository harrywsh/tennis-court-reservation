from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.db import repository as repo
from src.bot.filters.auth import AdminFilter
from src.bot.keyboards.common import AdminCancelCallback

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(Command("admin"))
async def cmd_admin(message: Message) -> None:
    await message.answer(
        "<b>Admin commands:</b>\n\n"
        "/toggle — Enable/disable reservations\n"
        "/allbookings — View all bookings\n"
        "/adduser &lt;id&gt; &lt;name&gt; — Add user\n"
        "/removeuser &lt;id&gt; — Remove user\n"
        "/users — List allowed users"
    )


@router.message(Command("toggle"))
async def cmd_toggle(message: Message, session: AsyncSession) -> None:
    enabled = await repo.toggle_reservations(session)
    status = "ENABLED" if enabled else "DISABLED"
    await message.answer(f"Reservations are now <b>{status}</b>.")


@router.message(Command("allbookings"))
async def cmd_all_bookings(message: Message, session: AsyncSession) -> None:
    reservations = await repo.get_all_reservations(session)
    if not reservations:
        await message.answer("No upcoming bookings.")
        return

    lines: list[str] = ["<b>All upcoming bookings:</b>\n"]
    buttons: list[list[InlineKeyboardButton]] = []
    for r in reservations:
        lines.append(
            f"#{r.id} — {r.date.strftime('%a %b %d')} "
            f"{r.start_time.strftime('%H:%M')}–{r.end_time.strftime('%H:%M')} "
            f"({r.user.display_name})"
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"Cancel #{r.id} ({r.user.display_name})",
                callback_data=AdminCancelCallback(reservation_id=r.id).pack(),
            )
        ])

    await message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
    )


@router.callback_query(AdminCancelCallback.filter())
async def on_admin_cancel(
    callback: CallbackQuery,
    callback_data: AdminCancelCallback,
    session: AsyncSession,
) -> None:
    success = await repo.cancel_reservation(session, callback_data.reservation_id)
    if success:
        await callback.answer("Booking cancelled.", show_alert=True)
        # Refresh
        reservations = await repo.get_all_reservations(session)
        if not reservations:
            await callback.message.edit_text("No upcoming bookings.")
        else:
            lines: list[str] = ["<b>All upcoming bookings:</b>\n"]
            buttons: list[list[InlineKeyboardButton]] = []
            for r in reservations:
                lines.append(
                    f"#{r.id} — {r.date.strftime('%a %b %d')} "
                    f"{r.start_time.strftime('%H:%M')}–{r.end_time.strftime('%H:%M')} "
                    f"({r.user.display_name})"
                )
                buttons.append([
                    InlineKeyboardButton(
                        text=f"Cancel #{r.id} ({r.user.display_name})",
                        callback_data=AdminCancelCallback(reservation_id=r.id).pack(),
                    )
                ])
            await callback.message.edit_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            )
    else:
        await callback.answer("Booking not found.", show_alert=True)


@router.message(Command("adduser"))
async def cmd_add_user(message: Message, session: AsyncSession) -> None:
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Usage: /adduser &lt;telegram_id&gt; &lt;display_name&gt;")
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer("Invalid Telegram ID. Must be a number.")
        return

    display_name = parts[2]
    user = await repo.ensure_user(session, telegram_id, display_name)
    await message.answer(f"User <b>{user.display_name}</b> (<code>{user.telegram_id}</code>) added.")


@router.message(Command("removeuser"))
async def cmd_remove_user(message: Message, session: AsyncSession) -> None:
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /removeuser &lt;telegram_id&gt;")
        return

    try:
        telegram_id = int(parts[1])
    except ValueError:
        await message.answer("Invalid Telegram ID. Must be a number.")
        return

    success = await repo.remove_user(session, telegram_id)
    if success:
        await message.answer(f"User <code>{telegram_id}</code> removed.")
    else:
        await message.answer("User not found.")


@router.message(Command("users"))
async def cmd_users(message: Message, session: AsyncSession) -> None:
    users = await repo.list_allowed_users(session)
    if not users:
        await message.answer("No users in the allowlist.")
        return

    lines = ["<b>Allowed users:</b>\n"]
    for u in users:
        lines.append(f"• {u.display_name} (<code>{u.telegram_id}</code>)")

    await message.answer("\n".join(lines))
