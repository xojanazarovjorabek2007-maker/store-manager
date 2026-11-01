"""tests/test_reports.py - SalesReport testlari (J ning ishi).

I ning klasslariga bog'liq emas: pastda oddiy "soxta" Sale va SaleItem
klasslari bor, ularda Umumiy TZ 7-bo'limdagi maydonlar bor.

Ishga tushirish (loyihaning asosiy papkasidan):
    python -m unittest discover -s tests
"""

import datetime
import unittest

from reports.sales_report import SalesReport


class FakeItem:
    """Sotuv qatori (soxta)."""

    def __init__(self, name, qty, price):
        self.name = name
        self.qty = qty
        self.price = price
        self.subtotal = qty * price


class FakeSale:
    """Sotuv (soxta)."""

    def __init__(self, date, items, discount=0):
        self.date = date
        self.items = items
        self.total = sum(item.subtotal for item in items)
        self.final_total = self.total - discount


def make_sales():
    """Uch kunlik namunaviy sotuvlar."""
    return [
        FakeSale("2026-11-05 10:15", [FakeItem("Non", 2, 4000), FakeItem("Sut", 1, 12000)]),
        FakeSale("2026-11-05 15:40", [FakeItem("Non", 3, 4000)], discount=1200),
        FakeSale("2026-11-06 09:00", [FakeItem("Olma", 5, 3500), FakeItem("Sut", 2, 12000)]),
    ]


class DailySummaryTests(unittest.TestCase):
    def test_counts_sales_of_the_day(self):
        summary = SalesReport(make_sales()).daily_summary("2026-11-05")
        self.assertEqual(summary["count"], 2)

    def test_total_uses_final_total_after_discount(self):
        # 1-sotuv: 20000, 2-sotuv: 12000 - 1200 = 10800
        summary = SalesReport(make_sales()).daily_summary("2026-11-05")
        self.assertEqual(summary["total"], 30800)

    def test_day_without_sales_is_zero(self):
        summary = SalesReport(make_sales()).daily_summary("2026-12-01")
        self.assertEqual(summary["count"], 0)
        self.assertEqual(summary["total"], 0)

    def test_other_day_is_not_mixed_in(self):
        summary = SalesReport(make_sales()).daily_summary("2026-11-06")
        self.assertEqual(summary["count"], 1)
        self.assertEqual(summary["total"], 41500)

    def test_accepts_date_object(self):
        summary = SalesReport(make_sales()).daily_summary(datetime.date(2026, 11, 5))
        self.assertEqual(summary["date"], "2026-11-05")
        self.assertEqual(summary["count"], 2)

    def test_empty_sales_list(self):
        summary = SalesReport([]).daily_summary("2026-11-05")
        self.assertEqual(summary, {"date": "2026-11-05", "count": 0, "total": 0})


class TopProductsTests(unittest.TestCase):
    def test_quantities_are_added_up_across_sales(self):
        top = SalesReport(make_sales()).top_products()
        # Non: 2 + 3 = 5, Olma: 5, Sut: 1 + 2 = 3
        self.assertIn(("Sut", 3), top)
        self.assertIn(("Non", 5), top)

    def test_sorted_by_quantity_then_name(self):
        top = SalesReport(make_sales()).top_products()
        self.assertEqual(top, [("Non", 5), ("Olma", 5), ("Sut", 3)])

    def test_limit_n(self):
        top = SalesReport(make_sales()).top_products(2)
        self.assertEqual(top, [("Non", 5), ("Olma", 5)])

    def test_empty_sales_list(self):
        self.assertEqual(SalesReport([]).top_products(), [])

    def test_zero_or_negative_n_gives_empty_list(self):
        report = SalesReport(make_sales())
        self.assertEqual(report.top_products(0), [])
        self.assertEqual(report.top_products(-3), [])


if __name__ == "__main__":
    unittest.main()
