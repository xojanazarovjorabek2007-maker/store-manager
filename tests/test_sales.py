"""tests/test_sales.py - services/sales.py testlari (I ning ishi).

Testlar vaqtinchalik papkada ishlaydi, haqiqiy data/ ga tegmaydi.

Ishga tushirish (loyihaning asosiy papkasidan):
    python -m unittest discover -s tests
"""

import os
import tempfile
import unittest

from exceptions import OutOfStockError, ProductNotFoundError, ValidationError
from services.inventory import InventoryService
from services.sales import SalesService
from storage.json_storage import JsonStorage


class SalesServiceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.products_path = os.path.join(self.folder.name, "products.json")
        self.sales_path = os.path.join(self.folder.name, "sales.json")
        self.inventory, self.sales = self.new_services()
        self.bread = self.inventory.add_product("Non", 4000, 20)
        self.milk = self.inventory.add_product("Sut", 12000, 3)

    def new_services(self):
        """Xuddi dastur qayta ishga tushgandek, fayllardan yangi xizmatlar yasaydi."""
        inventory = InventoryService(JsonStorage(self.products_path))
        sales = SalesService(JsonStorage(self.sales_path), inventory)
        return inventory, sales

    def test_start_sale_is_empty_and_not_saved(self):
        sale = self.sales.start_sale("kassir")
        self.assertEqual(sale.cashier, "kassir")
        self.assertEqual(sale.items, [])
        self.assertEqual(self.sales.all_sales(), [])

    def test_add_item_uses_current_product_price(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 2)
        item = sale.items[0]
        self.assertEqual((item.name, item.qty, item.price, item.subtotal),
                         ("Non", 2, 4000, 8000))
        self.assertEqual(sale.total, 8000)

    def test_adding_does_not_change_stock_before_finish(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 5)
        self.assertEqual(self.bread.stock, 20)

    def test_same_product_twice_is_merged(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 2)
        self.sales.add_item(sale, self.bread.pid, 3)
        self.assertEqual(len(sale.items), 1)
        self.assertEqual(sale.items[0].qty, 5)

    def test_cannot_add_more_than_in_stock(self):
        sale = self.sales.start_sale("kassir")
        with self.assertRaises(OutOfStockError) as context:
            self.sales.add_item(sale, self.milk.pid, 5)
        self.assertIn("qoldiq: 3", str(context.exception))
        self.assertEqual(sale.items, [])

    def test_cart_quantity_is_counted_against_stock(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.milk.pid, 2)
        with self.assertRaises(OutOfStockError) as context:
            self.sales.add_item(sale, self.milk.pid, 2)
        self.assertEqual(context.exception.available, 1)
        self.sales.add_item(sale, self.milk.pid, 1)  # oxirgi bittasi mumkin
        self.assertEqual(sale.quantity_of(self.milk.pid), 3)

    def test_unknown_product_raises_not_found(self):
        sale = self.sales.start_sale("kassir")
        with self.assertRaises(ProductNotFoundError):
            self.sales.add_item(sale, 99, 1)

    def test_invalid_quantity_is_rejected(self):
        sale = self.sales.start_sale("kassir")
        for bad in (0, -1, 1.5, "2", True):
            with self.assertRaises(ValidationError):
                self.sales.add_item(sale, self.bread.pid, bad)

    def test_percent_discount(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 5)  # 20000
        self.sales.apply_discount(sale, "percent", 10)
        self.assertEqual(sale.discount_text, "10%")
        self.assertEqual(sale.total, 20000)
        self.assertEqual(sale.final_total, 18000)

    def test_fixed_discount(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 5)
        self.sales.apply_discount(sale, "fixed", 5000)
        self.assertEqual(sale.discount_text, "5000 so'm")
        self.assertEqual(sale.final_total, 15000)

    def test_discount_can_be_replaced(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 5)
        self.sales.apply_discount(sale, "percent", 50)
        self.sales.apply_discount(sale, "fixed", 1000)
        self.assertEqual(sale.final_total, 19000)

    def test_invalid_discounts_are_rejected_and_change_nothing(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 1)  # 4000
        for kind, value in (("percent", 0), ("percent", 101), ("fixed", 4001),
                            ("fixed", 0), ("bonus", 10)):
            with self.assertRaises(ValidationError):
                self.sales.apply_discount(sale, kind, value)
        self.assertEqual(sale.final_total, 4000)

    def test_discount_on_empty_cart_is_rejected(self):
        sale = self.sales.start_sale("kassir")
        with self.assertRaises(ValidationError):
            self.sales.apply_discount(sale, "percent", 10)

    def test_finish_sale_reduces_stock_and_saves(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 2)
        self.sales.add_item(sale, self.milk.pid, 1)
        finished = self.sales.finish_sale(sale)
        self.assertIs(finished, sale)
        self.assertEqual(self.bread.stock, 18)
        self.assertEqual(self.milk.stock, 2)
        self.assertEqual(len(self.sales.all_sales()), 1)

    def test_finish_sale_sets_id_and_date(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 1)
        self.sales.finish_sale(sale)
        self.assertEqual(sale.id, 1)
        self.assertRegex(sale.date, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")

    def test_sale_ids_increase(self):
        ids = []
        for _ in range(3):
            sale = self.sales.start_sale("kassir")
            self.sales.add_item(sale, self.bread.pid, 1)
            ids.append(self.sales.finish_sale(sale).id)
        self.assertEqual(ids, [1, 2, 3])

    def test_data_survives_restart(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 2)
        self.sales.add_item(sale, self.milk.pid, 1)
        self.sales.apply_discount(sale, "percent", 10)
        self.sales.finish_sale(sale)

        inventory, sales = self.new_services()
        self.assertEqual(inventory.get_product(self.bread.pid).stock, 18)
        saved = sales.all_sales()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0].cashier, "kassir")
        self.assertEqual(saved[0].total, 20000)
        self.assertEqual(saved[0].discount_text, "10%")
        self.assertEqual(saved[0].final_total, 18000)
        self.assertEqual([item.name for item in saved[0].items], ["Non", "Sut"])
        self.assertRegex(saved[0].date, r"^\d{4}-\d{2}-\d{2} ")

    def test_empty_cart_cannot_be_finished(self):
        sale = self.sales.start_sale("kassir")
        with self.assertRaises(ValidationError):
            self.sales.finish_sale(sale)
        self.assertEqual(self.sales.all_sales(), [])

    def test_sale_cannot_be_finished_twice(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 1)
        self.sales.finish_sale(sale)
        with self.assertRaises(ValidationError):
            self.sales.finish_sale(sale)
        self.assertEqual(self.bread.stock, 19)
        self.assertEqual(len(self.sales.all_sales()), 1)

    def test_finished_sale_cannot_be_changed(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 1)
        self.sales.finish_sale(sale)
        with self.assertRaises(ValidationError):
            self.sales.add_item(sale, self.bread.pid, 1)
        with self.assertRaises(ValidationError):
            self.sales.apply_discount(sale, "percent", 10)

    def test_finish_fails_if_stock_dropped_in_the_meantime(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 2)
        self.sales.add_item(sale, self.milk.pid, 3)
        self.inventory.update_product(self.milk.pid, stock=1)  # savat ochiq paytida kamaydi
        with self.assertRaises(OutOfStockError):
            self.sales.finish_sale(sale)
        self.assertEqual(self.bread.stock, 20)  # hech narsa o'zgarmagan
        self.assertEqual(self.milk.stock, 1)
        self.assertEqual(self.sales.all_sales(), [])
        self.assertIsNone(sale.id)

    def test_all_sales_returns_a_copy(self):
        sale = self.sales.start_sale("kassir")
        self.sales.add_item(sale, self.bread.pid, 1)
        self.sales.finish_sale(sale)
        self.sales.all_sales().clear()
        self.assertEqual(len(self.sales.all_sales()), 1)


if __name__ == "__main__":
    unittest.main()
