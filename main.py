"""main.py - dasturni ishga tushiradi (I ning ishi).

Hamma qismni ulaydi: storage -> services -> Menu (J yozgan).
Ishga tushirish:  python main.py
"""

import os

from exceptions import AppError
from services.auth import AuthService
from services.inventory import InventoryService
from services.sales import SalesService
from storage.json_storage import JsonStorage
from ui.menu import Menu

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def build_services(data_dir=DATA_DIR):
    """Fayllar (data/ papkasi) va uchta xizmatni yasaydi."""
    users_storage = JsonStorage(os.path.join(data_dir, "users.json"))
    products_storage = JsonStorage(os.path.join(data_dir, "products.json"))
    sales_storage = JsonStorage(os.path.join(data_dir, "sales.json"))

    auth = AuthService(users_storage)
    inventory = InventoryService(products_storage)
    sales = SalesService(sales_storage, inventory)
    return auth, inventory, sales


def main():
    try:
        auth, inventory, sales = build_services()
    except AppError as error:
        # Masalan, ma'lumot fayli buzilgan bo'lsa: dastur yiqilmaydi, tushunarli xabar chiqadi
        print(f"Dasturni ishga tushirib bo'lmadi: {error}")
        return
    Menu(auth, inventory, sales).run()


if __name__ == "__main__":
    main()
