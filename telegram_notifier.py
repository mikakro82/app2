import requests
from datetime import datetime, timedelta
import json
import os

BOT_TOKEN = "8170146997:AAE5P3SIi_L06iYkke35s7A1EP77KftkWVI"
CHAT_ID = "1596720374"

LOG_FILE = "signal_log.json"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
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
            return

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
        f"\ud83d\udcca *FVG {direction.upper()} Signal*\n"
        f"\ud83d\udd39 *Quelle*: {quelle.upper()}\n"
        f"\ud83d\udd52 Zeit: {time}\n"
        f"\ud83c\udfaf Entry: `{entry:.2f}`\n"
        f"\ud83d\udee1\ufe0f SL: `{sl:.2f}` ({sl_pct}%)\n"
        f"\ud83c\udfc1 TP: `{tp:.2f}` ({tp_pct}%)\n"
        f"\ud83d\udcc0 CRV: `{rr_ratio}:1`"
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
    now = datetime.now()
    for signal in data:
        if signal["status"] != "pending":
            continue

        # Ignoriere neue Signale
        if datetime.fromisoformat(signal["time"]) > now - timedelta(minutes=1):
            continue

        entry = signal["entry"]
        sl = signal["sl"]
        tp = signal["tp"]
        if price_now >= tp:
            signal["status"] = "take_profit"
            signal["triggered_at"] = now.isoformat()
            send_telegram_message(f"\u2705 *Take Profit erreicht!* Entry: `{entry}` \u2192 TP: `{tp}`")
            changed = True
        elif price_now <= sl:
            signal["status"] = "stop_loss"
            signal["triggered_at"] = now.isoformat()
            send_telegram_message(f"\ud83d\uded1 *Stop Loss erreicht!* Entry: `{entry}` \u2192 SL: `{sl}`")
            changed = True

    if changed:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def send_daily_summary():
    if not os.path.exists(LOG_FILE):
        send_telegram_message("\ud83d\udcca Keine Signal-Daten f\u00fcr die Tagesauswertung verf\u00fcgbar.")
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
        f"\ud83d\udcc8 *Tagesauswertung {now.strftime('%d.%m.%Y')}*\n"
        f"\ud83d\uddd5\ufe0f Heute: \u2705 {stats['day']['tp']} TP | \ud83d\uded1 {stats['day']['sl']} SL\n"
        f"\ud83d\uddd3\ufe0f Woche: \u2705 {stats['week']['tp']} TP | \ud83d\uded1 {stats['week']['sl']} SL\n"
        f"\ud83d\udcc6 Monat: \u2705 {stats['month']['tp']} TP | \ud83d\uded1 {stats['month']['sl']} SL\n"
        f"\ud83d\udcca Jahr: \u2705 {stats['year']['tp']} TP | \ud83d\uded1 {stats['year']['sl']} SL"
    )
    send_telegram_message(summary)
