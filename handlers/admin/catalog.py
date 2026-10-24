"""Kurslar, mentorlar va FAQ boshqaruvi (qo'shish, tahrirlash, faol/nofaol, o'chirish)."""
from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.queries import catalog
from handlers.admin.panel import admin_router
from keyboards.callbacks import CrudCb
from keyboards.inline import BACK
from keyboards.reply import ADM_COURSES, ADM_FAQ, ADM_MENTORS, BTN_SKIP, admin_menu, cancel_kb, skip_cancel_kb
from states.admin import CrudInput
from utils.fmt import e
from utils.render import course_text, mentor_text
from utils.ui import send_card, show

router = admin_router("admin_catalog")

# maydon, nomi, turi (text | photo | int), majburiymi
ENTS: dict[str, dict] = {
    "course": {
        "one": "kurs", "title": "📚 Kurslar", "name": "title", "active": True,
        "fields": [("title", "Nomi", "text", True), ("description", "Tavsif", "text", False),
                   ("duration", "Davomiyligi", "text", False), ("price", "Narxi", "text", False),
                   ("schedule", "Dars kunlari va vaqti", "text", False), ("photo_id", "Rasm", "photo", False),
                   ("sort_order", "Tartib raqami", "int", False)],
    },
    "mentor": {
        "one": "mentor", "title": "👨‍🏫 Mentorlar", "name": "full_name", "active": True,
        "fields": [("full_name", "Ism", "text", True), ("specialty", "Mutaxassislik", "text", False),
                   ("experience", "Tajriba", "text", False), ("sat_score", "SAT natijasi", "text", False),
                   ("bio", "Qisqa bio", "text", False), ("photo_id", "Rasm", "photo", False),
                   ("sort_order", "Tartib raqami", "int", False)],
    },
    "faq": {
        "one": "savol", "title": "❓ FAQ", "name": "question", "active": False,
        "fields": [("question", "Savol", "text", True), ("answer", "Javob", "text", True),
                   ("sort_order", "Tartib raqami", "int", False)],
    },
}
MENU_BUTTONS = {ADM_COURSES: "course", ADM_MENTORS: "mentor", ADM_FAQ: "faq"}
SKIP = object()


async def card_text(ent: str, item: dict) -> str:
    if ent == "course":
        text = await course_text(item, active_only=False)
    elif ent == "mentor":
        text = await mentor_text(item, active_only=False)
    else:
        text = f"❓ <b>{e(item['question'])}</b>\n\n{e(item.get('answer') or '')}"
    extra = []
    if ENTS[ent]["active"] and "is_active" in item:
        extra.append("🟢 Faol" if item["is_active"] else "🔴 Nofaol")
    extra.append(f"Tartib: {item.get('sort_order') or 0}")
    return f"{text}\n\n<i>{' · '.join(extra)}</i>"


async def list_markup(ent: str):
    kb = InlineKeyboardBuilder()
    cfg = ENTS[ent]
    for item in await catalog.list_items(ent):
        mark = ("🟢 " if item["is_active"] else "🔴 ") if cfg["active"] else ""
        kb.button(text=f"{mark}{item[cfg['name']][:50]}", callback_data=CrudCb(ent=ent, action="open", id=item["id"]))
    kb.button(text=f"➕ Yangi {cfg['one']} qo'shish", callback_data=CrudCb(ent=ent, action="add"))
    kb.adjust(1)
    return kb.as_markup()


