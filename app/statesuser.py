from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class Send(StatesGroup):
    sendmess = State()
    confirm = State()