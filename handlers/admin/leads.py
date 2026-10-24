"""Mini-CRM: arizalar ro'yxati, kartochka, statuslar, izoh va tahrirlash."""
from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.queries import catalog, leads as leads_q, sources
from database.queries.leads import STATUS_LABELS, Status
from handlers.admin.panel import admin_router
from keyboards.callbacks import LeadCb, LeadsCb
from keyboards.inline import BACK, lead_kb
from keyboards.reply import ADM_LEADS, admin_menu, cancel_kb
from states.admin import LeadInput
from utils.fmt import e
from utils.phone import normalize_phone, valid_name
from utils.render import lead_text
from utils.ui import show

router = admin_router("admin_leads")
PAGE_SIZE = 10


async def filters_markup():
    kb = InlineKeyboardBuilder()
    kb.button(text=f"📋 Hammasi ({await leads_q.count_leads()})", callback_data=LeadsCb(status="all"))
    for code, label in STATUS_LABELS.items():
        kb.button(text=f"{label} ({await leads_q.count_leads(code)})", callback_data=LeadsCb(status=code))
    kb.adjust(1, 2)
    return kb.as_markup()


@router.message(StateFilter("*"), F.text == ADM_LEADS)
async def leads_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("📥 <b>Arizalar</b>\n\nStatus bo'yicha filtrlang:", reply_markup=await filters_markup())


@router.callback_query(LeadsCb.filter(F.status == "menu"))
async def leads_menu_cb(cb: CallbackQuery) -> None:
    await show(cb, "📥 <b>Arizalar</b>\n\nStatus bo'yicha filtrlang:", await filters_markup())


