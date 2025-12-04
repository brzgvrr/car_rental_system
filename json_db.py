import json
from typing import Dict, Any
from pathlib import Path


DB_FILE = Path("db.json")


def save_database(data: Dict[str, Any]) -> None:
    """Сохранение словаря в JSON-файл."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_database() -> Dict[str, Any]:
    """Загрузка данных из JSON. Если файла нет – возвращаем пустую БД."""
    if not DB_FILE.exists():
        return {"cars": [], "customers": [], "rentals": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)