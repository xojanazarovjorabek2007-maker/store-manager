"""exceptions.py - dasturdagi barcha xato turlari (I ning ishi).

Hamma xato AppError dan tarqaladi, shuning uchun menyu (ui/menu.py)
faqat `except AppError as error: print(error)` qilsa yetadi.
Xabarlar o'zbekcha va foydalanuvchiga tayyor holda yoziladi.
"""


class AppError(Exception):
    """Dasturdagi barcha kutilgan xatolarning umumiy asosi."""


class ValidationError(AppError):
    """Noto'g'ri qiymat kiritilganda: narx <= 0, bo'sh nom va hokazo."""


class ProductNotFoundError(AppError):
    """Berilgan ID bo'yicha mahsulot topilmaganda."""

    def __init__(self, pid):
        super().__init__(f"Mahsulot topilmadi (ID: {pid})")
        self.pid = pid


class OutOfStockError(AppError):
    """Omborda yetarli mahsulot qolmaganda."""

    def __init__(self, name, available):
        super().__init__(f"'{name}' yetarli emas, qoldiq: {available}")
        self.name = name
        self.available = available


class AuthError(AppError):
    """Login yoki parol xato bo'lganda."""

    def __init__(self, message="Login yoki parol xato!"):
        super().__init__(message)


class PermissionDeniedError(AppError):
    """Foydalanuvchining bu amalga ruxsati yo'q bo'lganda."""

    def __init__(self, message="Bu amalga ruxsat yo'q."):
        super().__init__(message)


class StorageError(AppError):
    """Ma'lumot fayli buzilgan yoki unga yozib bo'lmaganda."""
