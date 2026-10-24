from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from filters.admin import AdminFilter
from keyboards.reply import ADM_EXIT, admin_menu, main_menu


def admin_router(name: str) -> Router:
    """Faqat adminlar uchun ishlaydigan router."""
    r = Router(name=name)
    r.message.filter(AdminFilter())
    r.callback_query.filter(AdminFilter())
    return r


router = admin_router("admin_panel")


@router.message(StateFilter("*"), Command("admin"), F.chat.type == "private")
async def cmd_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🛠 <b>Admin panel</b>\n\nBo'limni tanlang 👇", reply_markup=admin_menu())


@router.message(StateFilter("*"), F.text == ADM_EXIT, F.chat.type == "private")
async def exit_admin(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Asosiy menyu 👇  (admin panelga qaytish: /admin)", reply_markup=main_menu())
