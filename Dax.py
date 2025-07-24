try:
    import tkinter as tk
except ImportError:
    print("❌ tkinter ist nicht installiert.")
    exit(1)

import threading
import time
from datetime import datetime
import yfinance as yf
from strategy_fvg_xdax_l_full_extended import evaluate_fvg_strategy_with_result, run_with_monitoring
from telegram_notifier import send_telegram_signal, evaluate_pending_signals
import os    

def get_real_dax():
    try:
        df = yf.download("^GDAXI", period="1d", interval="60m")
        if df.empty:
            return None
        return df["Close"].iloc[-1].item()
    except Exception:
        return None

class DAXFVGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📈 DAX FVG Bot – Live-Signale & Überwachung")
        self.root.geometry("800x600")

        self.output = tk.Text(root, wrap=tk.WORD, height=30)
        self.output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.start_button = tk.Button(root, text="🟢 Live-Modus starten", command=self.start_monitoring)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="🔴 Live-Modus stoppen", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.running = False
        self.last_sent_time = None

    def log(self, text):
        now = datetime.now().strftime('%H:%M:%S')
        self.output.insert(tk.END, f"[{now}] {text}\n")
        self.output.see(tk.END)

    def start_monitoring(self):
        if not self.running:
            self.running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.log("🔄 Starte Live-FVG-Scan und Überwachung...")
            threading.Thread(target=self.monitor_loop).start()

    def stop_monitoring(self):
        self.running = False
        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.log("🛑 Überwachung gestoppt.")

    def monitor_loop(self):
        while self.running:
            try:
                self.log("🔍 Suche nach neuen FVG-Signalen...")
                result = evaluate_fvg_strategy_with_result()

                if result and (self.last_sent_time is None or result["zeit"] != self.last_sent_time):
                    self.last_sent_time = result["zeit"]
                    self.log(f"📈 Neues Signal: {result['typ'].upper()} @ {result['entry']:.2f}")
                    self.log(f"   SL: {result['sl']:.2f} | TP: {result['tp']:.2f} | Zeit: {result['zeit'].strftime('%H:%M')}")

                    real_dax = get_real_dax()
                    if real_dax is not None:
                        evaluate_pending_signals(real_dax)
                        factor = float(real_dax) / float(result["entry"])
                        gdaxi_entry = float(result["entry"]) * factor
                        gdaxi_sl = float(result["sl"]) * factor
                        gdaxi_tp = float(result["tp"]) * factor

                        sl_percent = abs(gdaxi_entry - gdaxi_sl) / gdaxi_entry * 100
                        tp_percent = abs(gdaxi_tp - gdaxi_entry) / gdaxi_entry * 100
                        hebel = 15
                        sl_zertifikat = sl_percent * hebel
                        tp_zertifikat = tp_percent * hebel

                        self.log(f"📊 Realtime DAX-Kurs (GDAXI): {real_dax:.2f}")
                        self.log(f"📤 Telegram-Signal (GDAXI umgerechnet): Entry={gdaxi_entry:.2f}, SL={gdaxi_sl:.2f}, TP={gdaxi_tp:.2f}")
                        self.log(f"📊 Knockout-Risiko: 🔻 SL: {sl_zertifikat:.2f}% | 🔺 TP: {tp_zertifikat:.2f}% (bei Hebel 15)")

                        send_telegram_signal(gdaxi_entry, gdaxi_sl, gdaxi_tp, result["typ"], result["zeit"])
                    else:
                        self.log("⚠️ Kein GDAXI verfügbar – sende XDAX-Signal.")
                        send_telegram_signal(result["entry"], result["sl"], result["tp"], result["typ"], result["zeit"])
                else:
                    self.log("ℹ️ Kein neues Setup erkannt – kein Signal gesendet.")

                self.log("📡 Überprüfe aktive Trades...")
                run_with_monitoring()
                self.log("🧠 Überwachung abgeschlossen.")

            except Exception as e:
                self.log(f"❌ Fehler: {e}")
            time.sleep(130)

def run_gui():
    root = tk.Tk()
    app = DAXFVGApp(root)
    root.mainloop()

import os

def shutdown_app():
    print("🛑 Automatischer Shutdown nach 60 Sekunden aktiviert.")
    os._exit(0)

if __name__ == "__main__":
    # Start je nach Umgebung
    if os.environ.get("DISPLAY", "") == "":
        print("⚠️ Kein DISPLAY gefunden – GUI wird übersprungen.")
        from strategy_fvg_xdax_l_full_extended import get_dax_etf_xdax as get_dax_etf_xdax_once, evaluate_fvg_strategy
        df = get_dax_etf_xdax_once()
        evaluate_fvg_strategy()
        run_with_monitoring(df)
        time.sleep(60)
        shutdown_app()
    else:
        # Starte GUI mit Timer im Hintergrund
        def start_gui_with_timeout():
            time.sleep(60)
            shutdown_app()

        threading.Thread(target=start_gui_with_timeout, daemon=True).start()
        run_gui()
