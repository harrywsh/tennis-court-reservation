import calendar
from datetime import date

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.bot.config import Settings
from src.bot.services.booking import get_bookable_date_range


class CalendarCallback(CallbackData, prefix="cal"):
    action: str  # "day", "prev", "next", "ignore"
    year: int
    month: int
    day: int = 0


DAYS_OF_WEEK = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def build_calendar(year: int, month: int, settings: Settings) -> InlineKeyboardMarkup:
    min_date, max_date = get_bookable_date_range(settings)
    cal = calendar.monthcalendar(year, month)

    rows: list[list[InlineKeyboardButton]] = []

    # Header: « Month Year »
    month_name = calendar.month_name[month]
    rows.append([
        InlineKeyboardButton(
            text="«",
            callback_data=CalendarCallback(action="prev", year=year, month=month).pack(),
        ),
        InlineKeyboardButton(
            text=f"{month_name} {year}",
            callback_data=CalendarCallback(action="ignore", year=year, month=month).pack(),
        ),
        InlineKeyboardButton(
            text="»",
            callback_data=CalendarCallback(action="next", year=year, month=month).pack(),
        ),
    ])

    # Day-of-week labels
    rows.append([
        InlineKeyboardButton(
            text=d,
            callback_data=CalendarCallback(action="ignore", year=year, month=month).pack(),
        )
        for d in DAYS_OF_WEEK
    ])

    # Day buttons
    for week in cal:
        row: list[InlineKeyboardButton] = []
        for day_num in week:
            if day_num == 0:
                row.append(InlineKeyboardButton(
                    text=" ",
                    callback_data=CalendarCallback(action="ignore", year=year, month=month).pack(),
                ))
            else:
                d = date(year, month, day_num)
                if min_date <= d <= max_date:
                    row.append(InlineKeyboardButton(
                        text=str(day_num),
                        callback_data=CalendarCallback(
                            action="day", year=year, month=month, day=day_num
                        ).pack(),
                    ))
                else:
                    row.append(InlineKeyboardButton(
                        text="·",
                        callback_data=CalendarCallback(
                            action="ignore", year=year, month=month
                        ).pack(),
                    ))
        rows.append(row)

    # Cancel button
    rows.append([
        InlineKeyboardButton(
            text="Cancel",
            callback_data=CalendarCallback(action="cancel", year=year, month=month).pack(),
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def navigate_month(year: int, month: int, direction: int) -> tuple[int, int]:
    month += direction
    if month > 12:
        month = 1
        year += 1
    elif month < 1:
        month = 12
        year -= 1
    return year, month
