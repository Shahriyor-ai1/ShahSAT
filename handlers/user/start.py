import re

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.queries import admins, settings, users
from keyboards.reply import BTN_CANCEL, admin_menu, main_menu
from utils.fmt import e

router = Router(name="user_start")
router.message.filter(F.chat.type == "private")


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, state: FSMContext) -> None:
    await state.clear()
    source = None
    if command.args and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", command.args):
        source = command.args
    await users.upsert_user(message.from_user, source)
    welcome = await settings.get("welcome_text")
    await message.answer(e(welcome), reply_markup=main_menu())


@router.message(StateFilter("*"), F.text == BTN_CANCEL)
async def cancel_any(message: Message, state: FSMContext) -> None:
    current = await state.get_state() or ""
    await state.clear()
    is_admin_flow = admins.is_admin(message.from_user.id) and not current.startswith("Enroll")
    if is_admin_flow and current:
        await message.answer("Bekor qilindi.", reply_markup=admin_menu())
    else:
        await message.answer("Bekor qilindi. Asosiy menyu 👇", reply_markup=main_menu())


# Bu router eng oxirida ulanadi: noma'lum matnga asosiy menyuni qayta ko'rsatadi
fallback_router = Router(name="fallback")
fallback_router.message.filter(F.chat.type == "private")


@fallback_router.message(StateFilter(None))
async def unknown(message: Message) -> None:
    await message.answer("Iltimos, quyidagi menyudan tanlang 👇", reply_markup=main_menu())
