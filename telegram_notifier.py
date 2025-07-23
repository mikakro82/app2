import requests
import os
import json
from datetime import datetime, timedelta

# Optional: .env laden für lokale Tests
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Umgebungsvariablen (GitHub Secrets oder .env)
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LOG_FILE = "signal_log.json"


def send_telegram_message(message: str):
    """Sendet eine Nachricht an Telegram."""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_TOKEN oder TELEGRAM_CHAT_ID fehlt.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram-Fehler:", e)


def send_telegram_signal(entry, sl, tp, direction, time):
    """Formatiert ein Signal und sendet es an Telegram."""
    try:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_ratio = round(reward / risk, 2)
        sl_pct = round((risk / entry) * 100, 2)
        tp_pct = round((reward / entry) * 100, 2)
    except ZeroDivisionError:
        rr_ratio = sl_pct = tp_pct = 0

    message = (
        f"📊 *FVG {direction.upper()} Signal*\n"
        f"🕒 Zeit: {time}\n"
        f"🎯 Entry: `{entry:.2f}`\n"
        f"🛡️ SL: `{sl:.2f}` ({sl_pct}%)\n"
        f"🏁 TP: `{tp:.2f}` ({tp_pct}%)\n"
        f"📐 CRV: `{rr_ratio}:1`"
    )

    save_signal_log(time, entry, sl, tp)
    send_telegram_message(message)


def save_signal_log(time, entry, sl, tp):
    """Speichert ein Signal lokal im JSON-Log."""
    result = {
        "time": time.isoformat() if hasattr(time, "isoformat") else str(time),
        "entry": entry,
        "sl": sl,
        "tp": tp,
        "status": "pending",
        "triggered_at": None,
    }

    data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    data.append(result)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def update_signal_result(price_now):
    """Prüft, ob TP oder SL erreicht wurde, und sendet Telegram-Update."""
    if not os.path.exists(LOG_FILE):
        return

    changed = False
    with open(LOG_FILE, "r", encoding="utf-8") as f:
    try:
        data = json.load(f)
    except:
        data = []
