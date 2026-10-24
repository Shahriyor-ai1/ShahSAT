from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- Foydalanuvchi menyusi ---
BTN_COURSES = "📚 Kurslar"
BTN_MENTORS = "👨‍🏫 Mentorlar"
BTN_ENROLL = "✍️ Kursga yozilish"
BTN_CALLBACK = "📞 Nomer qoldirish"
BTN_ADDRESS = "📍 Manzil"
BTN_CONTACTS = "☎️ Aloqa"
BTN_ABOUT = "ℹ️ Markaz haqida"
BTN_FAQ = "❓ Ko'p so'raladigan savollar"

MAIN_BUTTONS = [BTN_COURSES, BTN_MENTORS, BTN_ENROLL, BTN_CALLBACK, BTN_ADDRESS, BTN_CONTACTS, BTN_ABOUT, BTN_FAQ]

BTN_CANCEL = "❌ Bekor qilish"
BTN_SKIP = "⏭ O'tkazib yuborish"
BTN_SEND_PHONE = "📱 Raqamni yuborish"

# --- Admin menyusi ---
ADM_LEADS = "📥 Arizalar"
ADM_STATS = "📊 Statistika"
ADM_CENTER = "🏫 Markaz ma'lumotlari"
ADM_COURSES = "📚 Kurslarni boshqarish"
ADM_MENTORS = "👨‍🏫 Mentorlarni boshqarish"
ADM_FAQ = "❓ FAQ"
ADM_SOURCES = "🔗 Manbalar"
ADM_BROADCAST = "📢 Xabar yuborish"
ADM_EXPORT = "📤 Excel eksport"
ADM_ADMINS = "👥 Adminlar"
ADM_EXIT = "🏠 Asosiy menyu"

ADMIN_BUTTONS = [ADM_LEADS, ADM_STATS, ADM_CENTER, ADM_COURSES, ADM_MENTORS, ADM_FAQ,
                 ADM_SOURCES, ADM_BROADCAST, ADM_EXPORT, ADM_ADMINS, ADM_EXIT]


def _grid(buttons: list[str], cols: int = 2) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for b in buttons:
        kb.button(text=b)
    kb.adjust(cols)
    return kb.as_markup(resize_keyboard=True)


def main_menu() -> ReplyKeyboardMarkup:
    return _grid(MAIN_BUTTONS)


def admin_menu() -> ReplyKeyboardMarkup:
    return _grid(ADMIN_BUTTONS)


def cancel_kb() -> ReplyKeyboardMarkup:
    return _grid([BTN_CANCEL], 1)


def skip_cancel_kb() -> ReplyKeyboardMarkup:
    return _grid([BTN_SKIP, BTN_CANCEL], 2)


def phone_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_SEND_PHONE, request_contact=True)], [KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )
