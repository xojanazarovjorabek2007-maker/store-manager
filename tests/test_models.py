"""tests/test_models.py - models/ papkasi testlari (I ning ishi).

Ishga tushirish (loyihaning asosiy papkasidan):
    python -m unittest discover -s tests
"""

import unittest

from exceptions import OutOfStockError, PermissionDeniedError, StorageError, ValidationError
from models.discount import (Discount, FixedDiscount, NoDiscount, PercentDiscount,
                             create_discount)
from models.product import Product
from models.sale import Sale, SaleItem
from models.user import Admin, Cashier, User, user_from_dict


class ProductTests(unittest.TestCase):
    def test_create_product(self):
        product = Product(1, "Non", 4000, 20)
        self.assertEqual(product.pid, 1)
        self.assertEqual(product.name, "Non")
        self.assertEqual(product.price, 4000)
        self.assertEqual(product.stock, 20)

    def test_price_must_be_positive(self):
        with self.assertRaises(ValidationError):
            Product(1, "Non", 0, 5)
        with self.assertRaises(ValidationError):
            Product(1, "Non", -100, 5)

    def test_price_setter_validates(self):
        product = Product(1, "Non", 4000, 5)
        with self.assertRaises(ValidationError):
            product.price = -1
        self.assertEqual(product.price, 4000)
        product.price = 4500
        self.assertEqual(product.price, 4500)

    def test_price_and_stock_must_be_whole_numbers(self):
        with self.assertRaises(ValidationError):
            Product(1, "Non", 12.5, 5)
        with self.assertRaises(ValidationError):
            Product(1, "Non", 4000, 2.5)
        with self.assertRaises(ValidationError):
            Product(1, "Non", True, 5)

    def test_stock_cannot_be_negative_but_can_be_zero(self):
        with self.assertRaises(ValidationError):
            Product(1, "Non", 4000, -1)
        self.assertEqual(Product(1, "Non", 4000, 0).stock, 0)

    def test_name_cannot_be_blank_and_is_trimmed(self):
        with self.assertRaises(ValidationError):
            Product(1, "", 4000, 5)
        with self.assertRaises(ValidationError):
            Product(1, "   ", 4000, 5)
        self.assertEqual(Product(1, "  Non  ", 4000, 5).name, "Non")

    def test_reduce_stock(self):
        product = Product(1, "Non", 4000, 10)
        product.reduce_stock(4)
        self.assertEqual(product.stock, 6)

    def test_reduce_stock_too_much_raises_out_of_stock(self):
        product = Product(1, "Sut", 12000, 3)
        with self.assertRaises(OutOfStockError) as context:
            product.reduce_stock(5)
        self.assertEqual(context.exception.available, 3)
        self.assertIn("qoldiq: 3", str(context.exception))
        self.assertEqual(product.stock, 3)

    def test_reduce_stock_rejects_zero_and_negative(self):
        product = Product(1, "Non", 4000, 10)
        with self.assertRaises(ValidationError):
            product.reduce_stock(0)
        with self.assertRaises(ValidationError):
            product.reduce_stock(-2)

    def test_str(self):
        text = str(Product(1, "Non", 4000, 20))
        self.assertIn("Non", text)
        self.assertIn("4000", text)

    def test_to_dict_and_from_dict(self):
        product = Product(7, "Olma", 3500, 50)
        copy = Product.from_dict(product.to_dict())
        self.assertEqual(copy.to_dict(), product.to_dict())

    def test_from_dict_with_missing_field_raises_storage_error(self):
        with self.assertRaises(StorageError):
            Product.from_dict({"pid": 1, "name": "Non", "price": 4000})

    def test_from_dict_with_invalid_value_raises_storage_error(self):
        with self.assertRaises(StorageError):
            Product.from_dict({"pid": 1, "name": "Non", "price": -5, "stock": 1})


class UserTests(unittest.TestCase):
    def test_user_is_abstract(self):
        with self.assertRaises(TypeError):
            User("a", "b")

    def test_admin_has_all_permissions(self):
        admin = Admin("admin", "1234")
        for permission in ("manage_products", "sell", "view_stock", "view_reports",
                           "manage_users"):
            self.assertTrue(admin.can(permission))

    def test_cashier_can_only_sell_and_view_stock(self):
        cashier = Cashier("kassir", "0000")
        self.assertTrue(cashier.can("sell"))
        self.assertTrue(cashier.can("view_stock"))
        self.assertFalse(cashier.can("manage_products"))
        self.assertFalse(cashier.can("view_reports"))
        self.assertFalse(cashier.can("manage_users"))

    def test_roles(self):
        self.assertEqual(Admin("a", "b").role, "Admin")
        self.assertEqual(Cashier("a", "b").role, "Kassir")

    def test_require_raises_permission_denied(self):
        cashier = Cashier("kassir", "0000")
        cashier.require("sell")
        with self.assertRaises(PermissionDeniedError):
            cashier.require("manage_products")

    def test_check_password(self):
        user = Admin("admin", "1234")
        self.assertTrue(user.check_password("1234"))
        self.assertFalse(user.check_password("0000"))

    def test_to_dict_and_user_from_dict_keep_the_class(self):
        for user in (Admin("admin", "1234"), Cashier("kassir", "0000")):
            copy = user_from_dict(user.to_dict())
            self.assertIs(type(copy), type(user))
            self.assertEqual(copy.username, user.username)
            self.assertTrue(copy.check_password(user._password))

    def test_user_from_dict_with_unknown_role_raises_storage_error(self):
        with self.assertRaises(StorageError):
            user_from_dict({"username": "x", "password": "y", "role": "Direktor"})

    def test_str(self):
        self.assertEqual(str(Admin("admin", "1234")), "admin (Admin)")


