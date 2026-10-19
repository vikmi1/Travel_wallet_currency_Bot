[English](README.md) · **Deutsch** · [Русский](README.ru.md)

# Travel Currency Bot

Ein Telegram-Bot zur Verwaltung der eigenen Finanzen auf Reisen. Er rechnet Währungen über die Live-API von [exchangerate.host](http://api.exchangerate.host) um und erfasst Ausgaben gleichzeitig in zwei Währungen.

Die Oberfläche des Bots ist auf Russisch.

---

## Funktionen

| Funktion | Beschreibung |
|---------|----------|
| ✈️ Reise anlegen | Abreise- und Zielland wählen – der Bot ermittelt Währungen und Wechselkurs |
| 💰 Doppelter Kontostand | Der Restbetrag wird immer in beiden Währungen angezeigt |
| 📝 Ausgaben erfassen | Eine Zahl senden – der Bot rechnet um und fragt, ob die Ausgabe gespeichert werden soll |
| 📋 Ausgabenverlauf | Aufschlüsselung nach Datum, Betrag und Währung |
| 🗺 Mehrere Reisen | Zwischen Reisen wechseln |
| 💱 Kurs ändern | Den Kurs manuell festlegen (z. B. den der Wechselstube vor Ort) |
| 🔗 Slash-Befehle | Alternative Steuerung ohne Schaltflächen |

---

## Befehle

| Befehl | Aktion |
|---------|----------|
| `/start` | Bot starten und Menü öffnen |
| `/newtrip` | Neue Reise anlegen |
| `/switch` | Aktive Reise wechseln |
| `/balance` | Aktuellen Kontostand anzeigen |
| `/history` | Ausgabenverlauf |
| `/setrate` | Wechselkurs manuell ändern |

---

## Beispiel

1. `/start` → **Reise anlegen** wählen
2. Abreiseland eingeben: `Россия` (Russland)
3. Zielland eingeben: `Италия` (Italien)
4. Kurs bestätigen (oder manuell eingeben)
5. Startbetrag eingeben: `200000`
6. Der Bot legt eine Reisekasse an: `200 000 RUB ≈ 1 923 EUR`
7. `100` senden → der Bot zeigt `100 EUR = 10 400 RUB` und fragt, ob die Ausgabe gespeichert werden soll

---

## Projektstruktur

```
API_travel_currency_bot/
├── bot.py            # Hauptdatei: Befehle, Handler, Dialoglogik
├── current_api.py    # Anfragen an api.exchangerate.host
├── database.py       # SQLite: Nutzer, Reisen, Ausgaben
├── keyboards.py      # Inline-Tastaturen
├── countries.py      # Wörterbuch „Land → Währungscode"
├── requirements.txt  # Python-Abhängigkeiten
└── .env              # Schlüssel (nicht in git einchecken!)
```

---

## Installation und Start

### 1. Virtuelle Umgebung anlegen

```bash
python -m venv venv
```

Aktivieren:
- **Windows:** `venv\Scripts\activate`
- **Linux / macOS:** `source venv/bin/activate`

### 2. Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 3. `.env` einrichten

Im Projektstamm eine Datei `.env` anlegen:

```
TELEGRAM_BOT_TOKEN=token_von_BotFather
API_KEY=schluessel_von_exchangerate.host
```

Woher die Schlüssel kommen:
- `TELEGRAM_BOT_TOKEN` – von [@BotFather](https://t.me/BotFather) in Telegram
- `API_KEY` – auf [exchangerate.host](https://exchangerate.host) nach der Registrierung (kostenloser Tarif)

### 4. Starten

```bash
python bot.py
```

---

## Technologien

- **Python 3.10+**
- [pyTelegramBotAPI](https://github.com/eternnoir/pyTelegramBotAPI) – Anbindung an Telegram
- **SQLite** (integriertes Modul `sqlite3`) – Datenspeicherung
- **exchangerate.host API** – Wechselkurse in Echtzeit
- **python-dotenv** – Umgebungsvariablen

---

## Unterstützte Länder (Auszug)

Russland, USA, Deutschland, Frankreich, Italien, Spanien, Großbritannien, China, Japan, Südkorea, Thailand, Türkei, VAE, Indien, Australien, Kanada, Brasilien, Ägypten, Georgien, Kasachstan und viele weitere.
Die vollständige Liste steht in [countries.py](countries.py). Ländernamen werden auf Russisch eingegeben.
