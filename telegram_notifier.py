def save_signal_log(time, entry, sl, tp, quelle):
    now = datetime.now().isoformat()
    result = {
        "time": time.isoformat(),
        "entry": round(entry, 2),
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "quelle": quelle,
        "status": "pending",
        "triggered_at": None
    }

    data = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = []

    for s in data:
        if (
            abs(s["entry"] - result["entry"]) < 0.01 and
            abs(s["sl"] - result["sl"]) < 0.01 and
            abs(s["tp"] - result["tp"]) < 0.01 and
            s["time"][:16] == result["time"][:16] and
            s.get("quelle") == result["quelle"]
        ):
            return  # Duplikat

    data.append(result)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def send_telegram_signal(entry, sl, tp, direction, time, quelle="xdax"):
    try:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr_ratio = round(reward / risk, 2)
        sl_pct = round((risk / entry) * 100, 2)
        tp_pct = round((reward / entry) * 100, 2)
    except ZeroDivisionError:
        rr_ratio = sl_pct = tp_pct = 0

    message = (
        f"📊 *FVG {direction.upper()} Signal*\n"
        f"📍 *Quelle*: {quelle.upper()}\n"
        f"🕒 Zeit: {time}\n"
        f"🎯 Entry: `{entry:.2f}`\n"
        f"🛡️ SL: `{sl:.2f}` ({sl_pct}%)\n"
        f"🏁 TP: `{tp:.2f}` ({tp_pct}%)\n"
        f"📐 CRV: `{rr_ratio}:1`"
    )
    save_signal_log(time, entry, sl, tp, quelle)
    send_telegram_message(message)
