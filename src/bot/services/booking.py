from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.config import Settings
from src.bot.db.repository import get_booked_times


def generate_daily_slots(settings: Settings) -> list[tuple[time, time]]:
    slots: list[tuple[time, time]] = []
    hour = settings.day_start_hour
    while hour + (settings.slot_duration_minutes // 60) <= settings.day_end_hour:
        start = time(hour, 0)
        end_hour = hour + settings.slot_duration_minutes // 60
        end = time(end_hour, 0)
        slots.append((start, end))
        hour = end_hour
    return slots


async def get_available_slots(
    session: AsyncSession, target_date: date, settings: Settings
) -> list[tuple[time, time]]:
    all_slots = generate_daily_slots(settings)
    booked = set(await get_booked_times(session, target_date))

    now = datetime.now()
    available: list[tuple[time, time]] = []
    for start, end in all_slots:
        if start in booked:
            continue
        # Filter out past slots for today
        if target_date == now.date() and start <= now.time():
            continue
        available.append((start, end))
    return available


def get_bookable_date_range(settings: Settings) -> tuple[date, date]:
    today = date.today()
    max_date = today + timedelta(days=settings.max_advance_days)
    return today, max_date
