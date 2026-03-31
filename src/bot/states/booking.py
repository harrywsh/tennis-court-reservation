from aiogram.fsm.state import State, StatesGroup


class BookingStates(StatesGroup):
    selecting_date = State()
    selecting_time = State()
    confirming = State()
