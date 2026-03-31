from aiogram import Dispatcher

from src.bot.handlers import admin, booking, common, my_bookings


def register_routers(dp: Dispatcher) -> None:
    dp.include_router(common.router)
    dp.include_router(booking.router)
    dp.include_router(my_bookings.router)
    dp.include_router(admin.router)
