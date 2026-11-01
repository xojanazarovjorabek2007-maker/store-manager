"""storage/json_storage.py - JSON fayldan o'qish va yozish (I ning ishi).

Bu qatlam faqat faylga tegadi. Ma'lumot nimaligini (mahsulotmi,
foydalanuvchimi) bilmaydi: oddiy ro'yxat (list) saqlaydi va qaytaradi.
"""

import json
import os

from exceptions import StorageError


class JsonStorage:
    """Bitta JSON faylni boshqaradi."""

    def __init__(self, path):
        self.path = path

    def load(self):
        """Fayldagi ro'yxatni qaytaradi. Fayl yo'q yoki bo'sh bo'lsa - bo'sh ro'yxat."""
        if not os.path.exists(self.path):
            return []
        try:
            # utf-8-sig: Windows Bloknoti qo'shgan BOM belgisini ham o'qiydi
            with open(self.path, "r", encoding="utf-8-sig") as file:
                content = file.read()
        except OSError as error:
            raise StorageError(f"Faylni o'qib bo'lmadi ({self.path}): {error}")
        if not content.strip():
            return []
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            raise StorageError(
                f"Ma'lumot fayli buzilgan: {self.path}. Faylni to'g'rilang yoki o'chirib yuboring."
            )
        if not isinstance(data, list):
            raise StorageError(f"Ma'lumot fayli noto'g'ri tuzilgan (ro'yxat kerak): {self.path}")
        return data

    def save(self, data):
        """Ro'yxatni faylga yozadi. Papka yo'q bo'lsa, yaratadi."""
        folder = os.path.dirname(self.path)
        temp_path = self.path + ".tmp"
        try:
            if folder:
                os.makedirs(folder, exist_ok=True)
            # Avval vaqtinchalik faylga yozamiz, keyin almashtiramiz:
            # dastur yozish paytida to'xtasa ham, eski fayl buzilmaydi.
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            os.replace(temp_path, self.path)
        except OSError as error:
            raise StorageError(f"Faylga yozib bo'lmadi ({self.path}): {error}")
