"""
Telegram-бот «Финансовый помощник путешественника».
Управление кошельками и расходами в разных валютах через API exchangerate.host.
"""

import os
import telebot
from telebot import types
from dotenv import load_dotenv

import current_api
import database
import keyboards
from countries import get_currency_by_country, get_currency_name

load_dotenv()

bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), parse_mode=None)

# ===== Состояния диалога =====
STATE_NEW_TRIP_FROM      = "new_trip_from"       # ожидаем страну отправления
STATE_NEW_TRIP_TO        = "new_trip_to"         # ожидаем страну назначения
STATE_NEW_TRIP_RATE      = "new_trip_rate"       # ожидаем ручной ввод курса
STATE_NEW_TRIP_AMOUNT    = "new_trip_amount"     # ожидаем начальную сумму
STATE_SET_RATE           = "set_rate"            # ожидаем новый курс для активного кошелька
STATE_EXPENSE_NAME       = "expense_name"        # ожидаем название расхода
STATE_RATE_CUSTOM        = "rate_custom"         # ожидаем страну/валюту для просмотра курса
STATE_MY_CURRENCY_CUSTOM = "my_currency_custom"  # ожидаем страну для настройки домашней валюты

# 8 основных валют для экрана «Основные валюты»
MAIN_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CNY", "CHF", "AUD", "CAD"]

# In-memory хранилища состояний и временных данных (на одну сессию)
user_states: dict[int, str] = {}
user_data:   dict[int, dict] = {}

# ===== Инициализация =====
database.init_db()


# ===== Вспомогательные функции состояний =====

def set_state(user_id: int, state: str | None):
    if state is None:
        user_states.pop(user_id, None)
    else:
        user_states[user_id] = state


def get_state(user_id: int) -> str | None:
    return user_states.get(user_id)


def save(user_id: int, key: str, value):
    """Сохранить временное значение для шагов диалога"""
    user_data.setdefault(user_id, {})[key] = value


def load(user_id: int, key: str):
    """Прочитать временное значение"""
    return user_data.get(user_id, {}).get(key)


def clear(user_id: int):
    """Сбросить состояние и временные данные"""
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)


# ===== Утилиты =====

def send_menu(chat_id: int, text: str = "Выбери действие:"):
    bot.send_message(chat_id, text, reply_markup=keyboards.main_menu_keyboard())


def parse_number(text: str) -> float | None:
    """Попытаться распознать число из строки (допускаем запятые и пробелы)"""
    try:
        return float(text.replace(",", ".").replace(" ", "").replace(" ", ""))
    except ValueError:
        return None


# ===== Команды =====

@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    """Приветствие и главное меню"""
    user_id   = message.from_user.id
    first_name = message.from_user.first_name or "Путешественник"

    database.get_or_create_user(user_id)
    clear(user_id)

    text = (
        f"Привет, {first_name}! 👋\n\n"
        "Я твой персональный помощник для управления финансами в путешествиях! 🌍💰\n\n"
        "Что я умею:\n"
        "• Создавать кошельки для разных стран\n"
        "• Конвертировать валюты по актуальным курсам\n"
        "• Отслеживать твои расходы\n"
        "• Показывать остаток в двух валютах\n\n"
        "Выбери действие из меню ниже:"
    )
    send_menu(message.chat.id, text)


@bot.message_handler(commands=["newtrip"])
def cmd_newtrip(message: types.Message):
    start_new_trip(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["balance"])
def cmd_balance(message: types.Message):
    show_balance(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["history"])
def cmd_history(message: types.Message):
    show_history(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["switch"])
def cmd_switch(message: types.Message):
    show_my_trips(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["setrate"])
def cmd_setrate(message: types.Message):
    start_set_rate(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["countries"])
def cmd_countries(message: types.Message):
    show_countries(message.chat.id)


@bot.message_handler(commands=["mycurrency"])
def cmd_mycurrency(message: types.Message):
    database.get_or_create_user(message.from_user.id)
    show_my_currency_menu(message.chat.id, message.from_user.id)


# ===== Обработчик callback-кнопок =====

