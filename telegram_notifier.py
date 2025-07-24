import requests
from datetime import datetime, timedelta
import json
import os

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
        f"🕒 Zeit: {time.strftime('%Y-%m-%d %H:%M')}\n"
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
    for signal in data:
        if signal["status"] != "pending":
            continue
        entry = signal["entry"]
        sl = signal["sl"]
        tp = signal["tp"]
        try:
            signal_time = datetime.fromisoformat(signal["time"])
            now = datetime.now(signal_time.tzinfo)  # gleiche Zeitzone wie das Signal
        except:
            continue
        if now - signal_time < timedelta(minutes=1):
            continue  # zu frisch

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
