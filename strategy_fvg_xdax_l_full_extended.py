import time
import os
import signal
import yfinance as yf
from datetime import datetime
from telegram_notifier import send_telegram_signal  # du brauchst diese Datei mit dieser Funktion

# ✅ Starte-Info an Telegram senden
def send_start_message():
    try:
        send_telegram_signal(0, 0, 0, "info", "🚀 DAX-FVG-Bot gestartet – einmalige Analyse läuft.")
    except Exception as e:
        print(f"⚠️ Konnte Startmeldung nicht senden: {e}")

# 📊 Holt XDAX.L-Daten (1-Tageszeitraum, 60m-Kerzen)
def get_dax_data():
    try:
        ticker = yf.Ticker("XDAX.L")
        df = ticker.history(period="1d", interval="60m")
        if df.empty:
            print("⚠️ Keine Daten von XDAX.L erhalten.")
            return None
        print(f"📊 {len(df)} Kerzen empfangen ({datetime.now().strftime('%H:%M:%S')})")
        return df[['Open', 'High', 'Low', 'Close']].between_time("08:00", "17:00")
    except Exception as e:
        print("❌ Fehler beim Abrufen der Daten:", e)
        return None

# 🔍 FVG-Logik
def detect_fvg(df):
    fvg_rows = []
    for i in range(1, len(df)-1):
        prev = df.iloc[i - 1]
        next_ = df.iloc[i + 1]
        if prev['High'] < next_['Low']:
            fvg_rows.append((i, 'bullish', prev['High'], next_['Low']))
        elif prev['Low'] > next_['High']:
            fvg_rows.append((i, 'bearish', next_['High'], prev['Low']))
    return fvg_rows

# 🔁 Einmalige Strategieauswertung
def run_once():
    df = get_dax_data()
    if df is None or df.empty:
        print("⛔ Abbruch: Keine Daten verfügbar.")
        return

    fvg_list = detect_fvg(df)
    if not fvg_list:
        print("🔍 Keine Fair Value Gaps gefunden.")
        return

    print(f"✅ {len(fvg_list)} FVGs erkannt.")
    for i, typ, fvg_low, fvg_high in fvg_list:
        if i + 1 >= len(df): continue
        entry = df.iloc[i + 1]['Close']
        sl = fvg_low if typ == 'bullish' else fvg_high
        tp = entry + 2 * abs(entry - sl) if typ == 'bullish' else entry - 2 * abs(entry - sl)
        zeit = df.index[i + 1]
        print(f"📤 {typ.upper()} FVG @ {zeit}: Entry={entry:.2f}, SL={sl:.2f}, TP={tp:.2f}")
        send_telegram_signal(entry, sl, tp, typ, zeit)

# ⏱️ 1-Minuten-Shutdown
def shutdown():
    print("⏱️ 60 Sekunden vorbei – beende das Programm.")
    os.kill(os.getpid(), signal.SIGTERM)

# ▶️ Main-Block
if __name__ == "__main__":
    send_start_message()
    run_once()
    time.sleep(60)
    shutdown()
