from database.db import execute, fetchall, fetchone

# Kalit -> admin panelda ko'rinadigan nom va kutiladigan qiymat turi
SETTINGS: dict[str, tuple[str, str]] = {
    "welcome_text": ("👋 Salomlashish matni", "text"),
    "thanks_text": ("🙏 Ariza uchun rahmat matni", "text"),
    "about_text": ("ℹ️ Markaz haqida", "text"),
    "about_photo_id": ("🖼 Markaz rasmi / videosi", "media"),
    "address_text": ("🏠 Manzil (matn)", "text"),
    "landmark_text": ("🧭 Mo'ljal", "text"),
    "location": ("📍 Lokatsiya (xarita nuqtasi)", "location"),
    "work_hours": ("🕘 Ish vaqti", "text"),
    "contacts_text": ("☎️ Aloqa matni (telefonlar)", "text"),
    "contact_telegram": ("✈️ Telegram admin (@username)", "text"),
    "contact_instagram": ("📸 Instagram havolasi", "text"),
    "contact_website": ("🌐 Sayt havolasi", "text"),
}

DEFAULTS = {
    "welcome_text": "Assalomu alaykum! ShahSAT o'quv markazi botiga xush kelibsiz.\nKerakli bo'limni tanlang 👇",
    "thanks_text": "Rahmat! Tez orada siz bilan bog'lanamiz ✅",
}


async def get(key: str, default: str | None = None) -> str | None:
    row = await fetchone("SELECT value FROM settings WHERE key = ?", key)
    if row and row["value"]:
        return row["value"]
    return default if default is not None else DEFAULTS.get(key)


async def get_many(*keys: str) -> dict[str, str | None]:
    return {k: await get(k) for k in keys}


async def set(key: str, value: str | None) -> None:
    await execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        key, value,
    )


async def all_settings() -> dict[str, str]:
    rows = await fetchall("SELECT key, value FROM settings")
    return {r["key"]: r["value"] for r in rows}
