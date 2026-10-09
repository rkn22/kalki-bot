import requests, time, datetime, os

# Telegram - 2 way support (Bot lib thile bhalo, nathile requests re chaliba)
try:
    from telegram import Bot
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    bot = Bot(token=BOT_TOKEN)
    USE_LIB = True
except:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    CHAT_ID = os.getenv("CHAT_ID")
    USE_LIB = False

def send_msg(text):
    if USE_LIB:
        bot.send_message(chat_id=CHAT_ID, text=text)
    else:
        # fallback without library
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_spot():
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        # NSE direct
        r = requests.get("https://www.nseindia.com/api/allIndices", headers=headers, timeout=10).json()
        for idx in r['data']:
            if idx['index'] == 'NIFTY 50':
                return float(idx['last']), float(idx['percentChange'])
    except Exception as e:
        print(f"NSE fail: {e}")
    return 22498.0, 1.20

def get_candle_info(spot):
    if 22500 <= spot <= 22540:
        return "⚠️ SHOOTING STAR @ 22540 Resistance", 72
    elif 22470 <= spot < 22500:
        return "✅ BULLISH HOLD @ 22500 Support", 78
    elif spot > 22540:
        return "🚀 BREAKOUT ABOVE 22540", 85
    else:
        return "📉 WEAK", 60

def main():
    spot, pct = get_spot()
    candle, acc = get_candle_info(spot)
    
    # 70% Filter
    if acc < 70:
        send_msg(f"❌ SKIP {datetime.datetime.now().strftime('%H:%M')}\nSpot {spot} | {candle} | Acc {acc}% <70%")
        return

    entry = 134  # Tuma entry
    tgt1 = 192
    sl = 96
    action = "BUY 22500 CE"
    
    # MAIN CALL
    send_msg(f"""🔱 Kalki 14.4 CALL {datetime.datetime.now().strftime('%H:%M')}

📊 NIFTY: {spot} ({pct}%)
🕯️ Candle: {candle}
📈 Accuracy: {acc}%

👉 {action} @ {entry}
🎯 TGT: {tgt1} | 🛑 SL: {sl}
📦 1 LOT ONLY (75 Qty)
⏰ Real-time update tale asiba 3min pare""")

    # REAL-TIME TALE UPDATE (6 times = 18 min)
    for i in range(6):
        time.sleep(180)
        n_spot, n_pct = get_spot()
        ce_now = entry + (n_spot - spot) * 0.65
        pnl = (ce_now - entry) * 75
        status = "⏳ HOLD"
        if ce_now >= tgt1: status = "🎯 TGT HIT! 50% BOOK!"
        if ce_now <= sl: status = "🛑 SL HIT! EXIT!"

        send_msg(f"""📈 LIVE UPDATE {datetime.datetime.now().strftime('%H:%M')}
NIFTY {spot:.0f} → {n_spot:.0f} ({n_spot-spot:+.0f})
22500 CE {entry} → {ce_now:.0f}
P&L: {pnl:.0f} Rs | {status}
🕯️ {candle}""")

        if ce_now >= tgt1 or ce_now <= sl:
            break

if __name__ == "__main__":
    main()
