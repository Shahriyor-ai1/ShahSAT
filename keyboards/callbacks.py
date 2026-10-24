from aiogram.filters.callback_data import CallbackData


class CourseCb(CallbackData, prefix="c"):
    action: str  # list | open | enroll
    id: int = 0


class MentorCb(CallbackData, prefix="m"):
    action: str  # list | open
    id: int = 0


class FaqCb(CallbackData, prefix="f"):
    action: str  # list | open
    id: int = 0


class EnrollCb(CallbackData, prefix="e"):
    action: str  # pick | confirm | retry
    id: int = 0


class LeadsCb(CallbackData, prefix="ll"):
    """Arizalar ro'yxati: status filtri ('all' yoki status) va sahifa."""
    status: str = "all"
    page: int = 0


class LeadCb(CallbackData, prefix="l"):
    action: str  # open | st | note | edit | ef | setc | sets | hist
    id: int
    val: str = ""


class CrudCb(CallbackData, prefix="cr"):
    """Kurs / mentor / FAQ boshqaruvi."""
    ent: str  # course | mentor | faq
    action: str  # list | open | add | save | edit | toggle | del | delok | mentors | tgm
    id: int = 0
    val: str = ""


class SettingCb(CallbackData, prefix="st"):
    action: str  # list | edit | save
    key: str = ""


class SourceCb(CallbackData, prefix="src"):
    action: str  # list | add | open | del
    id: int = 0


class AdminsCb(CallbackData, prefix="adm"):
    action: str  # list | add | del
    id: int = 0


class StatsCb(CallbackData, prefix="sts"):
    period: str  # today | week | month | all


class ExportCb(CallbackData, prefix="ex"):
    period: str  # today | week | month | all | custom


class BroadcastCb(CallbackData, prefix="bc"):
    action: str  # send | cancel
