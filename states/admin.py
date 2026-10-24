from aiogram.fsm.state import State, StatesGroup


class LeadInput(StatesGroup):
    meeting = State()
    reject = State()
    note = State()
    field = State()


class SettingInput(StatesGroup):
    value = State()
    confirm = State()


class CrudInput(StatesGroup):
    add = State()
    add_confirm = State()
    edit = State()


class SourceInput(StatesGroup):
    code = State()
    title = State()


class ExportInput(StatesGroup):
    range = State()


class BroadcastInput(StatesGroup):
    content = State()
    confirm = State()


class AdminInput(StatesGroup):
    tg_id = State()
