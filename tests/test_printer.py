"""tests/test_printer.py - printer.py testlari (J ning ishi).

I ning klasslariga bog'liq emas: pastda oddiy "soxta" Sale va SaleItem
klasslari bor, ularda Umumiy TZ 7-bo'limdagi maydonlar bor.

Ishga tushirish (loyihaning asosiy papkasidan):
    python -m unittest discover -s tests
"""

import contextlib
import io
import unittest

from ui.printer import RECEIPT_WIDTH, format_money, print_receipt, print_table


class FakeItem:
    """Sotuv qatori (soxta)."""

    def __init__(self, name, qty, price):
        self.name = name
        self.qty = qty
        self.price = price
        self.subtotal = qty * price


class FakeSale:
    """Sotuv (soxta)."""

    def __init__(self, items, discount_text="", discount=0):
        self.id = 7
        self.date = "2026-11-05 14:30"
        self.cashier = "kassir"
        self.items = items
        self.total = sum(item.subtotal for item in items)
        self.discount_text = discount_text
        self.final_total = self.total - discount


def capture(function, *args, **kwargs):
    """Funksiya print qilgan matnni qaytaradi."""
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        function(*args, **kwargs)
    return buffer.getvalue()


class FormatMoneyTests(unittest.TestCase):
    def test_thousands_are_separated_by_spaces(self):
        self.assertEqual(format_money(15000), "15 000 so'm")
        self.assertEqual(format_money(1234567), "1 234 567 so'm")

    def test_small_numbers_and_zero(self):
        self.assertEqual(format_money(0), "0 so'm")
        self.assertEqual(format_money(500), "500 so'm")

    def test_float_is_rounded(self):
        self.assertEqual(format_money(2500.0), "2 500 so'm")
        self.assertEqual(format_money(2500.4), "2 500 so'm")


class PrintTableTests(unittest.TestCase):
    def test_all_lines_have_equal_length(self):
        text = capture(print_table, ["ID", "Nomi"], [[1, "Non"], [22, "Qaymoqli muzqaymoq"]])
        lengths = {len(line) for line in text.splitlines()}
        self.assertEqual(len(lengths), 1)

    def test_contains_headers_and_cells(self):
        text = capture(print_table, ["ID", "Nomi"], [[1, "Non"]])
        self.assertIn("ID", text)
        self.assertIn("Nomi", text)
        self.assertIn("Non", text)

    def test_right_align_puts_numbers_on_the_right(self):
        text = capture(print_table, ["Nomi", "Soni"], [["Non", 5], ["Sut", 120]],
                       right_align=(1,))
        self.assertIn("|    5 |", text)
        self.assertIn("|  120 |", text)

    def test_table_without_rows_does_not_crash(self):
        text = capture(print_table, ["ID", "Nomi"], [])
        self.assertIn("ID", text)

    def test_short_and_long_rows_are_fixed(self):
        text = capture(print_table, ["A", "B"], [["x"], ["1", "2", "3"]])
        lengths = {len(line) for line in text.splitlines()}
        self.assertEqual(len(lengths), 1)
        self.assertNotIn("3", text)


class PrintReceiptTests(unittest.TestCase):
    def test_receipt_with_discount(self):
        sale = FakeSale([FakeItem("Non", 2, 4000), FakeItem("Sut", 1, 12000)],
                        discount_text="10%", discount=2000)
        text = capture(print_receipt, sale)
        self.assertIn("2026-11-05 14:30", text)
        self.assertIn("kassir", text)
        self.assertIn("Non", text)
        self.assertIn("2 x 4 000 so'm", text)
        self.assertIn("Chegirma (10%):", text)
        self.assertIn("-2 000 so'm", text)
        self.assertIn("TO'LANADIGAN SUMMA:", text)
        self.assertIn("18 000 so'm", text)

    def test_receipt_without_discount(self):
        sale = FakeSale([FakeItem("Non", 1, 4000)])
        text = capture(print_receipt, sale)
        self.assertIn("Chegirma:", text)
        self.assertIn("yo'q", text)
        self.assertNotIn("Chegirma (", text)

    def test_receipt_lines_fit_the_width(self):
        sale = FakeSale([FakeItem("Non", 2, 4000)], discount_text="5000 so'm", discount=5000)
        text = capture(print_receipt, sale)
        for line in text.splitlines():
            self.assertLessEqual(len(line), RECEIPT_WIDTH)

    def test_receipt_with_long_product_name_does_not_crash(self):
        sale = FakeSale([FakeItem("Juda uzun nomli mahsulot " * 3, 1, 1000)])
        text = capture(print_receipt, sale)
        self.assertIn("Juda uzun nomli mahsulot", text)


if __name__ == "__main__":
    unittest.main()
