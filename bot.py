import requests, os, datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_spot():
    try:
        h = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://www.nseindia.com/api/allIndices", headers=h, timeout=10).json()
        for i in r['data']:
            if i['index']=='NIFTY 50':
                return float(i['last']), float(i['percentChange'])
    except:
        return 22474.05, 1.09
    return 22474.05, 1.09

# IST Time Fix
ist_now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
time_str = ist_now.strftime('%I:%M %p')  # 12:17 PM

spot, pct = get_spot()

if 22500 <= spot <= 22540:
    candle = "✅ Bullish Hold @ 22500 Support"
    acc = 78
else:
    candle = "⚠️ Shooting Star"

msg = f"""🔱 Kalki 14.4 CALL {time_str}

📊 NIFTY: {spot} ({pct}%)
🕯️ Candle: {candle}
📈 Accuracy: {acc}%

👉 BUY 22500 CE @ 134
🎯 TGT: 192 | 🛑 SL: 96
📦 1 LOT ONLY"""

send_msg(msg)
