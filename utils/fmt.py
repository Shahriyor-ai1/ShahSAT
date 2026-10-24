"""Vaqt va matn formatlash yordamchilari."""
from datetime import datetime, timedelta, timezone
from html import escape

import config


def e(value) -> str:
    """HTML uchun xavfsiz matn."""
    return escape(str(value)) if value is not None else ""


def to_local(utc_str: str | None) -> str:
    if not utc_str:
        return "—"
    dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return dt.astimezone(config.TASHKENT).strftime("%d.%m.%Y %H:%M")


def utc_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def period_start(period: str) -> str | None:
    """'today' | 'week' | 'month' | 'all' davrining boshlanishini UTC qatorida qaytaradi."""
    now_local = datetime.now(config.TASHKENT)
    if period == "today":
        return utc_str(now_local.replace(hour=0, minute=0, second=0, microsecond=0))
    if period == "week":
        return utc_str(now_local - timedelta(days=7))
    if period == "month":
        return utc_str(now_local - timedelta(days=30))
    return None


def parse_local_date(text: str) -> datetime | None:
    try:
        return datetime.strptime(text.strip(), "%d.%m.%Y").replace(tzinfo=config.TASHKENT)
    except ValueError:
        return None


PERIOD_LABELS = {"today": "Bugun", "week": "Oxirgi 7 kun", "month": "Oxirgi 30 kun", "all": "Hammasi"}

NO_DATA = "Ma'lumot tez orada qo'shiladi ⏳"
