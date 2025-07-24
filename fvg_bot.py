from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import os
import json
import math
import requests

BOT_TOKEN = "8170146997:AAE5P3SIi_L06iYkke35s7A1EP77KftkWVI"
CHAT_ID   = "1596720374"
LOG_FILE  = "fvg_signal_log.json"

def send_telegram_signal(entry, sl, tp, direction, time):
    risk     = abs(entry - sl)
    reward   = abs(tp - entry)
    rr_ratio = round(reward / risk, 2)
    sl_pct   = round((risk / entry) * 100, 2)
    tp_pct   = round((reward / entry) * 100, 2)

    message = (
        f"📊 *FVG {direction.upper()} Setup*\n"
        f"🕒 Zeit: {time.strftime('%Y-%m-%d %H:%M')}\n"
        f"🎯 Entry: `{math.ceil(entry)}`\n"
        f"🛡️ SL: `{math.ceil(sl)}` ({sl_pct}%)\n"
        f"🏁 TP: `{math.ceil(tp)}` ({tp_pct}%)\n"
        f"📐 CRV: `{rr_ratio}:1`"
    )
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram Error:", e)

def detect_fvg(df):
    signals = []
    for i in range(1, len(df)-1):
        prev = df.iloc[i - 1]
        next_ = df.iloc[i + 1]
        if prev['High'] < next_['Low']:
            signals.append((i, 'bullish', prev['High'], next_['Low']))
        elif prev['Low'] > next_['High']:
            signals.append((i, 'bearish', next_['High'], prev['Low']))
    return signals

def load_logged_setups():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def log_new_setup(setup):
    setups = load_logged_setups()
    setups.append(setup)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(setups, f, indent=2)

def run_fvg_scan():
    now = datetime.now()
    ticker = yf.Ticker("^GDAXI")
    df_all = ticker.history(period="5d", interval="60m")[['Open', 'High', 'Low', 'Close']]
    df_all.index = df_all.index.tz_convert("Europe/Berlin")
    df_window = df_all.between_time("11:00", "14:29")

    fvg_signals = detect_fvg(df_window)
    logged = load_logged_setups()

    for i, typ, fvg_low, fvg_high in fvg_signals:
        if i+1 >= len(df_window): continue
        entry_time = df_window.index[i+1]
        entry = df_window['Close'].iloc[i+1]
        sl = fvg_low if typ == 'bullish' else fvg_high
        tp = entry + 2 * abs(entry - sl) if typ == 'bullish' else entry - 2 * abs(entry - sl)

        # Duplikate vermeiden
        if any(s['time'] == entry_time.strftime('%Y-%m-%d %H:%M') and math.ceil(s['entry']) == math.ceil(entry) for s in logged):
            continue

        send_telegram_signal(entry, sl, tp, typ, entry_time)
        log_new_setup({
            "time": entry_time.strftime('%Y-%m-%d %H:%M'),
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "type": typ
        })

run_fvg_scan()
