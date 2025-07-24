#!/usr/bin/env python3
"""
day.py - Läuft als Headless-Service oder GUI. Automatische Umrechnung von XDAXI auf GDAXI für Telegram-Signale.
Beendet sich selbst nach 50 Sekunden Laufzeit.
"""
import os
import sys
import time
import threading
from datetime import datetime

# Prüfen, ob GUI möglich ist
try:
    import tkinter as tk
    if os.name != 'nt' and not os.environ.get('DISPLAY'):
        print("✨ Keine Anzeige gefunden - wechsle in den Headless-Modus.")
        GUI_AVAILABLE = False
    else:
        GUI_AVAILABLE = True
except ImportError:
    print("⚠️ tkinter nicht verfügbar - Headless-Modus aktiviert.")
    GUI_AVAILABLE = False

import yfinance as yf
from strategy_fvg_xdax_l_full_extended import evaluate_fvg_strategy_with_result, run_with_monitoring
from telegram_notifier import send_telegram_signal

# Timer zum Beenden nach 50 Sekunden
def schedule_exit(root=None):
    if root:
        root.after(50000, root.destroy)
    else:
        threading.Timer(50, lambda: os._exit(0)).start()

# Echtzeit DAX-Kurs (GDAXI) abrufen
def get_real_dax():
    try:
        df = yf.download("^GDAXI", period="1d", interval="60m")
        return df["Close"].iloc[-1]
    except Exception:
        return None

# ==================== Headless-Modus ====================
def headless_run():
    schedule_exit()
    now = datetime.now().strftime('%H:%M:%S')
    print(f"[{now}] 📈 XDAXI: {entry:.2f} | GDAXI: {float(ge):.2f}")
                    send_telegram_signal(float(ge), float(gs), float(gt), typ, zeit)
                    self.log("📤 Telegram (GDAXI) gesendet.")
                else:
                    self.log(f"⚠️ Kein GDAXI - sende XDAXI: Entry={entry:.2f}, SL={sl:.2f}, TP={tp:.2f}")
                    send_telegram_signal(entry, sl, tp, typ, zeit)
            else:
                self.log("ℹ️ Kein Signal.")

            self.log("📡 Trades prüfen...")
            try:
                run_with_monitoring()
                self.log("✅ Monitoring fertig.")
            except Exception as e:
                self.log(f"❌ Monitoring-Fehler: {e}")

    def run_gui():
        root = tk.Tk()
        app = DAXFVGApp(root)
        root.mainloop()

# Programmstart
if __name__ == '__main__':
    if GUI_AVAILABLE:
        run_gui()
    else:
        headless_run()
