import logging

from aiogram import Bot

import config
from database.queries import admins, leads as leads_q
from keyboards.inline import lead_kb
from utils.render import lead_text

log = logging.getLogger(__name__)


async def notify_new_lead(bot: Bot, lead_id: int) -> None:
    """Yangi ariza kartochkasini guruhga (ADMIN_CHAT_ID) yoki barcha adminlarga yuboradi."""
    lead = await leads_q.get_lead(lead_id)
    text = await lead_text(lead, title=f"🆕 Yangi ariza #{lead_id}")
    targets = [config.ADMIN_CHAT_ID] if config.ADMIN_CHAT_ID else admins.all_ids()
    for chat_id in targets:
        try:
            await bot.send_message(chat_id, text, reply_markup=lead_kb(lead, back=None))
        except Exception as exc:  # bitta admin bloklagan bo'lsa ham qolganlariga ketsin
            log.warning("Adminga xabar yuborilmadi (%s): %s", chat_id, exc)


async def notify_super(bot: Bot, text: str) -> None:
    try:
        await bot.send_message(config.SUPER_ADMIN_ID, text[:4000], parse_mode=None)
    except Exception as exc:
        log.warning("Bosh adminga xabar yuborilmadi: %s", exc)
