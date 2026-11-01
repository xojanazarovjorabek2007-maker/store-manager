"""services/auth.py - kirish va foydalanuvchilar (I ning ishi).

Bu yerda print va input ishlatilmaydi: natija qaytariladi yoki xato
(AppError) ko'tariladi. Ularni ui/menu.py (J) ko'rsatadi.
"""

from exceptions import AuthError, ValidationError
from models.user import Admin, Cashier, user_from_dict


class AuthService:
    """Login tekshirish va yangi kassir qo'shish."""

    def __init__(self, storage):
        self.storage = storage
        self._users = [user_from_dict(item) for item in storage.load()]
        if not self._users:
            # Birinchi ishga tushish: boshlang'ich akkauntlar yaratiladi
            self._users = [Admin("admin", "1234"), Cashier("kassir", "0000")]
            self._save()

    def _save(self):
        self.storage.save([user.to_dict() for user in self._users])

    def login(self, username, password):
        """Login va parol to'g'ri bo'lsa foydalanuvchini qaytaradi, aks holda AuthError."""
        for user in self._users:
            if user.username == username and user.check_password(password):
                return user
        raise AuthError()

    def add_cashier(self, username, password):
        """Yangi kassir qo'shadi va uni qaytaradi."""
        if not isinstance(username, str) or not username.strip():
            raise ValidationError("Login bo'sh bo'lmasligi kerak")
        if not isinstance(password, str) or not password.strip():
            raise ValidationError("Parol bo'sh bo'lmasligi kerak")
        username = username.strip()
        password = password.strip()
        if self._username_exists(username):
            raise ValidationError(f"'{username}' logini allaqachon mavjud")
        cashier = Cashier(username, password)
        self._users.append(cashier)
        self._save()
        return cashier

    def _username_exists(self, username):
        for user in self._users:
            if user.username.lower() == username.lower():
                return True
        return False
