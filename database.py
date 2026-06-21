"""
Модуль для работы с SQLite базой данных.
Хранит пользователей, путешествия и историю расходов.
"""

import sqlite3

DB_NAME = "travel_wallet.db"


def get_connection() -> sqlite3.Connection:
    """Создать соединение с БД, строки возвращаются как словари"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создать таблицы при первом запуске (если не существуют)"""
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY,
            home_currency TEXT    DEFAULT 'RUB',
            created_at    TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Добавляем home_currency в уже существующие базы
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN home_currency TEXT DEFAULT 'RUB'")
    except Exception:
        pass

    # Таблица путешествий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id          INTEGER NOT NULL,
            name             TEXT    NOT NULL,
            from_country     TEXT    NOT NULL,
            to_country       TEXT    NOT NULL,
            from_currency    TEXT    NOT NULL,
            to_currency      TEXT    NOT NULL,
            exchange_rate    REAL    NOT NULL,   -- сколько to_currency за 1 from_currency
            balance_home     REAL    NOT NULL,   -- остаток в домашней валюте
            balance_foreign  REAL    NOT NULL,   -- остаток в иностранной валюте
            is_active        INTEGER DEFAULT 0,
            created_at       TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)

    # Таблица расходов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id        INTEGER NOT NULL,
            amount_foreign REAL    NOT NULL,   -- сумма в иностранной валюте
            amount_home    REAL    NOT NULL,   -- сумма в домашней валюте
            note           TEXT    DEFAULT '', -- название / описание расхода
            created_at     TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (trip_id) REFERENCES trips(id)
        )
    """)

    # Добавляем note в уже существующие базы (безопасно — игнорируем ошибку если колонка есть)
    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN note TEXT DEFAULT ''")
    except Exception:
        pass

    conn.commit()
    conn.close()


# ===== Пользователи =====

def get_or_create_user(user_id: int):
    """Зарегистрировать пользователя, если он ещё не существует"""
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()


def get_home_currency(user_id: int) -> str:
    """Получить домашнюю валюту пользователя (по умолчанию RUB)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT home_currency FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return (row["home_currency"] or "RUB") if row else "RUB"


def set_home_currency(user_id: int, currency: str):
    """Сохранить домашнюю валюту пользователя"""
    conn = get_connection()
    conn.execute(
        "UPDATE users SET home_currency = ? WHERE user_id = ?",
        (currency.upper(), user_id),
    )
    conn.commit()
    conn.close()


# ===== Путешествия =====

def create_trip(
    user_id: int,
    name: str,
    from_country: str,
    to_country: str,
    from_currency: str,
    to_currency: str,
    exchange_rate: float,
    initial_amount_home: float,
    initial_amount_foreign: float,
) -> int:
    """
    Создать новое путешествие и сделать его активным.
    Возвращает id созданной записи.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Снять флаг активности со всех прочих поездок пользователя
    cursor.execute("UPDATE trips SET is_active = 0 WHERE user_id = ?", (user_id,))

    cursor.execute(
        """
        INSERT INTO trips
            (user_id, name, from_country, to_country,
             from_currency, to_currency, exchange_rate,
             balance_home, balance_foreign, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        (
            user_id, name, from_country, to_country,
            from_currency, to_currency, exchange_rate,
            initial_amount_home, initial_amount_foreign,
        ),
    )

    trip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return trip_id


def get_active_trip(user_id: int) -> sqlite3.Row | None:
    """Получить активное путешествие пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM trips WHERE user_id = ? AND is_active = 1", (user_id,)
    )
    trip = cursor.fetchone()
    conn.close()
    return trip


def get_all_trips(user_id: int) -> list[sqlite3.Row]:
    """Получить все путешествия пользователя (новые — первыми)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    )
    trips = cursor.fetchall()
    conn.close()
    return trips


def get_trip(trip_id: int) -> sqlite3.Row | None:
    """Получить путешествие по id"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    trip = cursor.fetchone()
    conn.close()
    return trip


def switch_trip(user_id: int, trip_id: int):
    """Переключить активное путешествие пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE trips SET is_active = 0 WHERE user_id = ?", (user_id,))
    cursor.execute(
        "UPDATE trips SET is_active = 1 WHERE id = ? AND user_id = ?",
        (trip_id, user_id),
    )
    conn.commit()
    conn.close()


def update_trip_rate(trip_id: int, new_rate: float):
    """
    Обновить курс обмена и пересчитать balance_foreign.
    balance_home остаётся источником правды.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance_home FROM trips WHERE id = ?", (trip_id,))
    row = cursor.fetchone()
    if row:
        new_balance_foreign = round(row["balance_home"] * new_rate, 2)
        cursor.execute(
            "UPDATE trips SET exchange_rate = ?, balance_foreign = ? WHERE id = ?",
            (new_rate, new_balance_foreign, trip_id),
        )
    conn.commit()
    conn.close()


# ===== Расходы =====

def add_expense(trip_id: int, amount_foreign: float, amount_home: float, note: str = ""):
    """Записать расход и уменьшить балансы путешествия"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO expenses (trip_id, amount_foreign, amount_home, note) VALUES (?, ?, ?, ?)",
        (trip_id, amount_foreign, amount_home, note.strip()),
    )

    cursor.execute(
        """
        UPDATE trips
        SET balance_foreign = balance_foreign - ?,
            balance_home    = balance_home    - ?
        WHERE id = ?
        """,
        (amount_foreign, amount_home, trip_id),
    )

    conn.commit()
    conn.close()


def get_expenses(trip_id: int) -> list[sqlite3.Row]:
    """Получить все расходы путешествия (новые — первыми)"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM expenses WHERE trip_id = ? ORDER BY created_at DESC",
        (trip_id,),
    )
    expenses = cursor.fetchall()
    conn.close()
    return expenses
