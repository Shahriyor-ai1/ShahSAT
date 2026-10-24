"""Markaz ma'lumotlari (settings), manbalar (deep-link) va adminlar."""
import re

from aiogram import Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.queries import admins, settings, sources
from handlers.admin.panel import admin_router
from keyboards.callbacks import AdminsCb, SettingCb, SourceCb
from keyboards.inline import BACK
from keyboards.reply import ADM_ADMINS, ADM_CENTER, ADM_SOURCES, admin_menu, cancel_kb
from states.admin import AdminInput, SettingInput, SourceInput
from utils.fmt import e, to_local
from utils.ui import send_card, show

router = admin_router("admin_center")


# ================= Markaz ma'lumotlari =================

async def settings_markup():
    current = await settings.all_settings()
    kb = InlineKeyboardBuilder()
    for key, (label, _) in settings.SETTINGS.items():
        filled = "✅" if current.get(key) else "▫️"
        kb.button(text=f"{filled} {label}", callback_data=SettingCb(action="edit", key=key))
    kb.adjust(1)
    return kb.as_markup()


SETTINGS_TITLE = "🏫 <b>Markaz ma'lumotlari</b>\n✅ kiritilgan · ▫️ bo'sh\n\nTahrirlash uchun tanlang:"


@router.message(StateFilter("*"), F.text == ADM_CENTER)
async def center_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(SETTINGS_TITLE, reply_markup=await settings_markup())