@router.callback_query(LeadsCb.filter())
async def leads_list(cb: CallbackQuery, callback_data: LeadsCb) -> None:
    status = None if callback_data.status == "all" else callback_data.status
    page = max(callback_data.page, 0)
    total = await leads_q.count_leads(status)
    rows = await leads_q.list_leads(status, page * PAGE_SIZE, PAGE_SIZE)
    kb = InlineKeyboardBuilder()
    for r in rows:
        icon = leads_q.status_label(r["status"]).split()[0]
        kb.button(text=f"#{r['id']} {icon} {r['name']} — {r['phone']}",
                  callback_data=LeadCb(action="open", id=r["id"], val=callback_data.status))
    nav = []
    if page > 0:
        nav.append(("◀️", LeadsCb(status=callback_data.status, page=page - 1)))
    if (page + 1) * PAGE_SIZE < total:
        nav.append(("▶️", LeadsCb(status=callback_data.status, page=page + 1)))
    for text, data in nav:
        kb.button(text=text, callback_data=data)
    kb.button(text="⬅️ Filtrlar", callback_data=LeadsCb(status="menu"))
    kb.adjust(*([1] * len(rows)), *([len(nav)] if nav else []), 1)
    title = "Hammasi" if status is None else leads_q.status_label(status)
    pages = max((total - 1) // PAGE_SIZE + 1, 1)
    text = f"📥 <b>Arizalar — {title}</b>\nJami: {total} · Sahifa {page + 1}/{pages}"
    if not rows:
        text += "\n\nBu bo'limda ariza yo'q."
    await show(cb, text, kb.as_markup())


async def _render_card(cb: CallbackQuery, lead_id: int, back: str = "all") -> None:
    lead = await leads_q.get_lead(lead_id)
    if not lead:
        await cb.answer("Ariza topilmadi", show_alert=True)
        return
    in_private = cb.message.chat.type == "private"
    await show(cb, await lead_text(lead, full=True), lead_kb(lead, back=back if in_private else None))


async def send_card(message: Message, lead_id: int) -> None:
    lead = await leads_q.get_lead(lead_id)
    in_private = message.chat.type == "private"
    await message.answer(await lead_text(lead, full=True), reply_markup=lead_kb(lead, back="all" if in_private else None),
                         disable_web_page_preview=True)


@router.callback_query(LeadCb.filter(F.action == "open"))
async def lead_open(cb: CallbackQuery, callback_data: LeadCb) -> None:
    await _render_card(cb, callback_data.id, callback_data.val or "all")


# ---------- Statuslar ----------

@router.callback_query(LeadCb.filter(F.action == "st"))
async def lead_status(cb: CallbackQuery, callback_data: LeadCb, state: FSMContext) -> None:
    lead = await leads_q.get_lead(callback_data.id)
    if not lead:
        await cb.answer("Ariza topilmadi", show_alert=True)
        return
    new = callback_data.val
    if new not in STATUS_LABELS:
        await cb.answer()
        return
    if new == Status.MEETING.value:
        await state.set_state(LeadInput.meeting)
        await state.update_data(lead_id=lead["id"])
        await cb.message.answer(f"📅 Ariza #{lead['id']}: uchrashuv sana va vaqtini yozing\n(masalan: 25.10.2026 15:00)",
                                reply_markup=cancel_kb())
        await cb.answer()
        return
    if new == Status.NOT_SOLD.value:
        await state.set_state(LeadInput.reject)
        await state.update_data(lead_id=lead["id"])
        await cb.message.answer(f"❌ Ariza #{lead['id']}: rad etish sababini yozing:", reply_markup=cancel_kb())
        await cb.answer()
        return
    if lead["status"] == new:
        await cb.answer("Status allaqachon shu")
        return
    await leads_q.set_status(lead["id"], new, cb.from_user.id)
    await _render_card(cb, lead["id"])


async def _finish(message: Message, state: FSMContext, lead_id: int, done: str) -> None:
    await state.clear()
    kb = admin_menu() if message.chat.type == "private" else None
    await message.answer(done, reply_markup=kb)
    await send_card(message, lead_id)


@router.message(LeadInput.meeting, F.text)
async def meeting_input(message: Message, state: FSMContext) -> None:
    lead_id = (await state.get_data())["lead_id"]
    await leads_q.set_status(lead_id, Status.MEETING.value, message.from_user.id, meeting_at=message.text.strip()[:100])
    await _finish(message, state, lead_id, "✅ Uchrashuv belgilandi")


@router.message(LeadInput.reject, F.text)
async def reject_input(message: Message, state: FSMContext) -> None:
    lead_id = (await state.get_data())["lead_id"]
    await leads_q.set_status(lead_id, Status.NOT_SOLD.value, message.from_user.id, reject_reason=message.text.strip()[:500])
    await _finish(message, state, lead_id, "✅ Status yangilandi")


# ---------- Izoh ----------

@router.callback_query(LeadCb.filter(F.action == "note"))
async def note_start(cb: CallbackQuery, callback_data: LeadCb, state: FSMContext) -> None:
    await state.set_state(LeadInput.note)
    await state.update_data(lead_id=callback_data.id)
    await cb.message.answer(f"📝 Ariza #{callback_data.id} uchun izoh yozing:", reply_markup=cancel_kb())
    await cb.answer()


@router.message(LeadInput.note, F.text)
async def note_input(message: Message, state: FSMContext) -> None:
    lead_id = (await state.get_data())["lead_id"]
    await leads_q.add_note(lead_id, message.from_user.id, message.text.strip()[:1000])
    await _finish(message, state, lead_id, "✅ Izoh qo'shildi")


# ---------- Ma'lumotni tahrirlash ----------

@router.callback_query(LeadCb.filter(F.action == "edit"))
async def edit_menu(cb: CallbackQuery, callback_data: LeadCb) -> None:
    kb = InlineKeyboardBuilder()
    for field, label in (("name", "👤 Ism"), ("phone", "📱 Telefon"), ("course", "📚 Kurs"), ("source", "🔗 Manba")):
        kb.button(text=label, callback_data=LeadCb(action="ef", id=callback_data.id, val=field))
    kb.button(text=BACK, callback_data=LeadCb(action="open", id=callback_data.id))
    kb.adjust(2, 2, 1)
    await show(cb, f"✏️ Ariza #{callback_data.id}: nimani tahrirlaysiz?", kb.as_markup())


@router.callback_query(LeadCb.filter(F.action == "ef"))
async def edit_field(cb: CallbackQuery, callback_data: LeadCb, state: FSMContext) -> None:
    lead_id, field = callback_data.id, callback_data.val
    if field in ("name", "phone"):
        await state.set_state(LeadInput.field)
        await state.update_data(lead_id=lead_id, field=field)
        prompt = "Yangi ismni yozing:" if field == "name" else "Yangi telefon raqamni yozing (+998XXXXXXXXX):"
        await cb.message.answer(prompt, reply_markup=cancel_kb())
        await cb.answer()
        return
    kb = InlineKeyboardBuilder()
    if field == "course":
        for c in await catalog.list_items("course"):
            kb.button(text=c["title"], callback_data=LeadCb(action="setc", id=lead_id, val=str(c["id"])))
        kb.button(text="— Kurssiz —", callback_data=LeadCb(action="setc", id=lead_id, val="0"))
        title = "📚 Kursni tanlang:"
    else:
        for s in await sources.list_sources():
            kb.button(text=s["title"], callback_data=LeadCb(action="sets", id=lead_id, val=s["code"]))
        kb.button(text=sources.DIRECT, callback_data=LeadCb(action="sets", id=lead_id, val="-"))
        title = "🔗 Manbani tanlang:"
    kb.button(text=BACK, callback_data=LeadCb(action="edit", id=lead_id))
    kb.adjust(1)
    await show(cb, title, kb.as_markup())


@router.callback_query(LeadCb.filter(F.action == "setc"))
async def set_course(cb: CallbackQuery, callback_data: LeadCb) -> None:
    course_id = int(callback_data.val) or None
    await leads_q.update_field(callback_data.id, "course_id", course_id)
    await _render_card(cb, callback_data.id)


@router.callback_query(LeadCb.filter(F.action == "sets"))
async def set_source(cb: CallbackQuery, callback_data: LeadCb) -> None:
    code = None if callback_data.val == "-" else callback_data.val
    await leads_q.update_field(callback_data.id, "source", code)
    await _render_card(cb, callback_data.id)


@router.message(LeadInput.field, F.text)
async def field_input(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    value = message.text.strip()
    if data["field"] == "name":
        if not valid_name(value):
            await message.answer("❗️ Ism 2–50 belgi, raqamsiz bo'lishi kerak. Qayta yozing:")
            return
    else:
        value = normalize_phone(value)
        if value is None:
            await message.answer("❗️ Raqam noto'g'ri. Qayta yozing:")
            return
    await leads_q.update_field(data["lead_id"], data["field"], value)
    await _finish(message, state, data["lead_id"], f"✅ Saqlandi: {e(value)}")
