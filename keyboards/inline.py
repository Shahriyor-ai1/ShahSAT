from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.queries.leads import STATUS_LABELS
from keyboards.callbacks import CourseCb, EnrollCb, FaqCb, LeadCb, LeadsCb, MentorCb

BACK = "⬅️ Orqaga"


def courses_list(courses: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in courses:
        kb.button(text=c["title"], callback_data=CourseCb(action="open", id=c["id"]))
    kb.adjust(1)
    return kb.as_markup()


def course_card(course_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✍️ Shu kursga yozilish", callback_data=CourseCb(action="enroll", id=course_id))
    kb.button(text=BACK, callback_data=CourseCb(action="list"))
    kb.adjust(1)
    return kb.as_markup()


def mentors_list(mentors: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for m in mentors:
        kb.button(text=m["full_name"], callback_data=MentorCb(action="open", id=m["id"]))
    kb.adjust(1)
    return kb.as_markup()


def back_to(cb) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=BACK, callback_data=cb.pack())]])


def faq_list(items: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for f in items:
        kb.button(text=f["question"][:60], callback_data=FaqCb(action="open", id=f["id"]))
    kb.adjust(1)
    return kb.as_markup()


def enroll_courses(courses: list[dict]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for c in courses:
        kb.button(text=c["title"], callback_data=EnrollCb(action="pick", id=c["id"]))
    kb.adjust(1)
    return kb.as_markup()


def enroll_confirm() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Tasdiqlash", callback_data=EnrollCb(action="confirm"))
    kb.button(text="✏️ Qayta kiritish", callback_data=EnrollCb(action="retry"))
    kb.adjust(2)
    return kb.as_markup()


def lead_kb(lead: dict, back: str | None = "all") -> InlineKeyboardMarkup:
    """Lid kartochkasi: 7 status, izoh, tahrirlash va orqaga."""

    kb = InlineKeyboardBuilder()
    for code, label in STATUS_LABELS.items():
        mark = "• " if lead["status"] == code else ""
        kb.button(text=f"{mark}{label}", callback_data=LeadCb(action="st", id=lead["id"], val=code))
    kb.button(text="📝 Izoh qo'shish", callback_data=LeadCb(action="note", id=lead["id"]))
    kb.button(text="✏️ Ma'lumotni tahrirlash", callback_data=LeadCb(action="edit", id=lead["id"]))
    sizes = [2, 2, 2, 1, 2]
    if back is not None:
        kb.button(text=BACK, callback_data=LeadsCb(status=back, page=0))
        sizes.append(1)
    kb.adjust(*sizes)
    return kb.as_markup()
