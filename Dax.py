#!/usr/bin/env python3
"""
day.py – Läuft entweder als GUI oder als Headless-Service (z.B. auf GitHub Actions).
Wenn tkinter nicht installiert oder keine Anzeige vorhanden ist, wechselt es automatisch in den Headless-Modus.
"""
import os
import time
import threading
from datetime import datetime

# Prüfen, ob GUI möglich ist
try:
    import tkinter as tk
    # Unter Linux muss DISPLAY gesetzt sein
    if os.name != 'nt' and not os.environ.get('DISPLAY'):
        print("✨ Keine Anzeige gefunden – wechsle in den Headless-Modus.")
        GUI_AVAILABLE = False
    else:
        GUI_AVAILABLE = True
except ImportError:
    print("⚠️ tkinter nicht verfügbar – Headless-Modus aktiviert.")
    GUI_AVAILABLE = False

from strategy_fvg_xdax_l_full_extended import evaluate_fvg_strategy_with_result, run_with_monitoring
from telegram_notifier import send_telegram_signal

# ==================== Headless-Modus ====================
def headless_loop(interval=300):
    last_sent_time = None
    while True:
        now_str = datetime.now().strftime('%H:%M:%S')
        print(f"[{now_str}] 🔍 Suche nach neuen FVG-Signalen...")
        result = evaluate_fvg_strategy_with_result()

        if result and (last_sent_time is None or result['zeit'] != last_sent_time):
            last_sent_time = result['zeit']
            print(f"[{now_str}] 📈 Neues Signal: {result['typ'].upper()} @ {result['entry']:.2f} | SL {result['sl']:.2f} | TP {result['tp']:.2f}")
            send_telegram_signal(result['entry'], result['sl'], result['tp'], result['typ'], result['zeit'])
        else:
            print(f"[{now_str}] ℹ️ Kein neues Signal erkannt.")

        print(f"[{now_str}] 📡 Überprüfe aktive Trades...")
        run_with_monitoring()
        print(f"[{now_str}] ✅ Zyklus abgeschlossen. Warte {interval} Sekunden.\n")
        time.sleep(interval)

# ==================== GUI-Modus ====================
if GUI_AVAILABLE:
    class DAXFVGApp:
        def __init__(self, root):
            self.root = root
            self.root.title("📈 DAX FVG Bot – Live & Monitoring")
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
                threading.Thread(target=self.monitor_loop, daemon=True).start()

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

                    if result and (self.last_sent_time is None or result['zeit'] != self.last_sent_time):
                        self.last_sent_time = result['zeit']
                        self.log(f"📈 Neues Signal: {result['typ'].upper()} @ {result['entry']:.2f}")
                        self.log(f"   SL: {result['sl']:.2f} | TP: {result['tp']:.2f} | Zeit: {result['zeit'].strftime('%H:%M')}")
                        self.log("📤 Sende Telegram-Signal...")
                        send_telegram_signal(result['entry'], result['sl'], result['tp'], result['typ'], result['zeit'])
                    else:
                        self.log("ℹ️ Kein neues Setup erkannt – kein Signal gesendet.")

                    self.log("📡 Überprüfe aktive Trades...")
                    run_with_monitoring()
                    self.log("🧠 Überwachung abgeschlossen.")
                except Exception as e:
                    self.log(f"❌ Fehler: {e}")
                time.sleep(50)

    def run_gui():
        root = tk.Tk()
        app = DAXFVGApp(root)
        root.mainloop()

# ==================== Programmstart ====================
def main():
    if GUI_AVAILABLE:
        run_gui()
    else:
        headless_loop()

if __name__ == "__main__":
    main()



