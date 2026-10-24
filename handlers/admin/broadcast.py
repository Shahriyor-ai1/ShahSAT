"""Barcha foydalanuvchilarga xabar (reklama / e'lon) yuborish."""
import asyncio
import logging

from aiogram import Bot, F
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.queries import users
from handlers.admin.panel import admin_router
from keyboards.callbacks import BroadcastCb
from keyboards.reply import ADM_BROADCAST, admin_menu, cancel_kb
from states.admin import BroadcastInput

router = admin_router("admin_broadcast")
log = logging.getLogger(__name__)


@router.message(StateFilter("*"), F.text == ADM_BROADCAST, F.chat.type == "private")
async def broadcast_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BroadcastInput.content)
    await message.answer("📢 Yubormoqchi bo'lgan xabarni jo'nating (matn, rasm yoki video — izoh bilan):",
                         reply_markup=cancel_kb())


@router.message(BroadcastInput.content)
async def broadcast_content(message: Message, state: FSMContext) -> None:
    await state.update_data(chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(BroadcastInput.confirm)
    count = len(await users.active_ids())
    await message.answer("👀 Oldindan ko'rish:")
    await message.copy_to(message.chat.id)
    kb = InlineKeyboardBuilder()
    kb.button(text=f"✅ Yuborish ({count} kishi)", callback_data=BroadcastCb(action="send"))
    kb.button(text="❌ Bekor qilish", callback_data=BroadcastCb(action="cancel"))
    kb.adjust(1)
    await message.answer("Yuborilsinmi?", reply_markup=kb.as_markup())


@router.callback_query(BroadcastInput.confirm, BroadcastCb.filter(F.action == "cancel"))
async def broadcast_cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.edit_text("Bekor qilindi.")
    await cb.message.answer("Admin panel 👇", reply_markup=admin_menu())


@router.callback_query(BroadcastInput.confirm, BroadcastCb.filter(F.action == "send"))
async def broadcast_send(cb: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await state.clear()
    await cb.message.edit_text("⏳ Yuborish boshlandi. Tugagach natijani yuboraman.")
    await cb.message.answer("Admin panel 👇", reply_markup=admin_menu())
    asyncio.create_task(_run(bot, cb.from_user.id, data["chat_id"], data["message_id"]))


async def _run(bot: Bot, admin_id: int, from_chat: int, message_id: int) -> None:
    ok = fail = 0
    for uid in await users.active_ids():
        try:
            await bot.copy_message(uid, from_chat, message_id)
            ok += 1
        except TelegramRetryAfter as exc:
            await asyncio.sleep(exc.retry_after)
            try:
                await bot.copy_message(uid, from_chat, message_id)
                ok += 1
            except Exception:
                fail += 1
        except TelegramForbiddenError:
            await users.set_blocked(uid)
            fail += 1
        except Exception as exc:
            log.warning("Broadcast xato (%s): %s", uid, exc)
            fail += 1
        await asyncio.sleep(0.05)  # Telegram limiti: ~20 xabar/soniya
    await bot.send_message(admin_id, f"📢 Xabar yuborildi.\n✅ Yetkazildi: {ok}\n❌ Yetkazilmadi: {fail}")


@router.callback_query(BroadcastCb.filter())
async def broadcast_stale(cb: CallbackQuery) -> None:
    await cb.answer("Bu tugma eskirgan", show_alert=True)
