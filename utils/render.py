"""Kurs, mentor va ariza kartochkalari matni."""
from database.queries import catalog, leads as leads_q, sources
from utils.fmt import e, to_local


def _line(icon: str, label: str, value) -> str:
    return f"{icon} <b>{label}:</b> {e(value)}\n" if value else ""


async def course_text(c: dict, active_only: bool = True) -> str:
    mentors = await catalog.mentors_of_course(c["id"], active_only=active_only)
    text = f"📚 <b>{e(c['title'])}</b>\n\n"
    if c.get("description"):
        text += f"{e(c['description'])}\n\n"
    text += _line("⏳", "Davomiyligi", c.get("duration"))
    text += _line("💰", "Narxi", c.get("price"))
    text += _line("🗓", "Dars kunlari / vaqti", c.get("schedule"))
    if mentors:
        text += _line("👨‍🏫", "Mentor(lar)", ", ".join(m["full_name"] for m in mentors))
    return text.strip()


async def mentor_text(m: dict, active_only: bool = True) -> str:
    courses = await catalog.courses_of_mentor(m["id"], active_only=active_only)
    text = f"👨‍🏫 <b>{e(m['full_name'])}</b>\n\n"
    text += _line("🎯", "Mutaxassislik", m.get("specialty"))
    text += _line("📈", "Tajriba", m.get("experience"))
    text += _line("🏆", "SAT natijasi", m.get("sat_score"))
    if courses:
        text += _line("📚", "Kurs(lar)", ", ".join(c["title"] for c in courses))
    if m.get("bio"):
        text += f"\n{e(m['bio'])}"
    return text.strip()


def telegram_link(lead: dict) -> str:
    if lead.get("username"):
        return f"@{e(lead['username'])}"
    if lead.get("telegram_id"):
        return f'<a href="tg://user?id={lead["telegram_id"]}">{e(lead.get("tg_name") or "profil")}</a>'
    return "—"


async def lead_text(lead: dict, title: str | None = None, full: bool = False) -> str:
    title = title or f"📋 Ariza #{lead['id']}"
    text = (
        f"<b>{title}</b>\n\n"
        f"📚 <b>Kurs:</b> {e(lead.get('course_title') or '—')}\n"
        f"👤 <b>Ism:</b> {e(lead['name'])}\n"
        f"📱 <b>Telefon:</b> {e(lead['phone'])}\n"
        f"✈️ <b>Telegram:</b> {telegram_link(lead)}\n"
        f"🔗 <b>Manba:</b> {e(await sources.title_of(lead.get('source')))}\n"
        f"📝 <b>Turi:</b> {leads_q.TYPE_LABELS.get(lead['type'], lead['type'])}\n"
        f"🕒 <b>Sana:</b> {to_local(lead['created_at'])}\n"
        f"📌 <b>Status:</b> {leads_q.status_label(lead['status'])}\n"
    )
    if lead.get("meeting_at"):
        text += f"📅 <b>Uchrashuv:</b> {e(lead['meeting_at'])}\n"
    if lead.get("reject_reason"):
        text += f"🚫 <b>Rad sababi:</b> {e(lead['reject_reason'])}\n"
    if full:
        hist = await leads_q.history(lead["id"])
        if hist:
            text += "\n<b>🕘 Status tarixi:</b>\n"
            for h in hist[-10:]:
                text += (f"• {to_local(h['changed_at'])} — {leads_q.status_label(h['old_status'])} → "
                         f"{leads_q.status_label(h['new_status'])} (admin <code>{h['admin_id']}</code>)\n")
        notes = await leads_q.notes(lead["id"])
        if notes:
            text += "\n<b>📝 Izohlar:</b>\n"
            for n in notes[-10:]:
                text += f"• {to_local(n['created_at'])}: {e(n['text'])}\n"
    return text.strip()
