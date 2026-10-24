"""Muhit o'zgaruvchilarini o'qish."""
import os
from datetime import timedelta, timezone

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS: list[int] = [int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x]
_chat = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_CHAT_ID: int | None = int(_chat) if _chat else None
DB_PATH: str = os.getenv("DB_PATH", "bot.db").strip()
# Ixtiyoriy: api.telegram.org bloklangan tarmoqlar uchun (http://... yoki socks5://...)
PROXY_URL: str | None = os.getenv("PROXY_URL", "").strip() or None

# Barcha vaqtlar UTC'da saqlanadi, Toshkent vaqtida (UTC+5) ko'rsatiladi
TASHKENT = timezone(timedelta(hours=5), "Asia/Tashkent")

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN topilmadi: .env faylini yoki Railway Variables'ni tekshiring")
if not ADMIN_IDS:
    raise SystemExit("ADMIN_IDS topilmadi: kamida bitta admin Telegram ID kiriting")

SUPER_ADMIN_ID: int = ADMIN_IDS[0]
