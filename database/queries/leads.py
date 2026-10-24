from datetime import datetime, timedelta, timezone
from enum import Enum

from database.db import execute, fetchall, fetchone, fetchval, now


class Status(str, Enum):
    NEW = "new"
    CALLED = "called"
    RECALL = "recall"
    NO_ANSWER = "noanswer"
    MEETING = "meeting"
    SOLD = "sold"
    NOT_SOLD = "notsold"


STATUS_LABELS: dict[str, str] = {
    Status.NEW.value: "🆕 Yangi mijoz",
    Status.CALLED.value: "📞 Telefon qilindi",
    Status.RECALL.value: "🔁 Qayta aloqa",
    Status.NO_ANSWER.value: "📵 Javob bermadi",
    Status.MEETING.value: "📅 Uchrashuv belgilandi",
    Status.SOLD.value: "✅ Sotildi",
    Status.NOT_SOLD.value: "❌ Sotilmadi",
}

TYPE_LABELS = {"enroll": "Kursga yozilish", "callback": "Qayta qo'ng'iroq"}

LEAD_SELECT = (
    "SELECT l.*, c.title AS course_title, u.telegram_id, u.username, u.full_name AS tg_name "
    "FROM leads l LEFT JOIN courses c ON c.id = l.course_id LEFT JOIN users u ON u.id = l.user_id"
)


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, status)


async def create_lead(user_id: int, course_id: int | None, name: str, phone: str,
                      lead_type: str, source: str | None) -> int:
    ts = now()
    return await execute(
        "INSERT INTO leads (user_id, course_id, name, phone, type, source, status, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 'new', ?, ?)",
        user_id, course_id, name, phone, lead_type, source, ts, ts,
    )


async def recent_duplicate(user_id: int, course_id: int | None, lead_type: str, minutes: int = 10) -> bool:
    since = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    row = await fetchone(
        "SELECT id FROM leads WHERE user_id = ? AND course_id IS ? AND type = ? AND created_at >= ?",
        user_id, course_id, lead_type, since,
    )
    return row is not None


async def get_lead(lead_id: int) -> dict | None:
    return await fetchone(f"{LEAD_SELECT} WHERE l.id = ?", lead_id)


async def list_leads(status: str | None, offset: int, limit: int) -> list[dict]:
    if status:
        return await fetchall(
            f"{LEAD_SELECT} WHERE l.status = ? ORDER BY l.id DESC LIMIT ? OFFSET ?", status, limit, offset
        )
    return await fetchall(f"{LEAD_SELECT} ORDER BY l.id DESC LIMIT ? OFFSET ?", limit, offset)


async def count_leads(status: str | None = None) -> int:
    if status:
        return await fetchval("SELECT COUNT(*) FROM leads WHERE status = ?", status)
    return await fetchval("SELECT COUNT(*) FROM leads")


async def set_status(lead_id: int, new_status: str, admin_id: int, *,
                     meeting_at: str | None = None, reject_reason: str | None = None) -> None:
    lead = await fetchone("SELECT status FROM leads WHERE id = ?", lead_id)
    if lead is None:
        return
    ts = now()
    sets, args = ["status = ?", "updated_at = ?"], [new_status, ts]
    if meeting_at is not None:
        sets.append("meeting_at = ?")
        args.append(meeting_at)
    if reject_reason is not None:
        sets.append("reject_reason = ?")
        args.append(reject_reason)
    await execute(f"UPDATE leads SET {', '.join(sets)} WHERE id = ?", *args, lead_id)
    await execute(
        "INSERT INTO lead_history (lead_id, old_status, new_status, admin_id, changed_at) VALUES (?, ?, ?, ?, ?)",
        lead_id, lead["status"], new_status, admin_id, ts,
    )


async def update_field(lead_id: int, field: str, value) -> None:
    if field not in {"name", "phone", "course_id", "source"}:
        raise ValueError(field)
    await execute(f"UPDATE leads SET {field} = ?, updated_at = ? WHERE id = ?", value, now(), lead_id)


async def add_note(lead_id: int, admin_id: int, text: str) -> None:
    await execute(
        "INSERT INTO lead_notes (lead_id, admin_id, text, created_at) VALUES (?, ?, ?, ?)",
        lead_id, admin_id, text, now(),
    )
    await execute("UPDATE leads SET updated_at = ? WHERE id = ?", now(), lead_id)


async def notes(lead_id: int) -> list[dict]:
    return await fetchall("SELECT * FROM lead_notes WHERE lead_id = ? ORDER BY id", lead_id)


async def history(lead_id: int) -> list[dict]:
    return await fetchall("SELECT * FROM lead_history WHERE lead_id = ? ORDER BY id", lead_id)


# --- Statistika va eksport ---

async def stats(since: str | None) -> dict:
    where, args = ("WHERE l.created_at >= ?", [since]) if since else ("", [])
    total = await fetchval(f"SELECT COUNT(*) FROM leads l {where}", *args)
    by_status = await fetchall(f"SELECT status AS k, COUNT(*) AS n FROM leads l {where} GROUP BY status", *args)
    by_source = await fetchall(
        f"SELECT COALESCE(source, '') AS k, COUNT(*) AS n FROM leads l {where} GROUP BY k ORDER BY n DESC", *args
    )
    by_course = await fetchall(
        f"SELECT COALESCE(c.title, '— kurssiz —') AS k, COUNT(*) AS n FROM leads l "
        f"LEFT JOIN courses c ON c.id = l.course_id {where} GROUP BY k ORDER BY n DESC",
        *args,
    )
    return {"total": total, "by_status": by_status, "by_source": by_source, "by_course": by_course}


async def export_rows(since: str | None, until: str | None) -> list[dict]:
    cond, args = [], []
    if since:
        cond.append("l.created_at >= ?")
        args.append(since)
    if until:
        cond.append("l.created_at < ?")
        args.append(until)
    where = f" WHERE {' AND '.join(cond)}" if cond else ""
    rows = await fetchall(f"{LEAD_SELECT}{where} ORDER BY l.id", *args)
    for r in rows:
        r["notes"] = "; ".join(n["text"] for n in await notes(r["id"]))
    return rows
