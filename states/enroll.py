from aiogram.fsm.state import State, StatesGroup


class Enroll(StatesGroup):
    course = State()
    name = State()
    phone = State()
    confirm = State()
