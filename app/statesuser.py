# import functions from libraries
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class Send(StatesGroup):
    sendmess = State()
    ph_true = State()