@router.callback_query(SettingCb.filter(F.action == "list"))
async def center_menu_cb(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(cb, SETTINGS_TITLE, await settings_markup())


def _describe(key: str, value: str | None) -> str:
    if not value:
        return "<i>(bo'sh)</i>"
    if key == "location":
        return f"<code>{e(value)}</code>"
    if key == "about_photo_id":
        return "🖼 rasm/video yuklangan"
    return e(value)


@router.callback_query(SettingCb.filter(F.action == "edit"))
async def setting_edit(cb: CallbackQuery, callback_data: SettingCb, state: FSMContext) -> None:
    key = callback_data.key
    label, kind = settings.SETTINGS[key]
    current = await settings.get(key)
    ask = {
        "text": "Yangi matnni yozing.",
        "media": "Rasm yoki video yuboring.",
        "location": "Telegram'dagi 📎 → «Location» orqali xaritadan nuqta yuboring.",
    }[kind]
    await state.set_state(SettingInput.value)
    await state.update_data(key=key)
    await cb.message.answer(
        f"<b>{label}</b>\n\nHozirgi qiymat:\n{_describe(key, current)}\n\n{ask}\n<i>Tozalash uchun «-» yuboring.</i>",
        reply_markup=cancel_kb(),
    )
    await cb.answer()


@router.message(SettingInput.value)
async def setting_value(message: Message, state: FSMContext) -> None:
    key = (await state.get_data())["key"]
    label, kind = settings.SETTINGS[key]
    value = None
    if message.text and message.text.strip() == "-":
        value = ""
    elif kind == "text" and message.text:
        value = message.text.strip()[:3500]
    elif kind == "media" and (message.photo or message.video):
        value = f"photo:{message.photo[-1].file_id}" if message.photo else f"video:{message.video.file_id}"
    elif kind == "location" and message.location:
        value = f"{message.location.latitude},{message.location.longitude}"
    if value is None:
        await message.answer("❗️ Kutilgan turdagi qiymat yuboring (yoki «❌ Bekor qilish»).")
        return
    await state.update_data(value=value)
    await state.set_state(SettingInput.confirm)

    # Oldindan ko'rish
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Saqlash", callback_data=SettingCb(action="save", key=key))
    kb.button(text="❌ Bekor qilish", callback_data=SettingCb(action="list"))
    kb.adjust(2)
    await message.answer("👀 <b>Oldindan ko'rish:</b>", reply_markup=cancel_kb())
    if not value:
        await message.answer(f"{label}: <i>tozalanadi</i>", reply_markup=kb.as_markup())
    elif kind == "media":
        kind_, _, file_id = value.partition(":")
        await send_card(message, label, kb.as_markup(),
                        photo=file_id if kind_ == "photo" else None, video=file_id if kind_ == "video" else None)
    elif kind == "location":
        lat, lon = map(float, value.split(","))
        await message.answer_location(latitude=lat, longitude=lon)
        await message.answer(label, reply_markup=kb.as_markup())
    else:
        await message.answer(e(value), reply_markup=kb.as_markup())


@router.callback_query(SettingInput.confirm, SettingCb.filter(F.action == "save"))
async def setting_save(cb: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    await settings.set(data["key"], data["value"] or None)
    await cb.answer("Saqlandi ✅")
    await cb.message.edit_reply_markup(reply_markup=None)
    await cb.message.answer("✅ Saqlandi — foydalanuvchilarga darhol ko'rinadi.", reply_markup=admin_menu())
    await cb.message.answer(SETTINGS_TITLE, reply_markup=await settings_markup())


@router.callback_query(SettingCb.filter(F.action == "save"))
async def setting_save_stale(cb: CallbackQuery) -> None:
    await cb.answer("Bu tugma eskirgan", show_alert=True)


# ================= Manbalar =================

async def sources_view(bot: Bot) -> tuple[str, object]:
    me = await bot.me()
    items = await sources.list_sources()
    text = "🔗 <b>Manbalar</b>\n\nHar bir reklama joyi uchun alohida havola. Shu havola orqali kelganlarning arizasida manba avtomatik ko'rinadi.\n\n"
    for s in items:
        text += f"• <b>{e(s['title'])}</b>\n<code>https://t.me/{me.username}?start={s['code']}</code>\n"
    if not items:
        text += "<i>Hozircha manba yo'q.</i>\n"
    text += f"\nParametrsiz kelganlar — «{sources.DIRECT}»."
    kb = InlineKeyboardBuilder()
    for s in items:
        kb.button(text=f"🗑 {s['title']}", callback_data=SourceCb(action="del", id=s["id"]))
    kb.button(text="➕ Manba qo'shish", callback_data=SourceCb(action="add"))
    kb.adjust(2)
    return text, kb.as_markup()


@router.message(StateFilter("*"), F.text == ADM_SOURCES)
async def sources_menu(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    text, kb = await sources_view(bot)
    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(SourceCb.filter(F.action == "del"))
async def source_delete(cb: CallbackQuery, callback_data: SourceCb, bot: Bot) -> None:
    await sources.delete_source(callback_data.id)
    text, kb = await sources_view(bot)
    await show(cb, text, kb)


@router.callback_query(SourceCb.filter(F.action == "add"))
async def source_add(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SourceInput.title)
    await cb.message.answer("Manba nomini yozing (masalan: Instagram reklama):", reply_markup=cancel_kb())
    await cb.answer()


@router.message(SourceInput.title, F.text)
async def source_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip()[:60])
    await state.set_state(SourceInput.code)
    await message.answer("Havola uchun qisqa kod yozing — faqat lotin harflari, raqam va «_» (masalan: <code>instagram</code>):")


@router.message(SourceInput.code, F.text)
async def source_code(message: Message, state: FSMContext, bot: Bot) -> None:
    code = message.text.strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{1,32}", code):
        await message.answer("❗️ Faqat lotin harflari, raqam va «_», 32 belgigacha. Qayta yozing:")
        return
    title = (await state.get_data())["title"]
    try:
        await sources.add_source(code, title)
    except Exception:
        await message.answer("❗️ Bu kod allaqachon mavjud. Boshqa kod yozing:")
        return
    await state.clear()
    me = await bot.me()
    await message.answer(f"✅ Manba qo'shildi!\n\nHavola:\n<code>https://t.me/{me.username}?start={code}</code>",
                         reply_markup=admin_menu())


# ================= Adminlar =================

async def admins_view() -> tuple[str, object]:
    text = "👥 <b>Adminlar</b>\n\n"
    kb = InlineKeyboardBuilder()
    for a in await admins.list_admins():
        role = "👑 bosh admin" if a["is_super"] else "admin"
        text += f"• <code>{a['telegram_id']}</code> — {role}, {to_local(a['added_at'])}\n"
        if not a["is_super"]:
            kb.button(text=f"🗑 {a['telegram_id']}", callback_data=AdminsCb(action="del", id=a["telegram_id"]))
    kb.button(text="➕ Admin qo'shish", callback_data=AdminsCb(action="add"))
    kb.adjust(2)
    return text, kb.as_markup()


@router.message(StateFilter("*"), F.text == ADM_ADMINS)
async def admins_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    if not admins.is_super(message.from_user.id):
        await message.answer("⛔️ Bu bo'lim faqat bosh admin uchun.")
        return
    text, kb = await admins_view()
    await message.answer(text, reply_markup=kb)


@router.callback_query(AdminsCb.filter())
async def admins_cb(cb: CallbackQuery, callback_data: AdminsCb, state: FSMContext) -> None:
    if not admins.is_super(cb.from_user.id):
        await cb.answer("Faqat bosh admin uchun", show_alert=True)
        return
    if callback_data.action == "add":
        await state.set_state(AdminInput.tg_id)
        await cb.message.answer("Yangi adminning Telegram ID raqamini yuboring\n"
                                "(ID'ni @userinfobot orqali bilish mumkin):", reply_markup=cancel_kb())
        await cb.answer()
        return
    await admins.remove_admin(callback_data.id)
    text, kb = await admins_view()
    await show(cb, text, kb)


@router.message(AdminInput.tg_id)
async def admin_add_input(message: Message, state: FSMContext, bot: Bot) -> None:
    if not admins.is_super(message.from_user.id):
        await state.clear()
        return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("❗️ Faqat raqamlardan iborat Telegram ID yuboring:")
        return
    await admins.add_admin(int(raw), message.from_user.id)
    await state.clear()
    await message.answer(f"✅ <code>{raw}</code> admin qilindi. U /admin buyrug'i bilan panelga kira oladi.",
                         reply_markup=admin_menu())
    try:
        await bot.send_message(int(raw), "Siz ShahSAT botida admin qilib tayinlandingiz. Panel: /admin")
    except Exception:
        pass
