"""models/discount.py - chegirma turlari (I ning ishi).

Discount - abstract sinf. Har bir tur apply() ni o'zicha bajaradi
(polimorfizm): sotuv qaysi chegirma ekanini bilmasdan apply() ni chaqiradi.
"""

from abc import ABC, abstractmethod

from exceptions import ValidationError
from models.product import is_whole_number


class Discount(ABC):
    """Chegirma (abstract)."""

    kind = ""   # 'none', 'percent' yoki 'fixed'
    value = 0

    @abstractmethod
    def apply(self, total):
        """Chegirmadan keyingi summani qaytaradi."""

    @property
    @abstractmethod
    def text(self):
        """Chekda ko'rinadigan matn: '10%' yoki '5000 so'm' (chegirma yo'q bo'lsa '')."""

    def check(self, total):
        """Chegirma shu summaga qo'llanishi mumkinligini tekshiradi (kerak bo'lsa xato)."""

    def to_dict(self):
        """Faylga yozish uchun lug'at."""
        return {"kind": self.kind, "value": self.value}


class NoDiscount(Discount):
    """Chegirma yo'q."""

    kind = "none"

    def apply(self, total):
        return total

    @property
    def text(self):
        return ""


class PercentDiscount(Discount):
    """Foizli chegirma: 1 dan 100 gacha."""

    kind = "percent"

    def __init__(self, value):
        if not is_whole_number(value) or not 1 <= value <= 100:
            raise ValidationError("Chegirma foizi 1 dan 100 gacha butun son bo'lishi kerak")
        self.value = value

    def apply(self, total):
        amount = (total * self.value + 50) // 100  # butun so'mga yaxlitlanadi
        return total - amount

    @property
    def text(self):
        return f"{self.value}%"


class FixedDiscount(Discount):
    """Aniq summali chegirma (so'mda)."""

    kind = "fixed"

    def __init__(self, value):
        if not is_whole_number(value) or value < 1:
            raise ValidationError("Chegirma summasi 0 dan katta butun son bo'lishi kerak")
        self.value = value

    def check(self, total):
        if self.value > total:
            raise ValidationError("Chegirma jami summadan katta bo'lmasligi kerak")

    def apply(self, total):
        return max(total - self.value, 0)

    @property
    def text(self):
        return f"{self.value} so'm"


def create_discount(kind, value=0):
    """kind bo'yicha mos chegirma yasaydi: 'none', 'percent' yoki 'fixed'."""
    if kind == "none":
        return NoDiscount()
    if kind == "percent":
        return PercentDiscount(value)
    if kind == "fixed":
        return FixedDiscount(value)
    raise ValidationError(f"Chegirma turi noto'g'ri: {kind}")
