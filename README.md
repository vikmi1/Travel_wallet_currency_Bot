**English** · [Deutsch](README.de.md) · [Русский](README.ru.md)

# Travel Currency Bot

A Telegram bot for managing personal finances while travelling. It converts currencies using the live [exchangerate.host](http://api.exchangerate.host) API and tracks expenses in two currencies at once.

The bot's interface is in Russian.

---

## Features

| Feature | Description |
|---------|----------|
| ✈️ Create a trip | Choose the departure and destination countries — the bot finds the currencies and the exchange rate |
| 💰 Dual balance | The remaining balance is always shown in both currencies |
| 📝 Expense tracking | Send a number — the bot converts it and asks whether to record it as an expense |
| 📋 Expense history | Breakdown by date, amount and currency |
| 🗺 Multiple trips | Switch between trips |
| 💱 Change the rate | Set the rate manually (for example, the one at a local exchange office) |
| 🔗 Slash commands | Alternative control without buttons |

---

## Commands

| Command | Action |
|---------|----------|
| `/start` | Start the bot and open the menu |
| `/newtrip` | Create a new trip |
| `/switch` | Switch the active trip |
| `/balance` | Show the current balance |
| `/history` | Expense history |
| `/setrate` | Change the exchange rate manually |

---

## Example

1. `/start` → choose **Create a trip**
2. Enter the departure country: `Россия` (Russia)
3. Enter the destination country: `Италия` (Italy)
4. Confirm the rate (or enter it manually)
5. Enter the starting amount: `200000`
6. The bot creates a wallet: `200 000 RUB ≈ 1 923 EUR`
7. Send `100` → the bot shows `100 EUR = 10 400 RUB` and asks whether to record the expense

---

## Project structure

```
API_travel_currency_bot/
├── bot.py            # Main file: commands, handlers, dialog logic
├── current_api.py    # Requests to api.exchangerate.host
├── database.py       # SQLite: users, trips, expenses
├── keyboards.py      # Inline keyboards
├── countries.py      # "country → currency code" dictionary
├── requirements.txt  # Python dependencies
└── .env              # Keys (do not commit to git!)
```

---

## Installation and running

### 1. Create a virtual environment

```bash
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Linux / macOS:** `source venv/bin/activate`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

Create a `.env` file in the project root:

```
TELEGRAM_BOT_TOKEN=token_from_BotFather
API_KEY=key_from_exchangerate.host
```

Where to get the keys:
- `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather) in Telegram
- `API_KEY` — at [exchangerate.host](https://exchangerate.host) after signing up (free plan)

### 4. Run

```bash
python bot.py
```

---

## Technologies

- **Python 3.10+**
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) — Telegram integration
- **SQLite** (built-in `sqlite3` module) — data storage
- **exchangerate.host API** — real-time exchange rates
- **python-dotenv** — environment variables

---

## Supported countries (partial list)

Russia, USA, Germany, France, Italy, Spain, United Kingdom, China, Japan, South Korea, Thailand, Turkey, UAE, India, Australia, Canada, Brazil, Egypt, Georgia, Kazakhstan and many more.
The full list is in [countries.py](countries.py). Country names are entered in Russian.
