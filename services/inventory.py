"""services/inventory.py - mahsulotlar va ombor qoidalari (I ning ishi).

Bu yerda print va input ishlatilmaydi: natija qaytariladi yoki xato
(AppError) ko'tariladi. Har bir o'zgarishdan keyin ma'lumot faylga saqlanadi.
"""

from exceptions import ProductNotFoundError, ValidationError
from models.product import Product, check_price, check_stock

DEFAULT_LOW_STOCK_LIMIT = 5


def _by_stock_then_id(product):
    """Saralash kaliti: avval soni kam, teng bo'lsa ID kichigi."""
    return (product.stock, product.pid)


class InventoryService:
    """Mahsulotlarni qo'shish, o'zgartirish, o'chirish va ombor qoldig'i."""

    def __init__(self, storage):
        self.storage = storage
        self._products = [Product.from_dict(item) for item in storage.load()]

    def save(self):
        """Mahsulotlarni faylga yozadi (sotuv ombor sonini o'zgartirganda ham chaqiriladi)."""
        self.storage.save([product.to_dict() for product in self._products])

    def all_products(self):
        """Hamma mahsulotlar ro'yxati (nusxa)."""
        return list(self._products)

    def get_product(self, pid):
        """ID bo'yicha mahsulotni topadi, topilmasa ProductNotFoundError."""
        for product in self._products:
            if product.pid == pid:
                return product
        raise ProductNotFoundError(pid)

    def add_product(self, name, price, stock):
        """Yangi mahsulot qo'shadi va uni qaytaradi."""
        product = Product(self._next_pid(), name, price, stock)  # qiymatlarni tekshiradi
        if self._name_exists(product.name):
            raise ValidationError(f"'{product.name}' nomli mahsulot allaqachon bor")
        self._products.append(product)
        self.save()
        return product

    def update_product(self, pid, price=None, stock=None):
        """Narx yoki sonini o'zgartiradi (berilmaganiga tegmaydi)."""
        product = self.get_product(pid)
        if price is None and stock is None:
            raise ValidationError("Yangi narx yoki sonini kiriting")
        # Avval ikkalasini tekshiramiz, keyin o'zgartiramiz: biri xato bo'lsa, hech narsa o'zgarmaydi
        new_price = product.price if price is None else check_price(price)
        new_stock = product.stock if stock is None else check_stock(stock)
        product.price = new_price
        product.stock = new_stock
        self.save()
        return product

    def delete_product(self, pid):
        """Mahsulotni o'chiradi."""
        product = self.get_product(pid)
        self._products.remove(product)
        self.save()

    def low_stock(self, limit=DEFAULT_LOW_STOCK_LIMIT):
        """Soni limit va undan kam qolgan mahsulotlar (eng kami birinchi)."""
        low = [product for product in self._products if product.stock <= limit]
        low.sort(key=_by_stock_then_id)
        return low

    def _next_pid(self):
        if not self._products:
            return 1
        return max(product.pid for product in self._products) + 1

    def _name_exists(self, name):
        for product in self._products:
            if product.name.lower() == name.lower():
                return True
        return False
