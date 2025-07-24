import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from telegram_notifier import send_telegram_signal, update_signal_result, send_daily_summary

def get_dax_etf_xdax(interval='60m'):
    try:
        ticker = yf.Ticker("XDAX.L")  # Xtrackers DAX ETF an der LSE
        df     = ticker.history(period="1d", interval=interval)
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
        prev_candle = df.iloc[i-1]
        next_candle = df.iloc[i+1]
        if prev_candle['High'] < next_candle['Low']:
            fvg_rows.append((i, 'bullish', prev_candle['High'], next_candle['Low']))
        elif prev_candle['Low'] > next_candle['High']:
            fvg_rows.append((i, 'bearish', next_candle['High'], prev_candle['Low']))
    return fvg_rows

def evaluate_fvg_strategy_with_result():
    df = get_dax_etf_xdax()
    if df is None or df.empty:
        print("Keine Daten geladen.")
        return None

    # Handelszeit LSE in DE-Zeit
    df = df.between_time("08:00", "17:00")
    fvg_list = detect_fvg(df)
    if not fvg_list:
        print("Keine FVG erkannt.")
        return None

    # Neuestes FVG
    i, fvg_type, fvg_low, fvg_high = fvg_list[-1]
    if i + 1 >= len(df):
        return None

    entry_candle = df.iloc[i+1]
    entry = entry_candle["Close"]
    sl    = fvg_low if fvg_type=="bullish" else fvg_high
    tp    = entry + 2*abs(entry-sl) if fvg_type=="bullish" else entry-2*abs(entry-sl)
    zeit  = entry_candle.name.to_pydatetime()

    return {
        "entry": float(entry),
        "sl":    float(sl),
        "tp":    float(tp),
        "typ":   fvg_type,
        "zeit":  zeit
    }

def run_with_monitoring():
    df = get_dax_etf_xdax()
    if df is None or df.empty:
        print("Keine Daten empfangen.")
        return

    last_price = df['Close'].iloc[-1]
    update_signal_result(last_price)

    now = datetime.now()
    if now.strftime("%H:%M") == "17:00":
        send_daily_summary()

if __name__ == "__main__":
    evaluate_fvg_strategy_with_result()
    run_with_monitoring()
