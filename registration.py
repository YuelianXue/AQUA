import os
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Создаем папку DataBase, если она не существует
os.makedirs("DataBase", exist_ok=True)

# Инициализация БД SQLite
conn = sqlite3.connect("DataBase/users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    phone TEXT,
    registration_date TEXT
)
''')
conn.commit()

def is_russian_number(number: str) -> bool:
    """
    Примерная проверка: российский номер должен состоять из 11 цифр и начинаться с 7 или 8.
    """
    digits = ''.join(filter(str.isdigit, number))
    return len(digits) == 11 and (digits.startswith("7") or digits.startswith("8"))

def user_exists(telegram_id: int) -> bool:
    """Проверяет, существует ли пользователь в БД по telegram_id."""
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    return cursor.fetchone() is not None

def register_user(telegram_id: int, first_name: str, last_name: str, username: str, phone: str) -> None:
    """
    Регистрирует пользователя в БД, если его еще нет.
    """
    registration_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            """
            INSERT OR IGNORE INTO users 
            (telegram_id, first_name, last_name, username, phone, registration_date)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (telegram_id, first_name, last_name, username, phone, registration_date)
        )
        conn.commit()
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных: {e}")


def get_user(telegram_id: int):
    """
    Возвращает данные пользователя из БД в виде словаря или None, если пользователь не найден.
    """
    cursor.execute("SELECT telegram_id, first_name, last_name, username, phone, registration_date FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cursor.fetchone()
    if row:
        return {
            "telegram_id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "username": row[3],
            "phone": row[4],
            "registration_date": row[5]
        }
    return None
