from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class ConfirmCallback(CallbackData, prefix="confirm"):
    action: str  # "yes" or "no"


def build_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Confirm",
                callback_data=ConfirmCallback(action="yes").pack(),
            ),
            InlineKeyboardButton(
                text="Cancel",
                callback_data=ConfirmCallback(action="no").pack(),
            ),
        ]
    ])


class CancelBookingCallback(CallbackData, prefix="cancelbook"):
    reservation_id: int


class AdminCancelCallback(CallbackData, prefix="admcancel"):
    reservation_id: int
