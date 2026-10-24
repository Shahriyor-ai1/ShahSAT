"""Kursga yozilish va nomer qoldirish (FSM)."""
from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.queries import catalog, leads as leads_q, settings, users
from keyboards import inline
from keyboards.callbacks import CourseCb, EnrollCb
from keyboards.reply import BTN_CALLBACK, BTN_ENROLL, cancel_kb, main_menu, phone_kb
from states.enroll import Enroll
from utils.fmt import NO_DATA, e
from utils.notify import notify_new_lead
from utils.phone import normalize_phone, valid_name

router = Router(name="user_enroll")
router.message.filter(F.chat.type == "private")

ASK_NAME = "👤 Ism va familiyangizni yozing:"
ASK_PHONE = ("📱 Telefon raqamingizni yuboring.\n"
             "«📱 Raqamni yuborish» tugmasini bosing yoki qo'lda yozing (masalan: +998 90 123 45 67).")


@router.message(StateFilter("*"), F.text == BTN_ENROLL)
async def start_enroll(message: Message, state: FSMContext) -> None:
    await state.clear()
    courses = await catalog.list_items("course", active_only=True)
    if not courses:
        await message.answer(f"{NO_DATA}\n\nHozircha «{BTN_CALLBACK}» orqali raqamingizni qoldirishingiz mumkin.")
        return
    await state.set_state(Enroll.course)
    await state.update_data(type="enroll")
    await message.answer("✍️ Kursga yozilish", reply_markup=cancel_kb())
    await message.answer("Qaysi kursga yozilmoqchisiz?", reply_markup=inline.enroll_courses(courses))


@router.message(StateFilter("*"), F.text == BTN_CALLBACK)
async def start_callback(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Enroll.name)
    await state.update_data(type="callback", course_id=None, course_title=None)
    await message.answer("📞 Raqamingizni qoldiring — menejerimiz o'zi qo'ng'iroq qiladi.\n\n" + ASK_NAME,
                         reply_markup=cancel_kb())


@router.callback_query(CourseCb.filter(F.action == "enroll"))
async def enroll_from_card(cb: CallbackQuery, callback_data: CourseCb, state: FSMContext) -> None:
    course = await catalog.get_item("course", callback_data.id)
    if not course or not course["is_active"]:
        await cb.answer("Bu kurs hozircha mavjud emas", show_alert=True)
        return
    await state.clear()
    await state.set_state(Enroll.name)
    await state.update_data(type="enroll", course_id=course["id"], course_title=course["title"])
    await cb.answer()
    await cb.message.answer(f"📚 Kurs: <b>{e(course['title'])}</b>\n\n{ASK_NAME}", reply_markup=cancel_kb())


@router.callback_query(Enroll.course, EnrollCb.filter(F.action == "pick"))
async def pick_course(cb: CallbackQuery, callback_data: EnrollCb, state: FSMContext) -> None:
    course = await catalog.get_item("course", callback_data.id)
    if not course or not course["is_active"]:
        await cb.answer("Bu kurs hozircha mavjud emas", show_alert=True)
        return
    await state.update_data(course_id=course["id"], course_title=course["title"])
    await state.set_state(Enroll.name)
    await cb.message.edit_text(f"📚 Tanlangan kurs: <b>{e(course['title'])}</b>")
    await cb.message.answer(ASK_NAME, reply_markup=cancel_kb())
    await cb.answer()


@router.message(Enroll.course)
async def course_expected(message: Message) -> None:
    await message.answer("Iltimos, yuqoridagi ro'yxatdan kursni tanlang 👆")


@router.message(Enroll.name)
async def got_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if not valid_name(name):
        await message.answer("❗️ Ism 2–50 belgidan iborat bo'lishi va raqam qatnashmasligi kerak. Qayta yozing:")
        return
    await state.update_data(name=" ".join(name.split()))
    await state.set_state(Enroll.phone)
    await message.answer(ASK_PHONE, reply_markup=phone_kb())


@router.message(Enroll.phone)
async def got_phone(message: Message, state: FSMContext) -> None:
    raw = message.contact.phone_number if message.contact else (message.text or "")
    phone = normalize_phone(raw)
    if phone is None:
        await message.answer("❗️ Raqam noto'g'ri. Format: +998XXXXXXXXX (9 yoki 12 raqam). Qayta yuboring:")
        return
    await state.update_data(phone=phone)
    await state.set_state(Enroll.confirm)
    data = await state.get_data()
    text = "📋 <b>Ma'lumotlaringizni tekshiring:</b>\n\n"
    if data.get("course_title"):
        text += f"📚 Kurs: <b>{e(data['course_title'])}</b>\n"
    text += f"👤 Ism: <b>{e(data['name'])}</b>\n📱 Telefon: <b>{phone}</b>"
    await message.answer("Deyarli tayyor ✅", reply_markup=cancel_kb())
    await message.answer(text, reply_markup=inline.enroll_confirm())


@router.callback_query(Enroll.confirm, EnrollCb.filter(F.action == "retry"))
async def retry(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Enroll.name)
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer(ASK_NAME, reply_markup=cancel_kb())
    await cb.answer()


@router.callback_query(Enroll.confirm, EnrollCb.filter(F.action == "confirm"))
async def confirm(cb: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.answer()
    user = await users.get_user(cb.from_user.id) or await users.upsert_user(cb.from_user, None)
    course_id = data.get("course_id")
    if await leads_q.recent_duplicate(user["id"], course_id, data["type"]):
        await cb.message.answer("ℹ️ Arizangiz allaqachon qabul qilingan. Tez orada siz bilan bog'lanamiz.",
                                reply_markup=main_menu())
        return
    lead_id = await leads_q.create_lead(user["id"], course_id, data["name"], data["phone"],
                                       data["type"], user["source"])
    thanks = await settings.get("thanks_text")
    await cb.message.answer(e(thanks), reply_markup=main_menu())
    await notify_new_lead(bot, lead_id)


@router.callback_query(EnrollCb.filter())
async def stale(cb: CallbackQuery) -> None:
    await cb.answer("Bu tugma eskirgan. Qaytadan boshlang.", show_alert=True)
