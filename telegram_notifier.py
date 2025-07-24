def send_daily_summary():
    """Sendet eine tägliche Übersicht der TP/SL-Statistik."""
    if not os.path.exists(LOG_FILE):
        send_telegram_message("📊 Keine Signal-Daten für die Tagesauswertung verfügbar.")
        return

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []

    now = datetime.now()
    stats = {
        "day": {"tp": 0, "sl": 0},
        "week": {"tp": 0, "sl": 0},
        "month": {"tp": 0, "sl": 0},
        "year": {"tp": 0, "sl": 0},
    }

    for s in data:
        if s["status"] in ["take_profit", "stop_loss"] and s["triggered_at"]:
            t = datetime.fromisoformat(s["triggered_at"])
            for k, delta in [
                ("day", timedelta(days=1)),
                ("week", timedelta(weeks=1)),
                ("month", timedelta(days=31)),
                ("year", timedelta(days=365)),
            ]:
                if now - t <= delta:
                    stats[k]["tp" if s["status"] == "take_profit" else "sl"] += 1

    summary = (
        f"📈 *Tagesauswertung {now.strftime('%d.%m.%Y')}*\n"
        f"📅 Heute: ✅ {stats['day']['tp']} TP | 🛑 {stats['day']['sl']} SL\n"
        f"🗓️ Woche: ✅ {stats['week']['tp']} TP | 🛑 {stats['week']['sl']} SL\n"
        f"📆 Monat: ✅ {stats['month']['tp']} TP | 🛑 {stats['month']['sl']} SL\n"
        f"📊 Jahr: ✅ {stats['year']['tp']} TP | 🛑 {stats['year']['sl']} SL"
    )
    send_telegram_message(summary)
