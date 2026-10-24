import re


def normalize_phone(raw: str) -> str | None:
    """Raqamni +998XXXXXXXXX ko'rinishiga keltiradi. 9 yoki 12 raqam qabul qilinadi."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 9:
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+" + digits
    return None


def valid_name(name: str) -> bool:
    name = (name or "").strip()
    return 2 <= len(name) <= 50 and not any(ch.isdigit() for ch in name)
