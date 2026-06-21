"""
Модуль с inline-клавиатурами для Telegram-бота.
"""

from telebot import types


def main_menu_keyboard() -> types.InlineKeyboardMarkup:
    """Главное меню"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✈️ Создать путешествие", callback_data="new_trip"),
        types.InlineKeyboardButton("🗺 Мои путешествия",     callback_data="my_trips"),
    )
    kb.add(
        types.InlineKeyboardButton("💰 Баланс",             callback_data="balance"),
        types.InlineKeyboardButton("📋 История расходов",   callback_data="history"),
    )
    kb.add(
        types.InlineKeyboardButton("💱 Изменить курс",      callback_data="set_rate"),
        types.InlineKeyboardButton("📈 Посмотреть курс",    callback_data="view_rates"),
    )
    kb.add(
        types.InlineKeyboardButton("⚙️ Моя валюта",         callback_data="my_currency"),
    )
    return kb


def rate_view_keyboard() -> types.InlineKeyboardMarkup:
    """Подменю просмотра курсов"""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("💰 Основные валюты",  callback_data="rates_main"))
    kb.add(types.InlineKeyboardButton("🔍 Выбрать самому",   callback_data="rates_custom"))
    kb.add(types.InlineKeyboardButton("🔙 Назад в меню",     callback_data="back_to_menu"))
    return kb


# Популярные валюты для кнопочного выбора
_POPULAR = [
    ("RUB", "🇷🇺"), ("USD", "🇺🇸"), ("EUR", "🇪🇺"),
    ("GBP", "🇬🇧"), ("CNY", "🇨🇳"), ("JPY", "🇯🇵"),
    ("CHF", "🇨🇭"), ("AUD", "🇦🇺"), ("CAD", "🇨🇦"),
    ("TRY", "🇹🇷"), ("THB", "🇹🇭"), ("KZT", "🇰🇿"),
]


def home_currency_keyboard(current: str) -> types.InlineKeyboardMarkup:
    """Клавиатура выбора домашней валюты; текущая отмечена галочкой"""
    kb = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton(
            f"{'✅ ' if code == current else ''}{flag} {code}",
            callback_data=f"set_currency_{code}",
        )
        for code, flag in _POPULAR
    ]
    kb.add(*buttons)
    kb.add(types.InlineKeyboardButton("🌐 Другая страна",  callback_data="my_currency_custom"))
    kb.add(types.InlineKeyboardButton("🔙 Назад в меню",   callback_data="back_to_menu"))
    return kb


def confirm_rate_keyboard() -> types.InlineKeyboardMarkup:
    """Подтверждение полученного курса обмена"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Да, подходит",      callback_data="rate_ok"),
        types.InlineKeyboardButton("✏️ Ввести вручную",   callback_data="rate_manual"),
    )
    return kb


def expense_name_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура при запросе названия расхода — можно пропустить"""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("⏭ Пропустить название", callback_data="expense_skip_name"))
    kb.add(types.InlineKeyboardButton("❌ Отменить расход",     callback_data="expense_no"))
    return kb


def confirm_expense_keyboard() -> types.InlineKeyboardMarkup:
    """Подтверждение записи расхода"""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Да, учесть расход", callback_data="expense_yes"),
        types.InlineKeyboardButton("❌ Нет",               callback_data="expense_no"),
    )
    return kb


def trips_keyboard(trips: list) -> types.InlineKeyboardMarkup:
    """Список путешествий; активное отмечено галочкой"""
    kb = types.InlineKeyboardMarkup(row_width=1)
    for trip in trips:
        marker = "✅ " if trip["is_active"] else ""
        label = f"{marker}{trip['name']}  ({trip['from_currency']} → {trip['to_currency']})"
        kb.add(
            types.InlineKeyboardButton(label, callback_data=f"switch_{trip['id']}")
        )
    kb.add(
        types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu")
    )
    return kb


def set_rate_keyboard() -> types.InlineKeyboardMarkup:
    """Меню изменения курса: кнопка актуального курса + назад"""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📡 Актуальный курс (из API)", callback_data="rate_from_api"))
    kb.add(types.InlineKeyboardButton("🔙 Назад в меню",             callback_data="back_to_menu"))
    return kb


def back_keyboard() -> types.InlineKeyboardMarkup:
    """Одна кнопка возврата в главное меню"""
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("🔙 В главное меню", callback_data="back_to_menu")
    )
    return kb
