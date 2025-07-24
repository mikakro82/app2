import yfinance as yf
import pandas as pd
from datetime import datetime
from telegram_notifier import send_telegram_signal, evaluate_pending_signals, send_daily_summary


# 📦 Globale Variable für einmalig geladene Daten
global_df = None

def get_dax_etf_xdax_once(interval='60m'):
    try:
        ticker = yf.Ticker("XDAX.L")
        df = ticker.history(period="1d", interval=interval)
        if df.empty:
            print("Keine Daten empfangen für XDAX.L.")
            return None
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {len(df)} Kerzen geladen von XDAX.L.")
        return df[['Open', 'High', 'Low', 'Close']]
    except Exception as e:
        print("Fehler beim Laden der XDAX.L Daten:", e)
        return None

def detect_fvg(df):
    fvg_rows = []
    for i in range(1, len(df)-1):
        prev_candle = df.iloc[i - 1]
        next_candle = df.iloc[i + 1]

        if prev_candle['High'] < next_candle['Low']:
            fvg_rows.append((i, 'bullish', prev_candle['High'], next_candle['Low']))
        elif prev_candle['Low'] > next_candle['High']:
            fvg_rows.append((i, 'bearish', next_candle['High'], prev_candle['Low']))
    return fvg_rows

def evaluate_fvg_strategy(df):
    if df is None or df.empty:
        print("Keine Daten geladen.")
        return

    df = df.between_time("08:00", "17:00")
    fvg_list = detect_fvg(df)

    if not fvg_list:
        print("Keine FVG erkannt.")
        return

    print(f"Gefundene FVGs ({len(fvg_list)}):")
    for i, fvg_type, fvg_low, fvg_high in fvg_list:
        if i + 1 >= len(df): continue
        entry_candle = df.iloc[i + 1]
        sl = fvg_low if fvg_type == 'bullish' else fvg_high
        tp = entry_candle['Close'] + 2 * abs(entry_candle['Close'] - sl) if fvg_type == 'bullish' else entry_candle['Close'] - 2 * abs(entry_candle['Close'] - sl)
        print(f"{fvg_type.upper()} FVG bei {entry_candle.name}: Entry={entry_candle['Close']:.2f}, SL={sl:.2f}, TP={tp:.2f}")
        send_telegram_signal(entry_candle['Close'], sl, tp, fvg_type, entry_candle.name)

def run_with_monitoring(df):
    if df is None or df.empty:
        print("Keine Daten empfangen.")
        return

    last_price = df['Close'].iloc[-1]
    update_signal_result(last_price)

    now = datetime.now()
    if now.strftime("%H:%M") == "17:00":
        send_daily_summary()

def evaluate_fvg_strategy_with_result(df):
    if df is None or df.empty:
        print("Keine Daten geladen.")
        return None

    df = df.between_time("08:00", "17:00")
    fvg_list = detect_fvg(df)

    if not fvg_list:
        print("Keine FVG erkannt.")
        return None

    i, fvg_type, fvg_low, fvg_high = fvg_list[-1]
    if i + 1 >= len(df):
        return None

    entry_candle = df.iloc[i + 1]
    entry = entry_candle["Close"]
    sl = fvg_low if fvg_type == "bullish" else fvg_high
    tp = entry + 2 * abs(entry - sl) if fvg_type == "bullish" else entry - 2 * abs(entry - sl)
    zeit = entry_candle.name.to_pydatetime()

    return {
        "entry": float(entry),
        "sl": float(sl),
        "tp": float(tp),
        "typ": fvg_type,
        "zeit": zeit
    }

if __name__ == "__main__":
    global_df = get_dax_etf_xdax_once()
    evaluate_fvg_strategy(global_df)
    run_with_monitoring(global_df)