@bot.callback_query_handler(func=lambda call: True)
def on_callback(call: types.CallbackQuery):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data    = call.data

    bot.answer_callback_query(call.id)  # убираем «часики» на кнопке

    if data == "new_trip":
        start_new_trip(chat_id, user_id)

    elif data == "my_trips":
        show_my_trips(chat_id, user_id)

    elif data == "balance":
        show_balance(chat_id, user_id)

    elif data == "history":
        show_history(chat_id, user_id)

    elif data == "set_rate":
        start_set_rate(chat_id, user_id)

    elif data == "view_rates":
        show_rates_menu(chat_id, user_id)

    elif data == "rates_main":
        show_main_rates(chat_id, user_id)

    elif data == "rates_custom":
        start_rate_custom(chat_id, user_id)

    elif data == "my_currency":
        show_my_currency_menu(chat_id, user_id)

    elif data == "my_currency_custom":
        set_state(user_id, STATE_MY_CURRENCY_CUSTOM)
        bot.send_message(
            chat_id,
            "🌐 Введи название страны (на русском) или код валюты:\n"
            "Примеры: Бразилия, Индия, AED, BRL\n\n"
            "Список всех стран: /countries",
        )

    elif data.startswith("set_currency_"):
        code = data.split("set_currency_", 1)[1]
        database.set_home_currency(user_id, code)
        curr_name = get_currency_name(code)
        set_state(user_id, None)
        bot.send_message(
            chat_id,
            f"✅ Домашняя валюта установлена: {code} ({curr_name})",
            reply_markup=keyboards.main_menu_keyboard(),
        )

    elif data == "back_to_menu":
        clear(user_id)
        send_menu(chat_id)

    elif data == "rate_from_api":
        apply_api_rate(chat_id, user_id)

    elif data == "rate_ok":
        # Пользователь подтвердил курс — переходим к вводу суммы
        if load(user_id, "exchange_rate"):
            set_state(user_id, STATE_NEW_TRIP_AMOUNT)
            from_curr = load(user_id, "from_currency")
            bot.send_message(
                chat_id,
                f"Введи начальную сумму поездки в {from_curr}:"
            )

    elif data == "rate_manual":
        # Пользователь хочет ввести курс вручную
        set_state(user_id, STATE_NEW_TRIP_RATE)
        from_curr = load(user_id, "from_currency")
        to_curr   = load(user_id, "to_currency")
        bot.send_message(
            chat_id,
            f"Введи курс вручную — сколько {to_curr} за 1 {from_curr}:\n"
            f"(например: 0.0094 или 1.08)"
        )

    elif data == "expense_skip_name":
        # Пропустить название — показываем подтверждение без названия
        pending = load(user_id, "pending_expense")
        if pending:
            save(user_id, "pending_expense", {**pending, "note": ""})
            trip = database.get_active_trip(user_id)
            _send_expense_confirm(chat_id, pending, trip)

    elif data == "expense_yes":
        # Подтвердить и записать расход
        pending = load(user_id, "pending_expense")
        if pending:
            trip = database.get_active_trip(user_id)
            if trip:
                note = pending.get("note", "")
                database.add_expense(trip["id"], pending["foreign"], pending["home"], note)
                updated = database.get_trip(trip["id"])
                balance_warn = " ⚠️ Баланс отрицательный!" if updated["balance_home"] < 0 else ""
                note_line = f"\n📝 {note}" if note else ""
                bot.send_message(
                    chat_id,
                    f"✅ Расход записан!{note_line}\n\n"
                    f"Остаток: {updated['balance_foreign']:.2f} {updated['to_currency']} "
                    f"= {updated['balance_home']:.2f} {updated['from_currency']}"
                    f"{balance_warn}",
                    reply_markup=keyboards.back_keyboard(),
                )
                clear(user_id)

    elif data == "expense_no":
        clear(user_id)
        bot.send_message(chat_id, "❌ Расход не записан.", reply_markup=keyboards.back_keyboard())

    elif data.startswith("switch_"):
        trip_id = int(data.split("_", 1)[1])
        database.switch_trip(user_id, trip_id)
        trip = database.get_trip(trip_id)
        bot.send_message(
            chat_id,
            f"✅ Активное путешествие: {trip['name']}\n\n"
            f"Остаток: {trip['balance_foreign']:.2f} {trip['to_currency']} "
            f"= {trip['balance_home']:.2f} {trip['from_currency']}",
            reply_markup=keyboards.back_keyboard(),
        )


# ===== Обработчик текстовых сообщений =====

