import requests
from datetime import datetime, timedelta, timezone
import json
import os

BOT_TOKEN = "8170146997:AAE5P3SIi_L06iYkke35s7A1EP77KftkWVI"
CHAT_ID = "1596720374"

LOG_FILE = "signal_log.json"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    # Entfernt ungültige Unicode-Zeichen wie kaputte Emojis
    clean_message = message.encode('utf-8', errors='ignore').decode('utf-8')
    data = {
        "chat_id": CHAT_ID,
        "text": clean_message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Telegram Error:", e)

def save_signal_log(time, entry, sl, tp, quelle):
    result = {
        "time": time.isoformat(),
        "entry": round(entry, 2),
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "quelle": quelle,
        "status": "pending",
        "triggered_at": None
    }

    data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = []

    for s in data:
        if (
            abs(s["entry"] - result["entry"]) < 0.01 and
            abs(s["sl"] - result["sl"]) < 0.01 and
            abs(s["tp"] - result["tp"]) < 0.01 and
            s["time"][:16] == result["time"][:16] and
            s.get("quelle") == result["quelle"]
        ):
            return  # Duplikat – nicht speichern

    data.append(result)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def send_telegram_signal(entry, sl, tp, direction, time, quelle="xdax"):
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
        f"📍 *Quelle*: {quelle.upper()}\n"
        f"🕒 Zeit: {time}\n"
        f"🎯 Entry: `{entry:.2f}`\n"
        f"🛡️ SL: `{sl:.2f}` ({sl_pct}%)\n"
        f"🏁 TP: `{tp:.2f}` ({tp_pct}%)\n"
        f"📐 CRV: `{rr_ratio}:1`"
    )
    save_signal_log(time, entry, sl, tp, quelle)
    send_telegram_message(message)

def evaluate_pending_signals(price_now):
    if not os.path.exists(LOG_FILE):
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except:
            data = []

    changed = False
    now = datetime.now(timezone.utc)
    for signal in data:
        if signal["status"] != "pending":
            continue

        try:
            signal_time = datetime.fromisoformat(signal["time"])
            # sicherstellen, dass beide datetime-Objekte Zeitzonen enthalten
            if signal_time.tzinfo is None:
                signal_time = signal_time.replace(tzinfo=timezone.utc)
        except Exception:
            continue

        if signal_time > now - timedelta(minutes=1):
            continue  # noch zu frisch – nicht bewerten

        entry = signal["entry"]
        sl = signal["sl"]
        tp = signal["tp"]
        if price_now >= tp:
            signal["status"] = "take_profit"
            signal["triggered_at"] = now.isoformat()
            send_telegram_message(f"✅ *Take Profit erreicht!* Entry: `{entry}` → TP: `{tp}`")
            changed = True
        elif price_now <= sl:
            signal["status"] = "stop_loss"
            signal["triggered_at"] = now.isoformat()
            send_telegram_message(f"🛑 *Stop Loss erreicht!* Entry: `{entry}` → SL: `{sl}`")
            changed = True

    if changed:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def send_daily_summary():
    if not os.path.exists(LOG_FILE):
        send_telegram_message("📊 Keine Signal-Daten für die Tagesauswertung verfügbar.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    now = datetime.now()
    stats = {
        "day": {"tp": 0, "sl": 0},
        "week": {"tp": 0, "sl": 0},
        "month": {"tp": 0, "sl": 0},
        "year": {"tp": 0, "sl": 0},
    }

    for s in data:
        if s["status"] in ["take_profit", "stop_loss"] and s["triggered_at"]:
            t = datetime.fromisoformat(s["triggered_at"])
            for k, delta in [
                ("day", timedelta(days=1)),
                ("week", timedelta(weeks=1)),
                ("month", timedelta(days=31)),
                ("year", timedelta(days=365)),
            ]:
                if now - t <= delta:
                    stats[k]["tp" if s["status"] == "take_profit" else "sl"] += 1

    summary = (
        f"📈 *Tagesauswertung {now.strftime('%d.%m.%Y')}*\n"
        f"📅 Heute: ✅ {stats['day']['tp']} TP | 🛑 {stats['day']['sl']} SL\n"
        f"🗓️ Woche: ✅ {stats['week']['tp']} TP | 🛑 {stats['week']['sl']} SL\n"
        f"📆 Monat: ✅ {stats['month']['tp']} TP | 🛑 {stats['month']['sl']} SL\n"
        f"📊 Jahr: ✅ {stats['year']['tp']} TP | 🛑 {stats['year']['sl']} SL"
    )
    send_telegram_message(summary)
