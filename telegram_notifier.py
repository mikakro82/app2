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
CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID")

LOG_FILE = "signal_log.json"


def send_telegram_message(message: str):
    """Sendet eine Telegram-Nachricht."""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ TELEGRAM_TOKEN oder TELEGRAM_CHAT_ID fehlt.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id":    CHAT_ID,
        "text":       message,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram-Fehler:", e)


def send_telegram_signal(entry, sl, tp, direction, time):
    """
    Formatiert ein FVG-Signal und sendet es an Telegram.
    Signale mit entry == 0 werden still übersprungen.
    """
    # Wenn kein valider Entry, nichts tun
    if entry == 0:
        return

    try:
        risk     = abs(entry - sl)
        reward   = abs(tp    - entry)
        rr_ratio = round(reward / risk, 2)
        sl_pct   = round((risk   / entry) * 100, 2)
        tp_pct   = round((reward / entry) * 100, 2)
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
    """Speichert ein Signal im lokalen JSON-Log."""
    result = {
        "time":         time.isoformat() if hasattr(time, "isoformat") else str(time),
        "entry":        entry,
        "sl":           sl,
        "tp":           tp,
        "status":       "pending",
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
    """Prüft offene Signale auf TP/SL und sendet bei Erreichen ein Update."""
    if not os.path.exists(LOG_FILE):
        return

    # Log einlesen
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    changed = False
    for signal in data:
        if signal["status"] == "pending":
            if price_now >= signal["tp"]:
                signal["status"]      = "take_profit"
                signal["triggered_at"] = datetime.now().isoformat()
                send_telegram_message(
                    f"✅ *Take Profit erreicht!*\nEntry: `{signal['entry']}` → TP: `{signal['tp']}`"
                )
                changed = True
            elif price_now <= signal["sl"]:
                signal["status"]      = "stop_loss"
                signal["triggered_at"] = datetime.now().isoformat()
                send_telegram_message(
                    f"🛑 *Stop Loss erreicht!*\nEntry: `{signal['entry']}` → SL: `{signal['sl']}`"
                )
                changed = True

    if changed:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def send_daily_summary():
    """Sendet eine tägliche Übersicht der TP/SL-Statistik."""
    if not os.path.exists(LOG_FILE):
        send_telegram_message("📊 Keine Signale für Tagesauswertung gefunden.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    now = datetime.now()
    stats = {
        "day":   {"tp": 0, "sl": 0},
        "week":  {"tp": 0, "sl": 0},
        "month": {"tp": 0, "sl": 0},
        "year":  {"tp": 0, "sl": 0},
    }

    for s in data:
        if s["status"] in ["take_profit", "stop_loss"]:
            t = datetime.fromisoformat(s["triggered_at"])
            for k, delta in [
                ("day",   timedelta(days=1)),
                ("week",  timedelta(weeks=1)),
                ("month", timedelta(days=31)),
                ("year",  timedelta(days=365)),
            ]:
                if now - t <= delta:
                    stats[k]["tp" if s["status"]=="take_profit" else "sl"] += 1

    summary = (
        f"📈 *Tagesauswertung {now.strftime('%d.%m.%Y')}*\n"
        f"📅 Heute: ✅ {stats['day']['tp']} TP | 🛑 {stats['day']['sl']} SL\n"
        f"🗓️ Woche: ✅ {stats['week']['tp']} TP | 🛑 {stats['week']['sl']} SL\n"
        f"📆 Monat: ✅ {stats['month']['tp']} TP | 🛑 {stats['month']['sl']} SL\n"
        f"📊 Jahr: ✅ {stats['year']['tp']} TP | 🛑 {stats['year']['sl']} SL"
    )
    send_telegram_message(summary)
