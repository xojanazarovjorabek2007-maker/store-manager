"""models/product.py - mahsulot (I ning ishi).

Bu yerda faqat ma'lumot shakli va uni tekshirish bor.
Ekranga chiqarish va kiritish (print, input) bu yerda ishlatilmaydi.
"""

from exceptions import OutOfStockError, StorageError, ValidationError


def is_whole_number(value):
    """Butun son bo'lsa True. (True/False butun son hisoblanmaydi.)"""
    return isinstance(value, int) and not isinstance(value, bool)


def check_price(value):
    """Narxni tekshiradi: 0 dan katta butun son. To'g'ri bo'lsa, o'zini qaytaradi."""
    if not is_whole_number(value):
        raise ValidationError("Narx butun son bo'lishi kerak")
    if value <= 0:
        raise ValidationError("Narx 0 dan katta bo'lishi kerak")
    return value


def check_stock(value):
    """Sonni tekshiradi: 0 yoki undan katta butun son."""
    if not is_whole_number(value):
        raise ValidationError("Soni butun son bo'lishi kerak")
    if value < 0:
        raise ValidationError("Soni manfiy bo'lmasligi kerak")
    return value


class Product:
    """Do'kondagi bitta mahsulot: ID, nom, narx va ombordagi soni."""

    def __init__(self, pid, name, price, stock):
        self.pid = pid
        self.name = name      # name setter tekshiradi
        self.price = price    # price setter tekshiradi
        self.stock = stock    # stock setter tekshiradi

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Mahsulot nomi bo'sh bo'lmasligi kerak")
        self._name = value.strip()

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        self._price = check_price(value)

    @property
    def stock(self):
        return self._stock

    @stock.setter
    def stock(self, value):
        self._stock = check_stock(value)

    def reduce_stock(self, qty):
        """Ombordagi sonni qty ga kamaytiradi. Yetarli bo'lmasa OutOfStockError."""
        if not is_whole_number(qty) or qty <= 0:
            raise ValidationError("Soni 0 dan katta butun son bo'lishi kerak")
        if qty > self._stock:
            raise OutOfStockError(self.name, self._stock)
        self._stock -= qty

    def to_dict(self):
        """Faylga yozish uchun lug'at."""
        return {"pid": self.pid, "name": self.name, "price": self.price, "stock": self.stock}

    @classmethod
    def from_dict(cls, data):
        """Fayldan o'qilgan lug'atdan mahsulot yasaydi."""
        try:
            pid = data["pid"]
            if not is_whole_number(pid):
                raise ValidationError("ID butun son bo'lishi kerak")
            return cls(pid, data["name"], data["price"], data["stock"])
        except KeyError as error:
            raise StorageError(f"Fayldagi mahsulotda {error} maydoni yo'q")
        except (TypeError, ValidationError) as error:
            raise StorageError(f"Fayldagi mahsulot ma'lumoti noto'g'ri: {error}")

    def __str__(self):
        return f"{self.pid}. {self.name} - {self.price} so'm (qoldiq: {self.stock})"
