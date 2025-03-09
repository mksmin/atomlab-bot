# import from libraries
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


class Send(StatesGroup):
    sendmess = State()
    ph_true = State()


class Admins(StatesGroup):
    admins = State()


class ProjectState(StatesGroup):
    prj_name = State()
    prj_description = State()
    last_message_id = State()
    save_prj = State()
    cancel_prj = State()


class DeleteEntry(StatesGroup):
    object_number = State()
    last_message_id = State()
