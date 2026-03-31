from datetime import time

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class TimeSlotCallback(CallbackData, prefix="slot"):
    action: str  # "pick" or "back"
    hour: int = 0
    minute: int = 0


def build_time_slots_keyboard(
    available: list[tuple[time, time]],
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    # 3-column grid
    row: list[InlineKeyboardButton] = []
    for start, _end in available:
        label = start.strftime("%H:%M")
        row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=TimeSlotCallback(
                    action="pick", hour=start.hour, minute=start.minute
                ).pack(),
            )
        )
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    # Back + Cancel
    rows.append([
        InlineKeyboardButton(
            text="« Back",
            callback_data=TimeSlotCallback(action="back").pack(),
        ),
        InlineKeyboardButton(
            text="Cancel",
            callback_data=TimeSlotCallback(action="cancel").pack(),
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
