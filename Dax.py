#!/usr/bin/env python3
"""
day.py – Läuft entweder als GUI oder als Headless-Service (z.B. auf GitHub Actions).
Schaltet automatisch in den Headless-Modus, wenn keine Anzeige oder tkinter fehlt.
Beendet sich selbst nach 50 Sekunden Laufzeit.
"""
import os
import sys
time
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

# Timer-Funktion zum Beenden nach 50 Sekunden
def schedule_exit(root=None):
    if root:
        # GUI: zerstöre das Fenster
        root.after(50_000, root.destroy)
    else:
        # Headless: harte Beendigung
        threading.Timer(50, lambda: os._exit(0)).start()

# ==================== Headless-Modus ====================
def headless_run():
    # Exit-Timer starten
    schedule_exit()

    now_str = datetime.now().strftime('%H:%M:%S')
    print(f"[{now_str}] 🔍 Suche nach FVG-Signal...")
    try:
        result = evaluate_fvg_strategy_with_result()
    except Exception as e:
        print(f"[{now_str}] ❌ Fehler bei Strategie-Auswertung: {e}")
        return

    if result:
        print(f"[{now_str}] 📈 Signal: {result['typ'].upper()} @ {result['entry']:.2f} | SL {result['sl']:.2f} | TP {result['tp']:.2f}")
        try:
            send_telegram_signal(result['entry'], result['sl'], result['tp'], result['typ'], result['zeit'])
            print(f"[{now_str}] 📤 Telegram-Nachricht gesendet.")
        except Exception as e:
            print(f"[{now_str}] ❌ Fehler beim Senden: {e}")
    else:
        print(f"[{now_str}] ℹ️ Kein neues Signal.")

    print(f"[{now_str}] 📡 Überprüfung aktiver Trades...")
    try:
        run_with_monitoring()
        print(f"[{now_str}] ✅ Monitoring abgeschlossen.")
    except Exception as e:
        print(f"[{now_str}] ❌ Fehler im Monitoring: {e}")

# ==================== GUI-Modus ====================
if GUI_AVAILABLE:
    class DAXFVGApp:
        def __init__(self, root):
            self.root = root
            self.root.title("📈 DAX FVG Bot – Live & Monitoring")
            self.root.geometry("800x600")

            self.output = tk.Text(root, wrap=tk.WORD, height=30)
            self.output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

            self.start_button = tk.Button(root, text="🟢 Starte Einmal-Run", command=self.run_once)
            self.start_button.pack(pady=5)

            self.running = False

        def log(self, text):
            now = datetime.now().strftime('%H:%M:%S')
            self.output.insert(tk.END, f"[{now}] {text}\n")
            self.output.see(tk.END)

        def run_once(self):
            if not self.running:
                self.running = True
                self.start_button.config(state=tk.DISABLED)
                schedule_exit(self.root)
                threading.Thread(target=self.task, daemon=True).start()

        def task(self):
            try:
                self.log("🔍 Suche nach FVG-Signal...")
                result = evaluate_fvg_strategy_with_result()

                if result:
                    self.log(f"📈 Signal: {result['typ'].upper()} @ {result['entry']:.2f}")
                    self.log(f"   SL: {result['sl']:.2f} | TP: {result['tp']:.2f} | Zeit: {result['zeit'].strftime('%H:%M')}")
                    self.log("📤 Sende Telegram-Signal...")
                    send_telegram_signal(result['entry'], result['sl'], result['tp'], result['typ'], result['zeit'])
                else:
                    self.log("ℹ️ Kein neues Signal.")

                self.log("📡 Überprüfung aktiver Trades...")
                run_with_monitoring()
                self.log("✅ Monitoring abgeschlossen.")
            except Exception as e:
                self.log(f"❌ Fehler: {e}")

    def run_gui():
        root = tk.Tk()
        app = DAXFVGApp(root)
        root.mainloop()

# ==================== Programmstart ====================
def main():
    if GUI_AVAILABLE:
        run_gui()
    else:
        headless_run()

if __name__ == "__main__":
    main()
