"""models/user.py - foydalanuvchilar (I ning ishi).

User - abstract sinf. Admin va Cashier undan meros oladi va har biri
o'z ruxsatlarini (permissions) beradi.
"""

from abc import ABC, abstractmethod

from exceptions import PermissionDeniedError, StorageError


class User(ABC):
    """Foydalanuvchi (abstract). To'g'ridan-to'g'ri yaratib bo'lmaydi."""

    role = ""  # har bir sinf o'z rolini yozadi: 'Admin' yoki 'Kassir'

    def __init__(self, username, password):
        self.username = username
        self._password = password  # '_' - faqat sinf ichida ishlatiladi

    @abstractmethod
    def permissions(self):
        """Foydalanuvchining ruxsatlari ro'yxati."""

    def can(self, permission):
        """Ruxsat bormi? Masalan: user.can('sell')."""
        return permission in self.permissions()

    def require(self, permission):
        """Ruxsat bo'lmasa PermissionDeniedError ko'taradi."""
        if not self.can(permission):
            raise PermissionDeniedError(f"'{self.username}' uchun bu amalga ruxsat yo'q.")

    def check_password(self, password):
        return self._password == password

    def to_dict(self):
        """Faylga yozish uchun lug'at."""
        return {"username": self.username, "password": self._password, "role": self.role}

    def __str__(self):
        return f"{self.username} ({self.role})"


class Admin(User):
    """Do'kon egasi: hamma narsaga ruxsati bor."""

    role = "Admin"

    def permissions(self):
        return ["manage_products", "sell", "view_stock", "view_reports", "manage_users"]


class Cashier(User):
    """Kassir: faqat sotuv qiladi va ombor qoldig'ini ko'radi."""

    role = "Kassir"

    def permissions(self):
        return ["sell", "view_stock"]


def user_from_dict(data):
    """Fayldan o'qilgan lug'atdan Admin yoki Cashier yasaydi."""
    classes = {Admin.role: Admin, Cashier.role: Cashier}
    try:
        user_class = classes[data["role"]]
        username = data["username"]
        password = data["password"]
    except (KeyError, TypeError):
        raise StorageError("Fayldagi foydalanuvchi ma'lumoti noto'g'ri")
    if not isinstance(username, str) or not username or not isinstance(password, str):
        raise StorageError("Fayldagi foydalanuvchi ma'lumoti noto'g'ri")
    return user_class(username, password)