def card_markup(ent: str, item: dict):
    kb = InlineKeyboardBuilder()
    for field, label, _, _ in ENTS[ent]["fields"]:
        kb.button(text=f"✏️ {label}", callback_data=CrudCb(ent=ent, action="edit", id=item["id"], val=field))
    n = len(ENTS[ent]["fields"])
    sizes = [2] * (n // 2) + [1] * (n % 2)
    if ent == "course":
        kb.button(text="👨‍🏫 Mentorlarni biriktirish", callback_data=CrudCb(ent=ent, action="mentors", id=item["id"]))
        sizes.append(1)
    if ENTS[ent]["active"]:
        kb.button(text="🔴 Nofaol qilish" if item["is_active"] else "🟢 Faol qilish",
                  callback_data=CrudCb(ent=ent, action="toggle", id=item["id"]))
        sizes.append(1)
    kb.button(text="🗑 O'chirish", callback_data=CrudCb(ent=ent, action="del", id=item["id"]))
    kb.button(text=BACK, callback_data=CrudCb(ent=ent, action="list"))
    kb.adjust(*sizes, 2)
    return kb.as_markup()


def field_info(ent: str, field: str) -> tuple[str, str, str, bool]:
    return next(f for f in ENTS[ent]["fields"] if f[0] == field)


def parse_value(message: Message, kind: str, required: bool):
    """(qiymat, xato) qaytaradi. O'tkazib yuborish uchun SKIP, tozalash uchun '-' -> None."""
    text = (message.text or "").strip()
    if text == BTN_SKIP:
        return (None, "Bu maydon majburiy.") if required else (SKIP, None)
    if text == "-" and not required:
        return None, None
    if kind == "photo":
        if message.photo:
            return message.photo[-1].file_id, None
        return None, "Iltimos, rasm yuboring (yoki o'tkazib yuboring)."
    if kind == "int":
        try:
            return int(text), None
        except ValueError:
            return None, "Butun son kiriting (masalan: 1)."
    if not text:
        return None, "Matn yuboring."
    return text[:3000], None


def prompt(label: str, kind: str, required: bool) -> str:
    what = "rasm yuboring" if kind == "photo" else "son kiriting" if kind == "int" else "yozing"
    hint = "" if required else f"\n<i>Bo'sh qoldirish uchun «{BTN_SKIP}»</i>"
    return f"<b>{label}</b> — {what}:{hint}"


# ---------- Ro'yxat va kartochka ----------

@router.message(StateFilter("*"), F.text.in_(MENU_BUTTONS))
async def menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    ent = MENU_BUTTONS[message.text]
    await message.answer(f"<b>{ENTS[ent]['title']}</b>\n🟢 faol · 🔴 nofaol", reply_markup=await list_markup(ent))


@router.callback_query(CrudCb.filter(F.action == "list"))
async def list_cb(cb: CallbackQuery, callback_data: CrudCb, state: FSMContext | None = None) -> None:
    if state is not None and await state.get_state() == CrudInput.add_confirm.state:
        await state.clear()
    ent = callback_data.ent
    await show(cb, f"<b>{ENTS[ent]['title']}</b>\n🟢 faol · 🔴 nofaol", await list_markup(ent))


async def _open(cb: CallbackQuery, ent: str, item_id: int) -> None:
    item = await catalog.get_item(ent, item_id)
    if not item:
        await cb.answer("Topilmadi", show_alert=True)
        return
    await show(cb, await card_text(ent, item), card_markup(ent, item), photo=item.get("photo_id"))


@router.callback_query(CrudCb.filter(F.action == "open"))
async def open_cb(cb: CallbackQuery, callback_data: CrudCb) -> None:
    await _open(cb, callback_data.ent, callback_data.id)


async def send_item_card(message: Message, ent: str, item_id: int) -> None:
    item = await catalog.get_item(ent, item_id)
    await send_card(message, await card_text(ent, item), card_markup(ent, item), photo=item.get("photo_id"))


@router.callback_query(CrudCb.filter(F.action == "toggle"))
async def toggle_cb(cb: CallbackQuery, callback_data: CrudCb) -> None:
    await catalog.toggle_active(callback_data.ent, callback_data.id)
    await _open(cb, callback_data.ent, callback_data.id)


@router.callback_query(CrudCb.filter(F.action == "del"))
async def delete_ask(cb: CallbackQuery, callback_data: CrudCb) -> None:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Ha, o'chirish", callback_data=CrudCb(ent=callback_data.ent, action="delok", id=callback_data.id))
    kb.button(text="❌ Yo'q", callback_data=CrudCb(ent=callback_data.ent, action="open", id=callback_data.id))
    kb.adjust(2)
    await show(cb, "🗑 Rostdan ham o'chirilsinmi? Bu amalni qaytarib bo'lmaydi.\n"
                   "(Vaqtincha yashirish uchun «Nofaol qilish» dan foydalaning.)", kb.as_markup())


@router.callback_query(CrudCb.filter(F.action == "delok"))
async def delete_ok(cb: CallbackQuery, callback_data: CrudCb) -> None:
    await catalog.delete_item(callback_data.ent, callback_data.id)
    await cb.answer("O'chirildi")
    await list_cb(cb, callback_data)


# ---------- Kursga mentor biriktirish ----------

@router.callback_query(CrudCb.filter(F.action.in_({"mentors", "tgm"})))
async def course_mentors(cb: CallbackQuery, callback_data: CrudCb) -> None:
    course_id = callback_data.id
    if callback_data.action == "tgm":
        await catalog.toggle_course_mentor(course_id, int(callback_data.val))
    linked = {m["id"] for m in await catalog.mentors_of_course(course_id)}
    kb = InlineKeyboardBuilder()
    for m in await catalog.list_items("mentor"):
        mark = "✅" if m["id"] in linked else "▫️"
        kb.button(text=f"{mark} {m['full_name']}",
                  callback_data=CrudCb(ent="course", action="tgm", id=course_id, val=str(m["id"])))
    kb.button(text=BACK, callback_data=CrudCb(ent="course", action="open", id=course_id))
    kb.adjust(1)
    text = "👨‍🏫 Kursni o'tadigan mentorlarni belgilang:"
    if not linked and not await catalog.list_items("mentor"):
        text = "Avval «Mentorlarni boshqarish» bo'limida mentor qo'shing."
    await show(cb, text, kb.as_markup())


# ---------- Maydonni tahrirlash ----------

@router.callback_query(CrudCb.filter(F.action == "edit"))
async def edit_start(cb: CallbackQuery, callback_data: CrudCb, state: FSMContext) -> None:
    _, label, kind, required = field_info(callback_data.ent, callback_data.val)
    await state.set_state(CrudInput.edit)
    await state.update_data(ent=callback_data.ent, id=callback_data.id, field=callback_data.val)
    hint = "" if required else "\n<i>Qiymatni o'chirish uchun «-» yuboring.</i>"
    what = "rasm yuboring" if kind == "photo" else "son kiriting" if kind == "int" else "yangi qiymatni yozing"
    await cb.message.answer(f"✏️ <b>{label}</b> — {what}:{hint}", reply_markup=cancel_kb())
    await cb.answer()


@router.message(CrudInput.edit)
async def edit_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    _, _, kind, required = field_info(data["ent"], data["field"])
    value, error = parse_value(message, kind, required)
    if error or value is SKIP:
        await message.answer(f"❗️ {error or 'Qiymat yuboring.'}")
        return
    await catalog.update_field(data["ent"], data["id"], data["field"], value)
    await state.clear()
    await message.answer("✅ Saqlandi", reply_markup=admin_menu())
    await send_item_card(message, data["ent"], data["id"])


# ---------- Qo'shish ----------

@router.callback_query(CrudCb.filter(F.action == "add"))
async def add_start(cb: CallbackQuery, callback_data: CrudCb, state: FSMContext) -> None:
    ent = callback_data.ent
    await state.set_state(CrudInput.add)
    await state.update_data(ent=ent, step=0, vals={})
    _, label, kind, required = ENTS[ent]["fields"][0]
    await cb.message.answer(f"➕ Yangi {ENTS[ent]['one']}\n\n" + prompt(label, kind, required),
                            reply_markup=cancel_kb() if required else skip_cancel_kb())
    await cb.answer()


@router.message(CrudInput.add)
async def add_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    ent, step, vals = data["ent"], data["step"], data["vals"]
    fields = ENTS[ent]["fields"]
    field, _, kind, required = fields[step]
    value, error = parse_value(message, kind, required)
    if error:
        await message.answer(f"❗️ {error}")
        return
    if value is not SKIP and value is not None:
        vals[field] = value
    step += 1
    await state.update_data(step=step, vals=vals)
    if step < len(fields):
        _, label, kind, required = fields[step]
        await message.answer(prompt(label, kind, required), reply_markup=cancel_kb() if required else skip_cancel_kb())
        return
    # Oldindan ko'rish va tasdiqlash
    await state.set_state(CrudInput.add_confirm)
    preview = {"id": 0, "is_active": 1, **vals}
    await message.answer("👀 <b>Oldindan ko'rish:</b>", reply_markup=cancel_kb())
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Saqlash", callback_data=CrudCb(ent=ent, action="save"))
    kb.button(text="❌ Bekor qilish", callback_data=CrudCb(ent=ent, action="list"))
    kb.adjust(2)
    await send_card(message, await card_text(ent, preview), kb.as_markup(), photo=vals.get("photo_id"))


@router.callback_query(CrudInput.add_confirm, CrudCb.filter(F.action == "save"))
async def add_save(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    new_id = await catalog.add_item(data["ent"], data["vals"])
    await cb.answer("Saqlandi ✅")
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.message.answer("✅ Qo'shildi", reply_markup=admin_menu())
    await send_item_card(cb.message, data["ent"], new_id)


@router.callback_query(CrudCb.filter(F.action == "save"))
async def add_save_stale(cb: CallbackQuery) -> None:
    await cb.answer("Bu tugma eskirgan", show_alert=True)
