"""tests/test_inventory.py - services/inventory.py testlari (I ning ishi).

Testlar vaqtinchalik papkada ishlaydi, haqiqiy data/ ga tegmaydi.

Ishga tushirish (loyihaning asosiy papkasidan):
    python -m unittest discover -s tests
"""

import os
import tempfile
import unittest

from exceptions import ProductNotFoundError, StorageError, ValidationError
from services.inventory import InventoryService
from storage.json_storage import JsonStorage


class InventoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "products.json")
        self.inventory = self.new_service()

    def new_service(self):
        """Xuddi dastur qayta ishga tushgandek, fayldan yangi xizmat yasaydi."""
        return InventoryService(JsonStorage(self.path))

    def test_starts_empty(self):
        self.assertEqual(self.inventory.all_products(), [])

    def test_add_product_gives_increasing_ids(self):
        first = self.inventory.add_product("Non", 4000, 20)
        second = self.inventory.add_product("Sut", 12000, 3)
        self.assertEqual(first.pid, 1)
        self.assertEqual(second.pid, 2)
        self.assertEqual(len(self.inventory.all_products()), 2)

    def test_add_product_returns_product_with_given_values(self):
        product = self.inventory.add_product("  Non  ", 4000, 20)
        self.assertEqual((product.name, product.price, product.stock), ("Non", 4000, 20))

    def test_products_survive_restart(self):
        self.inventory.add_product("Non", 4000, 20)
        again = self.new_service().all_products()
        self.assertEqual(len(again), 1)
        self.assertEqual(again[0].name, "Non")
        self.assertEqual(again[0].stock, 20)

    def test_invalid_values_are_rejected(self):
        for name, price, stock in (("", 4000, 1), ("Non", 0, 1), ("Non", -5, 1),
                                   ("Non", 4000, -1), ("Non", 12.5, 1), ("Non", 4000, "5")):
            with self.assertRaises(ValidationError):
                self.inventory.add_product(name, price, stock)
        self.assertEqual(self.inventory.all_products(), [])

    def test_zero_stock_is_allowed(self):
        self.assertEqual(self.inventory.add_product("Non", 4000, 0).stock, 0)

    def test_duplicate_name_is_rejected_case_insensitive(self):
        self.inventory.add_product("Non", 4000, 20)
        with self.assertRaises(ValidationError):
            self.inventory.add_product("non", 5000, 1)
        self.assertEqual(len(self.inventory.all_products()), 1)

    def test_get_product(self):
        product = self.inventory.add_product("Non", 4000, 20)
        self.assertIs(self.inventory.get_product(product.pid), product)

    def test_unknown_id_raises_not_found(self):
        with self.assertRaises(ProductNotFoundError) as context:
            self.inventory.get_product(99)
        self.assertIn("Mahsulot topilmadi", str(context.exception))

    def test_update_price_only(self):
        product = self.inventory.add_product("Non", 4000, 20)
        self.inventory.update_product(product.pid, price=4500)
        self.assertEqual((product.price, product.stock), (4500, 20))

    def test_update_stock_only(self):
        product = self.inventory.add_product("Non", 4000, 20)
        self.inventory.update_product(product.pid, stock=7)
        self.assertEqual((product.price, product.stock), (4000, 7))

    def test_update_is_saved(self):
        product = self.inventory.add_product("Non", 4000, 20)
        self.inventory.update_product(product.pid, price=4500, stock=0)
        again = self.new_service().get_product(product.pid)
        self.assertEqual((again.price, again.stock), (4500, 0))

    def test_update_changes_nothing_if_one_value_is_invalid(self):
        product = self.inventory.add_product("Non", 4000, 20)
        with self.assertRaises(ValidationError):
            self.inventory.update_product(product.pid, price=5000, stock=-3)
        self.assertEqual((product.price, product.stock), (4000, 20))

    def test_update_without_values_is_rejected(self):
        product = self.inventory.add_product("Non", 4000, 20)
        with self.assertRaises(ValidationError):
            self.inventory.update_product(product.pid)

    def test_update_unknown_id_raises_not_found(self):
        with self.assertRaises(ProductNotFoundError):
            self.inventory.update_product(99, price=1000)

    def test_delete_product(self):
        product = self.inventory.add_product("Non", 4000, 20)
        self.inventory.add_product("Sut", 12000, 3)
        self.inventory.delete_product(product.pid)
        self.assertEqual([p.name for p in self.inventory.all_products()], ["Sut"])
        self.assertEqual([p.name for p in self.new_service().all_products()], ["Sut"])

    def test_delete_unknown_id_raises_not_found(self):
        with self.assertRaises(ProductNotFoundError):
            self.inventory.delete_product(99)

    def test_low_stock_includes_the_limit_and_is_sorted(self):
        self.inventory.add_product("Non", 4000, 20)
        self.inventory.add_product("Sut", 12000, 5)
        self.inventory.add_product("Tuxum", 1500, 2)
        self.inventory.add_product("Yog'", 30000, 0)
        names = [product.name for product in self.inventory.low_stock()]
        self.assertEqual(names, ["Yog'", "Tuxum", "Sut"])

    def test_low_stock_with_custom_limit(self):
        self.inventory.add_product("Non", 4000, 20)
        self.inventory.add_product("Sut", 12000, 5)
        self.assertEqual([p.name for p in self.inventory.low_stock(20)], ["Sut", "Non"])
        self.assertEqual(self.inventory.low_stock(1), [])

    def test_all_products_returns_a_copy(self):
        self.inventory.add_product("Non", 4000, 20)
        self.inventory.all_products().clear()
        self.assertEqual(len(self.inventory.all_products()), 1)

    def test_broken_products_file_raises_storage_error(self):
        with open(self.path, "w", encoding="utf-8") as file:
            file.write('[{"pid": 1, "name": "Non", "price": -4000, "stock": 1}]')
        with self.assertRaises(StorageError):
            self.new_service()


if __name__ == "__main__":
    unittest.main()
