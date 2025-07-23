import time
import os
import signal
import yfinance as yf
from datetime import datetime
from strategy_fvg_xdax_l_full_extended import evaluate_fvg_strategy_with_result, run_with_monitoring
from telegram_notifier import send_telegram_signal

def get_real_dax():
    try:
        df = yf.download("^GDAXI", period="1d", interval="60m")
        if df.empty:
            return None
        return df["Close"].iloc[-1].item()
    except Exception:
        return None

def send_start_message():
    try:
        send_telegram_signal(0, 0, 0, "info", "🚀 DAX-FVG-Bot gestartet – 1-Minuten-Lauf.")
    except Exception as e:
        print(f"⚠️ Startmeldung konnte nicht gesendet werden: {e}")

def run_once():
    print("🔍 Suche nach FVG...")
    result = evaluate_fvg_strategy_with_result()

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
    run_with_monitoring()

def shutdown():
    print("⏱️ 60 Sekunden vorbei – beende das Programm jetzt.")
    os.kill(os.getpid(), signal.SIGTERM)

if __name__ == "__main__":
    print("🚀 Starte Headless DAX-FVG-Bot...")
    send_start_message()
    run_once()
    time.sleep(860)
    shutdown()