class DiscountTests(unittest.TestCase):
    def test_discount_is_abstract(self):
        with self.assertRaises(TypeError):
            Discount()

    def test_no_discount(self):
        discount = NoDiscount()
        self.assertEqual(discount.apply(20000), 20000)
        self.assertEqual(discount.text, "")

    def test_percent_discount(self):
        discount = PercentDiscount(10)
        self.assertEqual(discount.apply(20000), 18000)
        self.assertEqual(discount.text, "10%")

    def test_percent_discount_rounds_to_whole_som(self):
        # 12345 ning 10% i = 1234.5 -> 1235 so'm chegirma
        self.assertEqual(PercentDiscount(10).apply(12345), 11110)

    def test_percent_100_makes_it_free(self):
        self.assertEqual(PercentDiscount(100).apply(5000), 0)

    def test_percent_out_of_range_raises(self):
        for bad in (0, 101, -5, 10.5, "10", True):
            with self.assertRaises(ValidationError):
                PercentDiscount(bad)

    def test_fixed_discount(self):
        discount = FixedDiscount(5000)
        self.assertEqual(discount.apply(20000), 15000)
        self.assertEqual(discount.text, "5000 so'm")

    def test_fixed_discount_check(self):
        FixedDiscount(5000).check(5000)  # teng bo'lsa mumkin
        with self.assertRaises(ValidationError):
            FixedDiscount(5001).check(5000)

    def test_fixed_discount_apply_never_goes_below_zero(self):
        self.assertEqual(FixedDiscount(9000).apply(5000), 0)

    def test_fixed_out_of_range_raises(self):
        for bad in (0, -1, 2.5, "100"):
            with self.assertRaises(ValidationError):
                FixedDiscount(bad)

    def test_create_discount(self):
        self.assertIsInstance(create_discount("none"), NoDiscount)
        self.assertIsInstance(create_discount("percent", 10), PercentDiscount)
        self.assertIsInstance(create_discount("fixed", 500), FixedDiscount)

    def test_create_discount_with_unknown_kind_raises(self):
        with self.assertRaises(ValidationError):
            create_discount("bonus", 10)

    def test_to_dict(self):
        self.assertEqual(PercentDiscount(15).to_dict(), {"kind": "percent", "value": 15})
        self.assertEqual(NoDiscount().to_dict(), {"kind": "none", "value": 0})


class SaleTests(unittest.TestCase):
    def make_sale(self):
        sale = Sale("kassir")
        sale.add_item(1, "Non", 2, 4000)
        sale.add_item(2, "Sut", 1, 12000)
        return sale

    def test_item_subtotal(self):
        self.assertEqual(SaleItem(1, "Non", 3, 4000).subtotal, 12000)

    def test_new_sale_is_empty_and_not_finished(self):
        sale = Sale("kassir")
        self.assertIsNone(sale.id)
        self.assertIsNone(sale.date)
        self.assertEqual(sale.items, [])
        self.assertEqual(sale.total, 0)
        self.assertEqual(sale.discount_text, "")

    def test_total_without_discount(self):
        sale = self.make_sale()
        self.assertEqual(sale.total, 20000)
        self.assertEqual(sale.final_total, 20000)

    def test_total_with_discount(self):
        sale = self.make_sale()
        sale.discount = PercentDiscount(10)
        self.assertEqual(sale.total, 20000)
        self.assertEqual(sale.discount_text, "10%")
        self.assertEqual(sale.final_total, 18000)

    def test_same_product_is_merged_into_one_line(self):
        sale = Sale("kassir")
        sale.add_item(1, "Non", 2, 4000)
        sale.add_item(1, "Non", 3, 4000)
        self.assertEqual(len(sale.items), 1)
        self.assertEqual(sale.items[0].qty, 5)

    def test_quantity_of(self):
        sale = self.make_sale()
        self.assertEqual(sale.quantity_of(1), 2)
        self.assertEqual(sale.quantity_of(99), 0)

    def test_to_dict_and_from_dict(self):
        sale = self.make_sale()
        sale.id = 3
        sale.date = "2026-11-05 14:30"
        sale.discount = FixedDiscount(5000)
        copy = Sale.from_dict(sale.to_dict())
        self.assertEqual(copy.id, 3)
        self.assertEqual(copy.date, "2026-11-05 14:30")
        self.assertEqual(copy.cashier, "kassir")
        self.assertEqual(len(copy.items), 2)
        self.assertEqual(copy.total, 20000)
        self.assertEqual(copy.discount_text, "5000 so'm")
        self.assertEqual(copy.final_total, 15000)

    def test_from_dict_with_broken_data_raises_storage_error(self):
        with self.assertRaises(StorageError):
            Sale.from_dict({"id": 1})
        with self.assertRaises(StorageError):
            Sale.from_dict({"id": 1, "date": "x", "cashier": "k", "items": [{"pid": 1}]})


if __name__ == "__main__":
    unittest.main()
