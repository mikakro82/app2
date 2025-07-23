import time
import os
import sys
import signal
import yfinance as yf
from datetime import datetime
from strategy_fvg_xdax_l_full_extended import (
    evaluate_fvg_strategy_with_result,
    run_with_monitoring
)
from telegram_notifier import send_telegram_signal

def get_real_dax():
    try:
        df = yf.download("^GDAXI", period="1d", interval="60m")
        if df.empty:
            return None
        return df["Close"].iloc[-1].item()
    except Exception:
        return None

def get_xdax_df():
    try:
        ticker = yf.Ticker("XDAX.L")
        df = ticker.history(period="1d", interval="60m")
        if df.empty:
            print("❌ Keine XDAX.L-Daten empfangen.")
            return None
        print(f"📊 {len(df)} Kerzen empfangen von XDAX.L ({datetime.now().strftime('%H:%M:%S')})")
        return df[['Open', 'High', 'Low', 'Close']]
    except Exception as e:
        print("❌ Fehler beim Laden von XDAX.L:", e)
        return None

def send_start_message():
    try:
        send_telegram_signal(0, 0, 0, "info", "🚀 DAX-FVG-Bot gestartet – 1-Minuten-Lauf.")
    except Exception as e:
        print(f"⚠️ Startmeldung konnte nicht gesendet werden: {e}")

def run_once(df):
    print("🔍 Suche nach FVG...")
    result = evaluate_fvg_strategy_with_result(df)

    if result:
        print(f"📈 Signal gefunden: {result['typ'].upper()} @ {result['entry']:.2f}")
        real_dax = get_real_dax()

        if real_dax:
            factor = float(real_dax) / float(result["entry"])
            entry = result["entry"] * factor
            sl = result["sl"] * factor
            tp = result["tp"] * factor
            print(f"📤 Telegram (GDAXI): Entry={entry:.2f}, SL={sl:.2f}, TP={tp:.2f}")
            send_telegram_signal(entry, sl, tp, result["typ"], result["zeit"])
        else:
            print("⚠️ Kein Real-DAX – sende XDAX-Daten.")
            send_telegram_signal(result["entry"], result["sl"], result["tp"], result["typ"], result["zeit"])
    else:
        print("ℹ️ Kein FVG-Signal gefunden.")

    print("📡 Auswertung offener Signale...")
    run_with_monitoring(df)

def shutdown():
    print("⏱️ Zeit abgelaufen – Programm wird beendet.")
    sys.exit(0)

if __name__ == "__main__":
    print("🚀 Starte Headless DAX-FVG-Bot...")
    send_start_message()

    df = get_xdax_df()
    if df is not None:
        run_once(df)
    else:
        print("❌ Kein gültiger DataFrame – Abbruch.")

    time.sleep(60)  # ⏱
    shutdown()
