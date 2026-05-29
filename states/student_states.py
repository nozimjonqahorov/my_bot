from aiogram.fsm.state import StatesGroup, State

class StudentState(StatesGroup):
    waiting_anonymity = State()
    waiting_content = State()
