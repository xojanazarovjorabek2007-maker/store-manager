"""models/sale.py - sotuv va uning qatorlari (I ning ishi)."""

from exceptions import StorageError, ValidationError
from models.discount import NoDiscount, create_discount


class SaleItem:
    """Sotuvdagi bitta qator: mahsulot, soni va sotilgan narxi."""

    def __init__(self, pid, name, qty, price):
        self.pid = pid
        self.name = name
        self.qty = qty
        self.price = price

    @property
    def subtotal(self):
        """Qator summasi: soni * narx."""
        return self.qty * self.price

    def to_dict(self):
        return {"pid": self.pid, "name": self.name, "qty": self.qty, "price": self.price}

    @classmethod
    def from_dict(cls, data):
        try:
            return cls(data["pid"], data["name"], data["qty"], data["price"])
        except (KeyError, TypeError):
            raise StorageError("Fayldagi sotuv qatori noto'g'ri")


class Sale:
    """Bitta sotuv (chek). id va date sotuv yakunlanganda to'ldiriladi."""

    def __init__(self, cashier, sale_id=None, date=None, items=None, discount=None):
        self.id = sale_id
        self.date = date
        self.cashier = cashier
        self.items = items if items is not None else []
        self.discount = discount if discount is not None else NoDiscount()

    @property
    def total(self):
        """Chegirmadan oldingi jami summa."""
        total = 0
        for item in self.items:
            total += item.subtotal
        return total

    @property
    def discount_text(self):
        """Chegirma matni ('10%', '5000 so'm'); chegirma yo'q bo'lsa ''."""
        return self.discount.text

    @property
    def final_total(self):
        """To'lanadigan summa (chegirmadan keyin)."""
        return self.discount.apply(self.total)

    def quantity_of(self, pid):
        """Shu mahsulotdan savatda nechta bor."""
        quantity = 0
        for item in self.items:
            if item.pid == pid:
                quantity += item.qty
        return quantity

    def add_item(self, pid, name, qty, price):
        """Savatga qator qo'shadi. Xuddi shu mahsulot bo'lsa, sonini oshiradi."""
        for item in self.items:
            if item.pid == pid and item.price == price:
                item.qty += qty
                return item
        item = SaleItem(pid, name, qty, price)
        self.items.append(item)
        return item

    def to_dict(self):
        """Faylga yozish uchun lug'at (total va final_total faqat o'qishga qulay bo'lishi uchun)."""
        return {
            "id": self.id,
            "date": self.date,
            "cashier": self.cashier,
            "items": [item.to_dict() for item in self.items],
            "discount": self.discount.to_dict(),
            "total": self.total,
            "final_total": self.final_total,
        }

    @classmethod
    def from_dict(cls, data):
        """Fayldan o'qilgan lug'atdan sotuv yasaydi."""
        try:
            items = [SaleItem.from_dict(item) for item in data["items"]]
            discount_data = data.get("discount", {"kind": "none", "value": 0})
            discount = create_discount(discount_data["kind"], discount_data.get("value", 0))
            return cls(data["cashier"], data["id"], data["date"], items, discount)
        except (KeyError, TypeError, AttributeError, ValidationError) as error:
            raise StorageError(f"Fayldagi sotuv ma'lumoti noto'g'ri: {error}")

    def __str__(self):
        return f"Sotuv #{self.id}: {len(self.items)} qator, to'lov {self.final_total} so'm"
