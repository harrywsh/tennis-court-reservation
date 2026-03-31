from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.db.repository import cancel_reservation_if_owned, get_user_reservations
from src.bot.filters.auth import AllowlistFilter
from src.bot.keyboards.common import CancelBookingCallback

router = Router(name="my_bookings")
router.message.filter(AllowlistFilter())
router.callback_query.filter(AllowlistFilter())


@router.message(Command("mybookings"))
async def cmd_my_bookings(
    message: Message,
    session: AsyncSession,
) -> None:
    reservations = await get_user_reservations(session, message.from_user.id)
    if not reservations:
        await message.answer("You have no upcoming bookings.")
        return

    lines: list[str] = ["<b>Your upcoming bookings:</b>\n"]
    buttons: list[list[InlineKeyboardButton]] = []
    for r in reservations:
        lines.append(
            f"#{r.id} — {r.date.strftime('%a %b %d')} "
            f"{r.start_time.strftime('%H:%M')}–{r.end_time.strftime('%H:%M')}"
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"Cancel #{r.id}",
                callback_data=CancelBookingCallback(reservation_id=r.id).pack(),
            )
        ])

    await message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
    )


@router.callback_query(CancelBookingCallback.filter())
async def on_cancel_booking(
    callback: CallbackQuery,
    callback_data: CancelBookingCallback,
    session: AsyncSession,
) -> None:
    success = await cancel_reservation_if_owned(
        session, callback_data.reservation_id, callback.from_user.id
    )
    if success:
        await callback.answer("Booking cancelled.", show_alert=True)
        # Refresh the list
        reservations = await get_user_reservations(session, callback.from_user.id)
        if not reservations:
            await callback.message.edit_text("You have no upcoming bookings.")
        else:
            lines: list[str] = ["<b>Your upcoming bookings:</b>\n"]
            buttons: list[list[InlineKeyboardButton]] = []
            for r in reservations:
                lines.append(
                    f"#{r.id} — {r.date.strftime('%a %b %d')} "
                    f"{r.start_time.strftime('%H:%M')}–{r.end_time.strftime('%H:%M')}"
                )
                buttons.append([
                    InlineKeyboardButton(
                        text=f"Cancel #{r.id}",
                        callback_data=CancelBookingCallback(reservation_id=r.id).pack(),
                    )
                ])
            await callback.message.edit_text(
                "\n".join(lines),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            )
    else:
        await callback.answer("Booking not found or already cancelled.", show_alert=True)
