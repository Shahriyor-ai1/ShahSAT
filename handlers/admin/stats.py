"""Statistika va Excel eksport."""
from datetime import timedelta

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.queries import leads as leads_q, sources, users
from database.queries.leads import STATUS_LABELS, Status
from handlers.admin.panel import admin_router
from keyboards.callbacks import ExportCb, StatsCb
from keyboards.reply import ADM_EXPORT, ADM_STATS, admin_menu, cancel_kb
from states.admin import ExportInput
from utils.export import leads_to_xlsx
from utils.fmt import PERIOD_LABELS, e, parse_local_date, period_start, utc_str
from utils.ui import show

router = admin_router("admin_stats")


def periods_markup(cb_cls, with_custom: bool = False):
    kb = InlineKeyboardBuilder()
    for code, label in PERIOD_LABELS.items():
        kb.button(text=label, callback_data=cb_cls(period=code))
    if with_custom:
        kb.button(text="📆 Sana oralig'ini kiritish", callback_data=cb_cls(period="custom"))
    kb.adjust(2, 2, 1)
    return kb.as_markup()


# ---------- Statistika ----------

async def stats_text(period: str) -> str:
    since = period_start(period)
    s = await leads_q.stats(since)
    total = s["total"]
    by_status = {r["k"]: r["n"] for r in s["by_status"]}
    sold = by_status.get(Status.SOLD.value, 0)
    conv = f"{sold / total * 100:.1f}%" if total else "—"
    text = (f"📊 <b>Statistika — {PERIOD_LABELS[period]}</b>\n\n"
            f"👥 Yangi foydalanuvchilar: <b>{await users.count_users(since)}</b>\n"
            f"📥 Arizalar: <b>{total}</b>\n"
            f"💹 Konversiya (sotildi ÷ jami): <b>{conv}</b>\n\n<b>Statuslar:</b>\n")
    for code, label in STATUS_LABELS.items():
        text += f"  {label}: {by_status.get(code, 0)}\n"
    if s["by_source"]:
        text += "\n<b>Manbalar:</b>\n"
        for r in s["by_source"]:
            text += f"  • {e(await sources.title_of(r['k'] or None))}: {r['n']}\n"
    if s["by_course"]:
        text += "\n<b>Kurslar:</b>\n"
        for r in s["by_course"]:
            text += f"  • {e(r['k'])}: {r['n']}\n"
    return text


@router.message(StateFilter("*"), F.text == ADM_STATS)
async def stats_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(await stats_text("today"), reply_markup=periods_markup(StatsCb))


@router.callback_query(StatsCb.filter())
async def stats_period(cb: CallbackQuery, callback_data: StatsCb) -> None:
    await show(cb, await stats_text(callback_data.period), periods_markup(StatsCb))


# ---------- Excel eksport ----------

async def _send_export(message: Message, since: str | None, until: str | None, label: str) -> None:
    rows = await leads_q.export_rows(since, until)
    if not rows:
        await message.answer(f"Tanlangan davrda ({label}) ariza yo'q.")
        return
    data = await leads_to_xlsx(rows)
    await message.answer_document(BufferedInputFile(data, filename="arizalar.xlsx"),
                                  caption=f"📤 Arizalar — {label} ({len(rows)} ta)")


@router.message(StateFilter("*"), F.text == ADM_EXPORT)
async def export_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("📤 <b>Excel eksport</b>\n\nDavrni tanlang:", reply_markup=periods_markup(ExportCb, True))


@router.callback_query(ExportCb.filter(F.period == "custom"))
async def export_custom(cb: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ExportInput.range)
    await cb.message.answer("Sana oralig'ini yozing: <code>01.10.2026-20.10.2026</code>", reply_markup=cancel_kb())
    await cb.answer()


@router.callback_query(ExportCb.filter())
async def export_period(cb: CallbackQuery, callback_data: ExportCb) -> None:
    await cb.answer("Tayyorlanmoqda…")
    await _send_export(cb.message, period_start(callback_data.period), None, PERIOD_LABELS[callback_data.period])


@router.message(ExportInput.range, F.text)
async def export_range(message: Message, state: FSMContext) -> None:
    parts = message.text.replace(" ", "").split("-")
    start = parse_local_date(parts[0]) if len(parts) == 2 else None
    end = parse_local_date(parts[1]) if len(parts) == 2 else None
    if not start or not end or end < start:
        await message.answer("❗️ Format: <code>01.10.2026-20.10.2026</code>. Qayta yozing:")
        return
    await state.clear()
    await message.answer("Tayyorlanmoqda…", reply_markup=admin_menu())
    await _send_export(message, utc_str(start), utc_str(end + timedelta(days=1)), message.text.strip())
