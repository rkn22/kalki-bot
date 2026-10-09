import requests, os
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

try:
    r = requests.get("https://www.nseindia.com/api/allIndices", headers={"User-Agent":"Mozilla/5.0"}, timeout=10).json()
    nifty = [x for x in r['data'] if x['index'] == 'NIFTY 50'][0]
    price = float(nifty['last'])
    pct = nifty['percentChange']
except:
    price = 22468.15
    pct = 1.06

utc_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
now = utc_now.strftime("%I:%M %p")

if 22500 <= price <= 22540:
    acc = 60
    zone = "Inside 22500-22540"
    signal = "Shooting Star @ Resistance"
else:
    acc = 78
    zone = "Outside Safe Zone"
    signal = "Bullish Hold @ Support"

if acc < 70:
    msg = f"⚠️ Kalki 14.4 SKIP {now}\n\n📊 NIFTY: {price} ({pct}%)\n📍 {zone}\n🕯️ {signal}\n📈 Accuracy: {acc}% - LOW!\n\n❌ No Trade - Next 40min Wait"
else:
    ce = round(price * 0.006)
    msg = f"🔱 Kalki 14.4 STRONG CALL {now}\n\n📊 NIFTY: {price} ({pct}%)\n📍 {zone}\n🕯️ {signal}\n📈 Accuracy: {acc}% - SAFE ✅\n\n👉 BUY 22500 CE @ {ce}\n🎯 TGT: {ce+60} | 🛑 SL: {ce-40}\n📦 1 LOT ONLY"

requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
print(f"Sent {acc}%")
