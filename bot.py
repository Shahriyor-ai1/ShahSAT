"""Kirish nuqtasi: Bot, Dispatcher, routerlar va long polling."""
import asyncio
import logging
import traceback

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault, ErrorEvent

import config
from database import db
from database.queries import admins
from handlers.admin import broadcast, catalog as admin_catalog, center, leads, panel, stats
from handlers.user import catalog as user_catalog, enroll, info, start
from middlewares.menu_reset import MenuResetMiddleware
from middlewares.throttling import ThrottlingMiddleware
from utils.backup import backup_loop
from utils.notify import notify_super

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("shahsat")


async def on_error(event: ErrorEvent, bot: Bot) -> bool:
    """Global xato ushlagich: logga yozadi va bosh adminga qisqa xabar yuboradi."""
    exc = event.exception
    log.exception("Handler xatosi: %s", exc, exc_info=exc)
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))[-1500:]
    await notify_super(bot, f"⚠️ Botda xato: {type(exc).__name__}: {exc}\n\n{tb}")
    # Foydalanuvchiga ham qisqa javob
    try:
        upd = event.update
        if upd.callback_query:
            await upd.callback_query.answer("Xatolik yuz berdi, qaytadan urinib ko'ring", show_alert=True)
        elif upd.message:
            await upd.message.answer("Xatolik yuz berdi, qaytadan urinib ko'ring 🙏")
    except Exception:
        pass
    return True


async def set_commands(bot: Bot) -> None:
    await bot.set_my_commands([BotCommand(command="start", description="Asosiy menyu")],
                              scope=BotCommandScopeDefault())
    admin_cmds = [BotCommand(command="start", description="Asosiy menyu"),
                  BotCommand(command="admin", description="Admin panel")]
    for admin_id in admins.all_ids():
        try:
            await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception:
            pass  # admin botni hali ishga tushirmagan bo'lishi mumkin


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.message.outer_middleware(ThrottlingMiddleware())
    dp.message.outer_middleware(MenuResetMiddleware())
    dp.errors.register(on_error)
    dp.include_routers(
        start.router,             # /start va «Bekor qilish» — har doim birinchi
        panel.router,
        leads.router,
        admin_catalog.router,
        center.router,
        stats.router,
        broadcast.router,
        user_catalog.router,
        info.router,
        enroll.router,
        start.fallback_router,    # noma'lum matn — eng oxirida
    )
    return dp


async def main() -> None:
    await db.init_db()
    await admins.seed()
    session = AiohttpSession(proxy=config.PROXY_URL) if config.PROXY_URL else None
    bot = Bot(config.BOT_TOKEN, session=session, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher()
    await set_commands(bot)
    await bot.delete_webhook(drop_pending_updates=False)
    me = await bot.me()
    log.info("Bot ishga tushdi: @%s", me.username)
    backup_task = asyncio.create_task(backup_loop(bot))
    try:
        await dp.start_polling(bot)
    finally:
        backup_task.cancel()
        await db.close_db()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
