import requests
from datetime import datetime

# Telegram-Konfiguration
BOT_TOKEN = '8170146997:AAE5P3SIi_L06iYkke35s7A1EP77KftkWVI'
CHAT_ID = '1596720374'

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=data)
    if response.ok:
        print("✅ Nachricht erfolgreich gesendet.")
    else:
        print("❌ Fehler beim Senden:", response.text)

if __name__ == "__main__":
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_telegram_message(f"📡 *Testsignal aktiviert*\n🕒 {now}")
