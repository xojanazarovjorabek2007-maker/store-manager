"""services/sales.py - sotuv jarayoni (I ning ishi).

Tartib: start_sale -> add_item (ko'p marta) -> apply_discount (ixtiyoriy)
-> finish_sale. Sotuv yakunlangandagina ombor kamayadi va fayl yoziladi.

Bu yerda print va input ishlatilmaydi: natija qaytariladi yoki xato
(AppError) ko'tariladi.
"""

import datetime

from exceptions import OutOfStockError, ValidationError
from models.discount import create_discount
from models.product import is_whole_number
from models.sale import Sale

DATE_FORMAT = "%Y-%m-%d %H:%M"


class SalesService:
    """Sotuv qilish va o'tgan sotuvlarni saqlash."""

    def __init__(self, storage, inventory):
        self.storage = storage
        self.inventory = inventory
        self._sales = [Sale.from_dict(item) for item in storage.load()]

    def start_sale(self, cashier_name):
        """Yangi bo'sh sotuv ochadi (hali hech narsa saqlanmaydi)."""
        return Sale(cashier_name)

    def add_item(self, sale, pid, qty):
        """Sotuvga mahsulot qo'shadi. Omborda yetarli bo'lmasa OutOfStockError."""
        self._check_not_finished(sale)
        if not is_whole_number(qty) or qty <= 0:
            raise ValidationError("Soni 0 dan katta butun son bo'lishi kerak")
        product = self.inventory.get_product(pid)
        available = product.stock - sale.quantity_of(product.pid)  # savatdagisini hisobga olamiz
        if qty > available:
            raise OutOfStockError(product.name, available)
        sale.add_item(product.pid, product.name, qty, product.price)

    def apply_discount(self, sale, kind, value):
        """Chegirma qo'yadi. kind: 'percent' (foiz) yoki 'fixed' (aniq summa)."""
        self._check_not_finished(sale)
        if not sale.items:
            raise ValidationError("Avval savatga mahsulot qo'shing")
        discount = create_discount(kind, value)
        discount.check(sale.total)
        sale.discount = discount

    def finish_sale(self, sale):
        """Sotuvni yakunlaydi: ombor kamayadi, sotuv saqlanadi. Yakunlangan sotuvni qaytaradi."""
        self._check_not_finished(sale)
        if not sale.items:
            raise ValidationError("Bo'sh savat bilan sotuvni tugatib bo'lmaydi")

        # Har bir mahsulotdan jami nechta kerak
        needed = {}
        for item in sale.items:
            needed[item.pid] = needed.get(item.pid, 0) + item.qty

        # Avval hammasini tekshiramiz, keyin kamaytiramiz: xato bo'lsa, hech narsa o'zgarmaydi
        to_reduce = []
        for pid, qty in needed.items():
            product = self.inventory.get_product(pid)
            if qty > product.stock:
                raise OutOfStockError(product.name, product.stock)
            to_reduce.append((product, qty))
        for product, qty in to_reduce:
            product.reduce_stock(qty)

        sale.id = self._next_id()
        sale.date = datetime.datetime.now().strftime(DATE_FORMAT)
        self._sales.append(sale)
        self.inventory.save()
        self._save()
        return sale

    def all_sales(self):
        """Barcha o'tgan sotuvlar ro'yxati (nusxa)."""
        return list(self._sales)

    def _save(self):
        self.storage.save([sale.to_dict() for sale in self._sales])

    def _next_id(self):
        if not self._sales:
            return 1
        return max(sale.id for sale in self._sales) + 1

    def _check_not_finished(self, sale):
        if sale.id is not None:
            raise ValidationError("Bu sotuv allaqachon yakunlangan")
