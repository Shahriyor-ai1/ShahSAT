"""Kurslar, mentorlar va FAQ — foydalanuvchi uchun."""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.queries import catalog
from keyboards import inline
from keyboards.callbacks import CourseCb, FaqCb, MentorCb
from keyboards.reply import BTN_COURSES, BTN_FAQ, BTN_MENTORS
from utils.fmt import NO_DATA, e
from utils.render import course_text, mentor_text
from utils.ui import show

router = Router(name="user_catalog")

COURSES_TITLE = "📚 <b>Kurslarimiz</b>\n\nKursni tanlang:"
MENTORS_TITLE = "👨‍🏫 <b>Mentorlarimiz</b>\n\nMentorni tanlang:"
FAQ_TITLE = "❓ <b>Ko'p so'raladigan savollar</b>\n\nSavolni tanlang:"


# ---------- Kurslar ----------

@router.message(StateFilter("*"), F.text == BTN_COURSES, F.chat.type == "private")
async def courses(message: Message, state: FSMContext) -> None:
    await state.clear()
    items = await catalog.list_items("course", active_only=True)
    if not items:
        await message.answer(NO_DATA)
        return
    await message.answer(COURSES_TITLE, reply_markup=inline.courses_list(items))


@router.callback_query(CourseCb.filter(F.action == "list"))
async def courses_back(cb: CallbackQuery) -> None:
    items = await catalog.list_items("course", active_only=True)
    await show(cb, COURSES_TITLE if items else NO_DATA, inline.courses_list(items))


@router.callback_query(CourseCb.filter(F.action == "open"))
async def course_open(cb: CallbackQuery, callback_data: CourseCb) -> None:
    c = await catalog.get_item("course", callback_data.id)
    if not c or not c["is_active"]:
        await cb.answer("Bu kurs hozircha mavjud emas", show_alert=True)
        return
    await show(cb, await course_text(c), inline.course_card(c["id"]), photo=c.get("photo_id"))


# ---------- Mentorlar ----------

@router.message(StateFilter("*"), F.text == BTN_MENTORS, F.chat.type == "private")
async def mentors(message: Message, state: FSMContext) -> None:
    await state.clear()
    items = await catalog.list_items("mentor", active_only=True)
    if not items:
        await message.answer(NO_DATA)
        return
    await message.answer(MENTORS_TITLE, reply_markup=inline.mentors_list(items))


@router.callback_query(MentorCb.filter(F.action == "list"))
async def mentors_back(cb: CallbackQuery) -> None:
    items = await catalog.list_items("mentor", active_only=True)
    await show(cb, MENTORS_TITLE if items else NO_DATA, inline.mentors_list(items))


@router.callback_query(MentorCb.filter(F.action == "open"))
async def mentor_open(cb: CallbackQuery, callback_data: MentorCb) -> None:
    m = await catalog.get_item("mentor", callback_data.id)
    if not m or not m["is_active"]:
        await cb.answer("Ma'lumot topilmadi", show_alert=True)
        return
    await show(cb, await mentor_text(m), inline.back_to(MentorCb(action="list")), photo=m.get("photo_id"))


# ---------- FAQ ----------

@router.message(StateFilter("*"), F.text == BTN_FAQ, F.chat.type == "private")
async def faq(message: Message, state: FSMContext) -> None:
    await state.clear()
    items = await catalog.list_items("faq")
    if not items:
        await message.answer(NO_DATA)
        return
    await message.answer(FAQ_TITLE, reply_markup=inline.faq_list(items))


@router.callback_query(FaqCb.filter(F.action == "list"))
async def faq_back(cb: CallbackQuery) -> None:
    items = await catalog.list_items("faq")
    await show(cb, FAQ_TITLE if items else NO_DATA, inline.faq_list(items))


@router.callback_query(FaqCb.filter(F.action == "open"))
async def faq_open(cb: CallbackQuery, callback_data: FaqCb) -> None:
    f = await catalog.get_item("faq", callback_data.id)
    if not f:
        await cb.answer("Savol topilmadi", show_alert=True)
        return
    text = f"❓ <b>{e(f['question'])}</b>\n\n{e(f['answer'] or NO_DATA)}"
    await show(cb, text, inline.back_to(FaqCb(action="list")))