@bot.message_handler(func=lambda msg: True)
def on_text(message: types.Message):
    """Маршрутизация по текущему состоянию пользователя"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    text    = message.text.strip()
    state   = get_state(user_id)

    if state == STATE_NEW_TRIP_FROM:
        handle_from_country(chat_id, user_id, text)

    elif state == STATE_NEW_TRIP_TO:
        handle_to_country(chat_id, user_id, text)

    elif state == STATE_NEW_TRIP_RATE:
        handle_manual_rate(chat_id, user_id, text)

    elif state == STATE_NEW_TRIP_AMOUNT:
        handle_initial_amount(chat_id, user_id, text)

    elif state == STATE_SET_RATE:
        handle_new_rate(chat_id, user_id, text)

    elif state == STATE_EXPENSE_NAME:
        handle_expense_name(chat_id, user_id, text)

    elif state == STATE_RATE_CUSTOM:
        handle_rate_custom(chat_id, user_id, text)

    elif state == STATE_MY_CURRENCY_CUSTOM:
        handle_my_currency_custom(chat_id, user_id, text)

    else:
        # Нет активного состояния — пробуем распознать как сумму расхода
        handle_expense(chat_id, user_id, text)


# ===== Создание путешествия =====

def start_new_trip(chat_id: int, user_id: int):
    """Шаг 1 — запросить страну отправления"""
    clear(user_id)
    set_state(user_id, STATE_NEW_TRIP_FROM)
    bot.send_message(
        chat_id,
        "✈️ Создаём новое путешествие!\n\n"
        "Введи страну отправления (на русском):\n"
        "Примеры: Россия, Германия, Китай, США\n\n"
        "📋 Полный список стран: /countries"
    )


def handle_from_country(chat_id: int, user_id: int, text: str):
    """Шаг 2 — обработать страну отправления"""
    currency = get_currency_by_country(text)
    if not currency:
        bot.send_message(
            chat_id,
            f"❓ Страна «{text}» не найдена. Попробуй ещё раз.\n"
            "Примеры: Россия, Германия, США, Китай, Таиланд, Италия\n\n"
            "📋 Полный список доступных стран: /countries"
        )
        return

    save(user_id, "from_country",  text.capitalize())
    save(user_id, "from_currency", currency)
    set_state(user_id, STATE_NEW_TRIP_TO)

    bot.send_message(
        chat_id,
        f"✅ {text.capitalize()} — {currency} ({get_currency_name(currency)})\n\n"
        "Теперь введи страну назначения:"
    )


def handle_to_country(chat_id: int, user_id: int, text: str):
    """Шаг 3 — обработать страну назначения и получить курс"""
    currency = get_currency_by_country(text)
    if not currency:
        bot.send_message(
            chat_id,
            f"❓ Страна «{text}» не найдена. Попробуй ещё раз.\n"
            "Примеры: Италия, Япония, Таиланд, Турция\n\n"
            "📋 Полный список доступных стран: /countries"
        )
        return

    from_currency = load(user_id, "from_currency")
    if currency == from_currency:
        bot.send_message(
            chat_id,
            "⚠️ Страна назначения совпадает со страной отправления. Укажи другую страну:"
        )
        return

    save(user_id, "to_country",  text.capitalize())
    save(user_id, "to_currency", currency)

    # Запрашиваем курс у API
    bot.send_message(chat_id, "⏳ Получаю актуальный курс...")
    rate = current_api.get_exchange_rate(from_currency, currency)

    if rate is None:
        # API недоступен — предлагаем ввести вручную
        set_state(user_id, STATE_NEW_TRIP_RATE)
        bot.send_message(
            chat_id,
            "❌ Не удалось получить курс от API. Введи курс вручную —\n"
            f"сколько {currency} за 1 {from_currency}:"
        )
        return

    save(user_id, "exchange_rate", rate)

    bot.send_message(
        chat_id,
        f"✅ {text.capitalize()} — {currency} ({get_currency_name(currency)})\n\n"
        f"Текущий курс: 1 {from_currency} = {rate:.6g} {currency}\n\n"
        "Этот курс тебя устраивает?",
        reply_markup=keyboards.confirm_rate_keyboard(),
    )


def handle_manual_rate(chat_id: int, user_id: int, text: str):
    """Шаг 4 (альтернативный) — принять курс, введённый вручную"""
    rate = parse_number(text)
    if rate is None or rate <= 0:
        from_curr = load(user_id, "from_currency")
        to_curr   = load(user_id, "to_currency")
        bot.send_message(
            chat_id,
            f"❌ Некорректное число. Введи курс — сколько {to_curr} за 1 {from_curr}:\n"
            "Например: 0.0094 или 1.08"
        )
        return

    from_curr = load(user_id, "from_currency")
    to_curr   = load(user_id, "to_currency")

    save(user_id, "exchange_rate", rate)
    set_state(user_id, STATE_NEW_TRIP_AMOUNT)

    bot.send_message(
        chat_id,
        f"✅ Курс установлен: 1 {from_curr} = {rate} {to_curr}\n\n"
        f"Введи начальную сумму поездки в {from_curr}:"
    )


def handle_initial_amount(chat_id: int, user_id: int, text: str):
    """Шаг 5 — принять начальную сумму и создать путешествие"""
    amount = parse_number(text)
    if amount is None or amount <= 0:
        from_curr = load(user_id, "from_currency")
        bot.send_message(
            chat_id,
            f"❌ Некорректная сумма. Введи число в {from_curr}:\n"
            "Например: 200000 или 1500.50"
        )
        return

    from_country  = load(user_id, "from_country")
    to_country    = load(user_id, "to_country")
    from_currency = load(user_id, "from_currency")
    to_currency   = load(user_id, "to_currency")
    rate          = load(user_id, "exchange_rate")

    # Конвертируем начальную сумму в иностранную валюту
    amount_foreign = round(amount * rate, 2)
    trip_name      = f"{from_country} → {to_country}"

    trip_id = database.create_trip(
        user_id=user_id,
        name=trip_name,
        from_country=from_country,
        to_country=to_country,
        from_currency=from_currency,
        to_currency=to_currency,
        exchange_rate=rate,
        initial_amount_home=amount,
        initial_amount_foreign=amount_foreign,
    )

    clear(user_id)

    bot.send_message(
        chat_id,
        f"🎉 Путешествие создано!\n\n"
        f"📍 {trip_name}\n"
        f"💱 Курс: 1 {from_currency} = {rate:.6g} {to_currency}\n\n"
        f"💰 Стартовый баланс:\n"
        f"  {amount:,.2f} {from_currency}\n"
        f"  ≈ {amount_foreign:,.2f} {to_currency}\n\n"
        f"Теперь просто отправляй мне суммы расходов в {to_currency} — "
        "я пересчитаю и запишу их.",
        reply_markup=keyboards.main_menu_keyboard(),
    )


# ===== Просмотр данных =====

def show_balance(chat_id: int, user_id: int):
    """Показать баланс активного путешествия"""
    trip = database.get_active_trip(user_id)
    if not trip:
        send_menu(chat_id, "❌ У тебя нет активного путешествия. Создай его!")
        return

    balance_warn = "\n⚠️ Баланс отрицательный!" if trip["balance_home"] < 0 else ""

    bot.send_message(
        chat_id,
        f"💰 Баланс: {trip['name']}\n\n"
        f"Остаток: {trip['balance_foreign']:,.2f} {trip['to_currency']} "
        f"= {trip['balance_home']:,.2f} {trip['from_currency']}"
        f"{balance_warn}\n\n"
        f"Курс: 1 {trip['from_currency']} = {trip['exchange_rate']:.6g} {trip['to_currency']}",
        reply_markup=keyboards.back_keyboard(),
    )


def show_history(chat_id: int, user_id: int):
    """Показать историю расходов активного путешествия"""
    trip = database.get_active_trip(user_id)
    if not trip:
        send_menu(chat_id, "❌ У тебя нет активного путешествия.")
        return

    expenses = database.get_expenses(trip["id"])
    if not expenses:
        bot.send_message(
            chat_id,
            f"📋 История расходов: {trip['name']}\n\nРасходов пока нет.",
            reply_markup=keyboards.back_keyboard(),
        )
        return

    lines = [f"📋 История расходов: {trip['name']}\n"]
    total_foreign = 0.0
    total_home    = 0.0

    for i, exp in enumerate(expenses[:20], 1):  # максимум 20 последних записей
        date_str  = exp["created_at"][:16].replace("T", " ")
        note_part = f"  📝 {exp['note']}" if exp["note"] else ""
        lines.append(
            f"{i}. {date_str}{note_part}\n"
            f"   -{exp['amount_foreign']:.2f} {trip['to_currency']} "
            f"/ -{exp['amount_home']:.2f} {trip['from_currency']}"
        )
        total_foreign += exp["amount_foreign"]
        total_home    += exp["amount_home"]

    lines.append(
        f"\n💸 Итого потрачено:\n"
        f"  {total_foreign:,.2f} {trip['to_currency']} "
        f"= {total_home:,.2f} {trip['from_currency']}\n"
        f"\n💰 Остаток:\n"
        f"  {trip['balance_foreign']:,.2f} {trip['to_currency']} "
        f"= {trip['balance_home']:,.2f} {trip['from_currency']}"
    )

    bot.send_message(chat_id, "\n".join(lines), reply_markup=keyboards.back_keyboard())


def show_my_trips(chat_id: int, user_id: int):
    """Показать список всех путешествий для переключения"""
    trips = database.get_all_trips(user_id)
    if not trips:
        send_menu(chat_id, "🗺 У тебя пока нет путешествий. Создай первое!")
        return

    bot.send_message(
        chat_id,
        "🗺 Твои путешествия:\n(нажми, чтобы сделать активным)",
        reply_markup=keyboards.trips_keyboard(trips),
    )


# ===== Изменение курса =====

def start_set_rate(chat_id: int, user_id: int):
    """Начать процесс изменения курса вручную"""
    trip = database.get_active_trip(user_id)
    if not trip:
        send_menu(chat_id, "❌ Нет активного путешествия.")
        return

    set_state(user_id, STATE_SET_RATE)
    bot.send_message(
        chat_id,
        f"💱 Изменить курс для: {trip['name']}\n"
        f"Текущий: 1 {trip['from_currency']} = {trip['exchange_rate']:.6g} {trip['to_currency']}\n\n"
        f"Введи новый курс вручную (сколько {trip['to_currency']} за 1 {trip['from_currency']})\n"
        f"или нажми кнопку ниже для сброса на актуальный:",
        reply_markup=keyboards.set_rate_keyboard(),
    )


def apply_api_rate(chat_id: int, user_id: int):
    """Получить актуальный курс из API и применить к активному путешествию"""
    trip = database.get_active_trip(user_id)
    if not trip:
        send_menu(chat_id, "❌ Нет активного путешествия.")
        return

    bot.send_message(chat_id, "⏳ Получаю актуальный курс...")
    rate = current_api.get_exchange_rate(trip["from_currency"], trip["to_currency"])

    if rate is None:
        bot.send_message(
            chat_id,
            "❌ Не удалось получить курс от API. Попробуй позже или введи вручную:",
            reply_markup=keyboards.set_rate_keyboard(),
        )
        return

    database.update_trip_rate(trip["id"], rate)
    updated = database.get_trip(trip["id"])
    clear(user_id)

    bot.send_message(
        chat_id,
        f"✅ Курс сброшен на актуальный!\n\n"
        f"1 {trip['from_currency']} = {rate:.6g} {trip['to_currency']}\n\n"
        f"Пересчитанный остаток:\n"
        f"  {updated['balance_foreign']:,.2f} {trip['to_currency']} "
        f"= {updated['balance_home']:,.2f} {trip['from_currency']}",
        reply_markup=keyboards.back_keyboard(),
    )


def handle_new_rate(chat_id: int, user_id: int, text: str):
    """Принять и сохранить новый курс обмена"""
    rate = parse_number(text)
    if rate is None or rate <= 0:
        bot.send_message(chat_id, "❌ Некорректное число. Попробуй ещё раз:")
        return

    trip = database.get_active_trip(user_id)
    if not trip:
        bot.send_message(chat_id, "❌ Нет активного путешествия.")
        clear(user_id)
        return

    database.update_trip_rate(trip["id"], rate)
    updated = database.get_trip(trip["id"])
    clear(user_id)

    bot.send_message(
        chat_id,
        f"✅ Курс обновлён!\n\n"
        f"1 {trip['from_currency']} = {rate} {trip['to_currency']}\n\n"
        f"Пересчитанный остаток:\n"
        f"  {updated['balance_foreign']:,.2f} {trip['to_currency']} "
        f"= {updated['balance_home']:,.2f} {trip['from_currency']}",
        reply_markup=keyboards.back_keyboard(),
    )


# ===== Ввод суммы расхода =====

def handle_expense(chat_id: int, user_id: int, text: str):
    """
    Любое сообщение без активного состояния — попытка распознать как расход
    в иностранной валюте активного путешествия.
    """
    amount = parse_number(text)
    if amount is None or amount <= 0:
        # Не число — просто показываем меню
        send_menu(chat_id)
        return

    trip = database.get_active_trip(user_id)
    if not trip:
        bot.send_message(
            chat_id,
            "❌ У тебя нет активного путешествия. Создай его сначала!",
            reply_markup=keyboards.main_menu_keyboard(),
        )
        return

    # Пересчёт расхода в домашнюю валюту по сохранённому курсу
    amount_home = round(amount / trip["exchange_rate"], 2)

    # Сохраняем сумму и переходим к запросу названия
    save(user_id, "pending_expense", {
        "foreign": amount,
        "home": amount_home,
        "to_currency": trip["to_currency"],
        "from_currency": trip["from_currency"],
    })
    set_state(user_id, STATE_EXPENSE_NAME)

    bot.send_message(
        chat_id,
        f"💱 {amount:,.2f} {trip['to_currency']} = {amount_home:,.2f} {trip['from_currency']}\n\n"
        "Как называется этот расход?\n"
        "Например: обед, такси, билеты, сувениры",
        reply_markup=keyboards.expense_name_keyboard(),
    )


def handle_expense_name(chat_id: int, user_id: int, text: str):
    """Принять название расхода и перейти к подтверждению"""
    pending = load(user_id, "pending_expense")
    if not pending:
        set_state(user_id, None)
        send_menu(chat_id)
        return

    # Сохраняем название и показываем подтверждение
    save(user_id, "pending_expense", {**pending, "note": text})
    set_state(user_id, None)

    trip = database.get_active_trip(user_id)
    _send_expense_confirm(chat_id, {**pending, "note": text}, trip)


def _send_expense_confirm(chat_id: int, pending: dict, trip):
    """Показать итоговую карточку расхода с кнопками подтверждения"""
    note = pending.get("note", "")
    to_curr   = pending.get("to_currency")   or (trip["to_currency"]   if trip else "?")
    from_curr = pending.get("from_currency") or (trip["from_currency"] if trip else "?")
    note_line = f"\n📝 {note}" if note else ""

    bot.send_message(
        chat_id,
        f"💱 {pending['foreign']:,.2f} {to_curr} = {pending['home']:,.2f} {from_curr}"
        f"{note_line}\n\n"
        "Учесть как расход?",
        reply_markup=keyboards.confirm_expense_keyboard(),
    )


# ===== Просмотр курса =====

def show_rates_menu(chat_id: int, user_id: int):
    """Подменю: выбор между основными валютами и произвольной"""
    home_curr = database.get_home_currency(user_id)
    curr_name = get_currency_name(home_curr)
    bot.send_message(
        chat_id,
        f"📈 Просмотр курсов валют\n\n"
        f"Твоя домашняя валюта: {home_curr} ({curr_name})\n"
        "(изменить: ⚙️ Моя валюта)\n\n"
        "Что хочешь посмотреть?",
        reply_markup=keyboards.rate_view_keyboard(),
    )


def show_main_rates(chat_id: int, user_id: int):
    """Показать курсы 8 основных валют к домашней"""
    home_curr = database.get_home_currency(user_id)
    targets = [c for c in MAIN_CURRENCIES if c != home_curr]

    bot.send_message(chat_id, "⏳ Загружаю курсы... (~10 сек, бесплатный API)")
    rates = current_api.get_rates_for_currencies(targets, home_curr)

    if not rates:
        bot.send_message(
            chat_id,
            "❌ Не удалось получить курсы. Попробуй позже.",
            reply_markup=keyboards.back_keyboard(),
        )
        return

    lines = [f"📊 Основные валюты к {home_curr} ({get_currency_name(home_curr)}):\n"]
    for curr in targets:
        if curr in rates:
            lines.append(f"1 {curr} = {rates[curr]:,.4g} {home_curr}  ({get_currency_name(curr)})")
        else:
            lines.append(f"1 {curr} — ❌ нет данных")

    bot.send_message(chat_id, "\n".join(lines), reply_markup=keyboards.back_keyboard())


def start_rate_custom(chat_id: int, user_id: int):
    """Запросить у пользователя страну/валюту для просмотра произвольного курса"""
    home_curr = database.get_home_currency(user_id)
    set_state(user_id, STATE_RATE_CUSTOM)

    bot.send_message(
        chat_id,
        f"🔍 Курс к {home_curr} ({get_currency_name(home_curr)})\n\n"
        "Введи название страны (на русском) или код валюты:\n"
        "Примеры: Япония, Таиланд, EUR, JPY, AED\n\n"
        "Список всех стран: /countries",
    )


def handle_rate_custom(chat_id: int, user_id: int, text: str):
    """Получить и показать курс для произвольной валюты"""
    home_curr = database.get_home_currency(user_id)

    # Сначала пробуем как код валюты (3 буквы)
    text_up = text.strip().upper()
    if len(text_up) == 3 and text_up.isalpha():
        foreign_curr = text_up
    else:
        foreign_curr = get_currency_by_country(text)

    if not foreign_curr:
        bot.send_message(
            chat_id,
            f"❓ Не нашёл страну или валюту «{text}».\n"
            "Попробуй ещё раз или смотри список: /countries",
        )
        return  # состояние сохраняется, ждём следующего ввода

    set_state(user_id, None)

    if foreign_curr == home_curr:
        bot.send_message(
            chat_id,
            f"Это и есть твоя домашняя валюта ({home_curr}) — курс 1:1 😄",
            reply_markup=keyboards.back_keyboard(),
        )
        return

    bot.send_message(chat_id, f"⏳ Получаю курс {foreign_curr} → {home_curr}...")
    rate = current_api.get_exchange_rate(foreign_curr, home_curr)

    if rate is None:
        bot.send_message(
            chat_id,
            f"❌ Не удалось получить курс для {foreign_curr}. Попробуй другую валюту.",
            reply_markup=keyboards.back_keyboard(),
        )
        return

    bot.send_message(
        chat_id,
        f"📈 {foreign_curr} ({get_currency_name(foreign_curr)}):\n\n"
        f"1 {foreign_curr} = {rate:,.4g} {home_curr}",
        reply_markup=keyboards.back_keyboard(),
    )


# ===== Настройка домашней валюты =====

def show_my_currency_menu(chat_id: int, user_id: int):
    """Показать меню выбора домашней валюты"""
    home_curr = database.get_home_currency(user_id)
    curr_name = get_currency_name(home_curr)

    bot.send_message(
        chat_id,
        f"⚙️ Моя домашняя валюта\n\n"
        f"Сейчас установлена: {home_curr} ({curr_name})\n\n"
        "Выбери из популярных или введи свою страну:",
        reply_markup=keyboards.home_currency_keyboard(home_curr),
    )


def handle_my_currency_custom(chat_id: int, user_id: int, text: str):
    """Принять страну/код валюты от пользователя и сохранить как домашнюю"""
    text_up = text.strip().upper()
    if len(text_up) == 3 and text_up.isalpha():
        currency = text_up
    else:
        currency = get_currency_by_country(text)

    if not currency:
        bot.send_message(
            chat_id,
            f"❓ Не нашёл страну «{text}». Попробуй ещё раз.\n"
            "Или посмотри список: /countries",
        )
        return

    database.set_home_currency(user_id, currency)
    curr_name = get_currency_name(currency)
    set_state(user_id, None)

    bot.send_message(
        chat_id,
        f"✅ Домашняя валюта установлена: {currency} ({curr_name})",
        reply_markup=keyboards.main_menu_keyboard(),
    )


# ===== Список стран =====

def show_countries(chat_id: int):
    """Показать отсортированный список всех доступных стран с валютами"""
    from countries import COUNTRIES_TO_CURRENCY, get_currency_name

    sorted_items = sorted(COUNTRIES_TO_CURRENCY.items(), key=lambda x: x[0])

    lines = ["🌍 Доступные страны:\n"]
    for country, currency in sorted_items:
        lines.append(f"• {country.capitalize()} — {currency} ({get_currency_name(currency)})")

    bot.send_message(chat_id, "\n".join(lines), reply_markup=keyboards.back_keyboard())


# ===== Запуск =====

if __name__ == "__main__":
    print("Бот запущен. Нажми Ctrl+C для остановки.")
    bot.infinity_polling(skip_pending=True)
