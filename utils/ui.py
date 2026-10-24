"""Inline sahifalarni chiroyli almashtirish: xabarni tahrirlash yoki rasmli kartochka yuborish."""
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

CAPTION_LIMIT = 1024


async def send_card(message: Message, text: str, kb: InlineKeyboardMarkup | None = None,
                    photo: str | None = None, video: str | None = None) -> None:
    """Yangi xabar sifatida kartochka yuboradi (rasm/video bo'lsa — media bilan)."""
    media = photo or video
    if not media:
        await message.answer(text, reply_markup=kb, disable_web_page_preview=True)
        return
    send = message.answer_photo if photo else message.answer_video
    if len(text) <= CAPTION_LIMIT:
        await send(media, caption=text, reply_markup=kb)
    else:
        await send(media)
        await message.answer(text, reply_markup=kb, disable_web_page_preview=True)


async def show(cb: CallbackQuery, text: str, kb: InlineKeyboardMarkup | None = None,
               photo: str | None = None) -> None:
    """Joriy inline xabarni yangi kontent bilan almashtiradi — chat to'lib ketmaydi."""
    msg = cb.message
    if photo or msg.photo or msg.video or msg.document:
        try:
            await msg.delete()
        except TelegramBadRequest:
            pass
        await send_card(msg, text, kb, photo=photo)
    else:
        try:
            await msg.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
        except TelegramBadRequest as exc:
            if "not modified" not in str(exc):
                await msg.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await cb.answer()
