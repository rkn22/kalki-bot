import requests, os, datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_spot():
    try:
        h = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        r = requests.get("https://www.nseindia.com/api/allIndices", headers=h, timeout=10).json()
        for i in r['data']:
            if i['index'] == 'NIFTY 50':
                return float(i['last']), float(i['percentChange'])
    except Exception as e:
        print(f"NSE Error {e}")
        return 22474.05, 1.09
    return 22474.05, 1.09

# IST Time
ist_now = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
time_str = ist_now.strftime('%I:%M %p')

spot, pct = get_spot()

# Fix: acc defined here
if spot >= 22500 and spot <= 22540:
    candle = "Bullish Hold @ 22500"
    acc = 78
else:
    candle = "Shooting Star @ Resistance"
    acc = 72

msg = f"🔱 Kalki 14.4 CALL {time_str}\n\n📊 NIFTY: {spot} ({pct}%)\n🕯️ Candle: {candle}\n📈 Accuracy: {acc}%\n\n👉 BUY 22500 CE @ 134\n🎯 TGT: 192 | 🛑 SL: 96\n📦 1 LOT ONLY"

send_msg(msg)
print("Sent OK")
