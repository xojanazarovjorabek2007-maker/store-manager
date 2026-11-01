"""tests/test_storage.py - storage/json_storage.py testlari (I ning ishi).

Testlar vaqtinchalik papkada ishlaydi, haqiqiy data/ ga tegmaydi.

Ishga tushirish (loyihaning asosiy papkasidan):
    python -m unittest discover -s tests
"""

import json
import os
import tempfile
import unittest

from exceptions import AppError, StorageError
from storage.json_storage import JsonStorage


class JsonStorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        # "data" papkasi hali mavjud emas: save() uni o'zi yaratishi kerak
        self.path = os.path.join(self.folder.name, "data", "items.json")
        self.storage = JsonStorage(self.path)

    def write_raw(self, text, encoding="utf-8"):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding=encoding) as file:
            file.write(text)

    def test_missing_file_gives_empty_list(self):
        self.assertEqual(self.storage.load(), [])

    def test_save_creates_folder_and_file(self):
        self.storage.save([{"a": 1}])
        self.assertTrue(os.path.exists(self.path))

    def test_save_then_load_returns_same_data(self):
        data = [{"name": "Non", "price": 4000}, {"name": "Sut", "price": 12000}]
        self.storage.save(data)
        self.assertEqual(self.storage.load(), data)

    def test_save_overwrites_old_data(self):
        self.storage.save([{"a": 1}, {"a": 2}])
        self.storage.save([{"a": 3}])
        self.assertEqual(self.storage.load(), [{"a": 3}])

    def test_non_ascii_text_is_kept_readable(self):
        data = [{"name": "O\u02bbrik"}]
        self.storage.save(data)
        self.assertEqual(self.storage.load(), data)
        with open(self.path, encoding="utf-8") as file:
            self.assertIn("O\u02bbrik", file.read())  # \u02bb belgisi faylda o'zi yozilgan

    def test_saved_file_is_valid_json(self):
        self.storage.save([{"a": 1}])
        with open(self.path, encoding="utf-8") as file:
            self.assertEqual(json.load(file), [{"a": 1}])

    def test_no_temp_file_is_left_behind(self):
        self.storage.save([{"a": 1}])
        self.assertFalse(os.path.exists(self.path + ".tmp"))

    def test_empty_file_gives_empty_list(self):
        self.write_raw("")
        self.assertEqual(self.storage.load(), [])
        self.write_raw("   \n")
        self.assertEqual(self.storage.load(), [])

    def test_broken_json_raises_storage_error(self):
        self.write_raw('[{"a": 1}')
        with self.assertRaises(StorageError) as context:
            self.storage.load()
        self.assertIn("buzilgan", str(context.exception))

    def test_json_that_is_not_a_list_raises_storage_error(self):
        self.write_raw('{"a": 1}')
        with self.assertRaises(StorageError):
            self.storage.load()

    def test_file_with_bom_is_read(self):
        self.write_raw('[{"a": 1}]', encoding="utf-8-sig")
        self.assertEqual(self.storage.load(), [{"a": 1}])

    def test_storage_error_is_an_app_error(self):
        self.assertTrue(issubclass(StorageError, AppError))


if __name__ == "__main__":
    unittest.main()
