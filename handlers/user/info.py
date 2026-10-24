"""Manzil, aloqa va markaz haqida bo'limlari."""
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from database.queries import settings
from keyboards.reply import BTN_ABOUT, BTN_ADDRESS, BTN_CONTACTS
from utils.fmt import NO_DATA, e
from utils.ui import send_card

router = Router(name="user_info")
router.message.filter(F.chat.type == "private")


@router.message(StateFilter("*"), F.text == BTN_ADDRESS)
async def address(message: Message, state: FSMContext) -> None:
    await state.clear()
    s = await settings.get_many("location", "address_text", "landmark_text", "work_hours")
    if s["location"]:
        lat, lon = map(float, s["location"].split(","))
        await message.answer_location(latitude=lat, longitude=lon)
    parts = []
    if s["address_text"]:
        parts.append(f"🏠 <b>Manzil:</b> {e(s['address_text'])}")
    if s["landmark_text"]:
        parts.append(f"🧭 <b>Mo'ljal:</b> {e(s['landmark_text'])}")
    if s["work_hours"]:
        parts.append(f"🕘 <b>Ish vaqti:</b> {e(s['work_hours'])}")
    if parts:
        await message.answer("\n".join(parts))
    elif not s["location"]:
        await message.answer(NO_DATA)


def _url(value: str, kind: str) -> str:
    value = value.strip()
    if value.startswith(("http://", "https://")):
        return value
    handle = value.lstrip("@")
    if kind == "telegram":
        return f"https://t.me/{handle}"
    if kind == "instagram":
        return f"https://instagram.com/{handle}"
    return f"https://{value}"


@router.message(StateFilter("*"), F.text == BTN_CONTACTS)
async def contacts(message: Message, state: FSMContext) -> None:
    await state.clear()
    s = await settings.get_many("contacts_text", "contact_telegram", "contact_instagram", "contact_website")
    buttons = []
    for key, label, kind in (("contact_telegram", "✈️ Telegram admin", "telegram"),
                             ("contact_instagram", "📸 Instagram", "instagram"),
                             ("contact_website", "🌐 Sayt", "web")):
        if s[key]:
            buttons.append([InlineKeyboardButton(text=label, url=_url(s[key], kind))])
    if not s["contacts_text"] and not buttons:
        await message.answer(NO_DATA)
        return
    text = f"☎️ <b>Aloqa</b>\n\n{e(s['contacts_text'] or '')}".strip()
    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None)


@router.message(StateFilter("*"), F.text == BTN_ABOUT)
async def about(message: Message, state: FSMContext) -> None:
    await state.clear()
    text = await settings.get("about_text")
    media = await settings.get("about_photo_id")
    if not text and not media:
        await message.answer(NO_DATA)
        return
    photo = video = None
    if media:
        kind, _, file_id = media.partition(":")
        photo, video = (file_id, None) if kind == "photo" else (None, file_id)
    await send_card(message, f"ℹ️ <b>Markaz haqida</b>\n\n{e(text or '')}".strip(), photo=photo, video=video)
