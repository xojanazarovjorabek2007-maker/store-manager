"""tests/test_auth.py - services/auth.py testlari (I ning ishi).

Testlar vaqtinchalik papkada ishlaydi, haqiqiy data/ ga tegmaydi.

Ishga tushirish (loyihaning asosiy papkasidan):
    python -m unittest discover -s tests
"""

import os
import tempfile
import unittest

from exceptions import AuthError, StorageError, ValidationError
from services.auth import AuthService
from storage.json_storage import JsonStorage


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = os.path.join(self.folder.name, "users.json")

    def new_service(self):
        """Xuddi dastur qayta ishga tushgandek, fayldan yangi xizmat yasaydi."""
        return AuthService(JsonStorage(self.path))

    def test_default_accounts_are_created_on_first_run(self):
        auth = self.new_service()
        admin = auth.login("admin", "1234")
        cashier = auth.login("kassir", "0000")
        self.assertEqual(admin.role, "Admin")
        self.assertEqual(cashier.role, "Kassir")

    def test_default_accounts_are_saved_to_file(self):
        self.new_service()
        self.assertTrue(os.path.exists(self.path))
        self.assertEqual(self.new_service().login("admin", "1234").username, "admin")

    def test_login_returns_user_with_permissions(self):
        auth = self.new_service()
        self.assertTrue(auth.login("admin", "1234").can("manage_users"))
        self.assertFalse(auth.login("kassir", "0000").can("manage_users"))

    def test_wrong_password_raises_auth_error(self):
        auth = self.new_service()
        with self.assertRaises(AuthError) as context:
            auth.login("admin", "xato")
        self.assertIn("xato", str(context.exception))

    def test_unknown_login_raises_auth_error(self):
        with self.assertRaises(AuthError):
            self.new_service().login("yoq_odam", "1234")

    def test_add_cashier(self):
        auth = self.new_service()
        auth.add_cashier("ali", "parol1")
        user = auth.login("ali", "parol1")
        self.assertEqual(user.role, "Kassir")
        self.assertTrue(user.can("sell"))
        self.assertFalse(user.can("manage_products"))

    def test_added_cashier_survives_restart(self):
        self.new_service().add_cashier("ali", "parol1")
        self.assertEqual(self.new_service().login("ali", "parol1").username, "ali")

    def test_add_cashier_trims_spaces(self):
        auth = self.new_service()
        auth.add_cashier("  vali  ", "  1111  ")
        self.assertEqual(auth.login("vali", "1111").username, "vali")

    def test_duplicate_login_is_rejected_case_insensitive(self):
        auth = self.new_service()
        with self.assertRaises(ValidationError):
            auth.add_cashier("kassir", "9999")
        with self.assertRaises(ValidationError):
            auth.add_cashier("ADMIN", "9999")

    def test_blank_login_or_password_is_rejected(self):
        auth = self.new_service()
        for username, password in (("", "1"), ("   ", "1"), ("ali", ""), ("ali", "  ")):
            with self.assertRaises(ValidationError):
                auth.add_cashier(username, password)

    def test_broken_users_file_raises_storage_error(self):
        with open(self.path, "w", encoding="utf-8") as file:
            file.write('[{"username": "x"}]')
        with self.assertRaises(StorageError):
            self.new_service()


if __name__ == "__main__":
    unittest.main()
