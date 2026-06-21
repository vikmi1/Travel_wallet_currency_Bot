"""
Модуль для работы с API exchangerate.host.
Все запросы идут на endpoint: http://api.exchangerate.host/convert
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "http://api.exchangerate.host/convert"
TIMEOUT = 10  # секунды ожидания ответа


def get_exchange_rate(from_currency: str, to_currency: str) -> float | None:
    """
    Получить курс обмена: сколько to_currency за 1 from_currency.
    Возвращает float или None при ошибке.
    """
    params = {
        "access_key": API_KEY,
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "amount": 1,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            # Логируем ошибку от API
            error_info = data.get("error", {})
            print(f"[API] Ошибка: {error_info.get('type')} — {error_info.get('info')}")
            return None

        result = data.get("result")
        if result is None or result <= 0:
            print(f"[API] Некорректный результат: {result}")
            return None

        return float(result)

    except requests.exceptions.Timeout:
        print(f"[API] Превышено время ожидания ({TIMEOUT}с)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[API] Ошибка запроса: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"[API] Ошибка разбора ответа: {e}")
        return None


RATE_LIMIT_DELAY = 1.1  # пауза между запросами (сек) — защита от 429 на бесплатном плане


def get_rates_for_currencies(target_currencies: list[str], home_currency: str) -> dict[str, float]:
    """
    Получить курсы нескольких валют к home_currency.
    Между запросами выдерживает паузу RATE_LIMIT_DELAY во избежание 429.
    Возвращает {currency_code: rate}, где rate = сколько home_currency за 1 target.
    """
    results = {}
    for i, curr in enumerate(target_currencies):
        if curr == home_currency:
            results[curr] = 1.0
            continue
        if i > 0:
            time.sleep(RATE_LIMIT_DELAY)
        rate = get_exchange_rate(curr, home_currency)
        if rate is not None:
            results[curr] = rate
    return results


def convert_amount(from_currency: str, to_currency: str, amount: float) -> float | None:
    """
    Конвертировать amount из from_currency в to_currency через API.
    Возвращает сконвертированную сумму или None при ошибке.
    """
    params = {
        "access_key": API_KEY,
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "amount": amount,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            error_info = data.get("error", {})
            print(f"[API] Ошибка конвертации: {error_info.get('type')} — {error_info.get('info')}")
            return None

        result = data.get("result")
        if result is None:
            return None

        return round(float(result), 2)

    except requests.exceptions.Timeout:
        print(f"[API] Превышено время ожидания при конвертации ({TIMEOUT}с)")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[API] Ошибка запроса при конвертации: {e}")
        return None
    except (KeyError, ValueError) as e:
        print(f"[API] Ошибка разбора ответа при конвертации: {e}")
        return None
