import asyncio
import logging
import os
import tempfile
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import FSInputFile

import config
from database import db

log = logging.getLogger(__name__)

BACKUP_HOUR = 3  # Toshkent vaqti bilan har kuni 03:00 da


async def send_backup(bot: Bot) -> None:
    path = os.path.join(tempfile.gettempdir(), "shahsat_backup.db")
    await db.snapshot(path)
    stamp = datetime.now(config.TASHKENT).strftime("%Y-%m-%d_%H-%M")
    await bot.send_document(
        config.SUPER_ADMIN_ID,
        FSInputFile(path, filename=f"shahsat_{stamp}.db"),
        caption="💾 Kunlik zaxira nusxa (backup)",
    )
    os.remove(path)


async def backup_loop(bot: Bot) -> None:
    while True:
        now = datetime.now(config.TASHKENT)
        target = now.replace(hour=BACKUP_HOUR, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())
        try:
            await send_backup(bot)
            log.info("Backup yuborildi")
        except Exception:
            log.exception("Backup yuborishda xato")
