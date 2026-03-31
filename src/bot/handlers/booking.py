from datetime import date, time

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.config import Settings
from src.bot.db.repository import get_allowed_user, get_system_config, create_reservation
from src.bot.filters.auth import AllowlistFilter
from src.bot.keyboards.calendar import CalendarCallback, build_calendar, navigate_month
from src.bot.keyboards.common import ConfirmCallback, build_confirm_keyboard
from src.bot.keyboards.time_slots import TimeSlotCallback, build_time_slots_keyboard
from src.bot.services.booking import get_available_slots
from src.bot.states.booking import BookingStates

router = Router(name="booking")
router.message.filter(AllowlistFilter())
router.callback_query.filter(AllowlistFilter())


@router.message(Command("book"))
async def cmd_book(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    config = await get_system_config(session)
    if not config.reservations_enabled:
        await message.answer("Reservations are currently disabled by the admin.")
        return

    today = date.today()
    keyboard = build_calendar(today.year, today.month, settings)
    await message.answer("Select a date:", reply_markup=keyboard)
    await state.set_state(BookingStates.selecting_date)


@router.callback_query(CalendarCallback.filter(F.action == "day"), BookingStates.selecting_date)
async def on_date_selected(
    callback: CallbackQuery,
    callback_data: CalendarCallback,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    selected = date(callback_data.year, callback_data.month, callback_data.day)
    available = await get_available_slots(session, selected, settings)

    if not available:
        await callback.answer("No available slots on this date.", show_alert=True)
        return

    await state.update_data(
        date=selected.isoformat(),
    )
    keyboard = build_time_slots_keyboard(available)
    await callback.message.edit_text(
        f"Available slots on <b>{selected.strftime('%a %b %d')}</b>:",
        reply_markup=keyboard,
    )
    await state.set_state(BookingStates.selecting_time)
    await callback.answer()


@router.callback_query(CalendarCallback.filter(F.action == "prev"), BookingStates.selecting_date)
@router.callback_query(CalendarCallback.filter(F.action == "next"), BookingStates.selecting_date)
async def on_calendar_nav(
    callback: CallbackQuery,
    callback_data: CalendarCallback,
    state: FSMContext,
    settings: Settings,
) -> None:
    direction = 1 if callback_data.action == "next" else -1
    year, month = navigate_month(callback_data.year, callback_data.month, direction)
    keyboard = build_calendar(year, month, settings)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(CalendarCallback.filter(F.action == "cancel"), BookingStates.selecting_date)
async def on_calendar_cancel(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    await callback.message.edit_text("Booking cancelled.")
    await callback.answer()


@router.callback_query(CalendarCallback.filter(F.action == "ignore"), BookingStates.selecting_date)
async def on_calendar_ignore(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(TimeSlotCallback.filter(F.action == "pick"), BookingStates.selecting_time)
async def on_time_selected(
    callback: CallbackQuery,
    callback_data: TimeSlotCallback,
    state: FSMContext,
    settings: Settings,
) -> None:
    start = time(callback_data.hour, callback_data.minute)
    end_hour = callback_data.hour + settings.slot_duration_minutes // 60
    end = time(end_hour, 0)

    data = await state.get_data()
    selected_date = date.fromisoformat(data["date"])

    await state.update_data(
        start_time=start.isoformat(),
        end_time=end.isoformat(),
    )

    text = (
        f"<b>Confirm your booking:</b>\n\n"
        f"Date: {selected_date.strftime('%a %b %d, %Y')}\n"
        f"Time: {start.strftime('%H:%M')} – {end.strftime('%H:%M')}"
    )
    await callback.message.edit_text(text, reply_markup=build_confirm_keyboard())
    await state.set_state(BookingStates.confirming)
    await callback.answer()


@router.callback_query(TimeSlotCallback.filter(F.action == "back"), BookingStates.selecting_time)
async def on_time_back(
    callback: CallbackQuery,
    state: FSMContext,
    settings: Settings,
) -> None:
    today = date.today()
    keyboard = build_calendar(today.year, today.month, settings)
    await callback.message.edit_text("Select a date:", reply_markup=keyboard)
    await state.set_state(BookingStates.selecting_date)
    await callback.answer()


@router.callback_query(TimeSlotCallback.filter(F.action == "cancel"), BookingStates.selecting_time)
async def on_time_cancel(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    await callback.message.edit_text("Booking cancelled.")
    await callback.answer()


@router.callback_query(ConfirmCallback.filter(F.action == "yes"), BookingStates.confirming)
async def on_confirm(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    settings: Settings,
) -> None:
    data = await state.get_data()
    selected_date = date.fromisoformat(data["date"])
    start = time.fromisoformat(data["start_time"])
    end = time.fromisoformat(data["end_time"])

    user = await get_allowed_user(session, callback.from_user.id)
    if user is None:
        await state.clear()
        await callback.message.edit_text("Your access has been revoked. Contact the admin.")
        await callback.answer()
        return

    try:
        reservation = await create_reservation(session, user, selected_date, start, end)
        await session.flush()
    except IntegrityError:
        await session.rollback()
        await state.clear()
        await callback.message.edit_text(
            "Sorry, this slot was just booked by someone else. Please try again with /book."
        )
        await callback.answer()
        return

    await state.clear()
    await callback.message.edit_text(
        f"Booked!\n\n"
        f"Date: {selected_date.strftime('%a %b %d, %Y')}\n"
        f"Time: {start.strftime('%H:%M')} – {end.strftime('%H:%M')}\n"
        f"Booking ID: #{reservation.id}"
    )
    await callback.answer("Booking confirmed!")


@router.callback_query(ConfirmCallback.filter(F.action == "no"), BookingStates.confirming)
async def on_confirm_cancel(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    await state.clear()
    await callback.message.edit_text("Booking cancelled.")
    await callback.answer()
