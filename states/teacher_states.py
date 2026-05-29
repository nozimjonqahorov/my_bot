from aiogram.fsm.state import StatesGroup, State

class TeacherState(StatesGroup):
    waiting_answer = State()
    waiting_broadcast = State()
