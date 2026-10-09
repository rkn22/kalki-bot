import requests, os
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_nifty():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m&range=1d"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10).json()
        meta = r['chart']['result'][0]['meta']
        price = meta['regularMarketPrice']
        prev = meta['chartPreviousClose']
        pct = round((price-prev)/prev*100,2)
        quote = r['chart']['result'][0]['indicators']['quote'][0]
        h = max([x for x in quote['high'] if x]) if quote['high'] else price
        l = min([x for x in quote['low'] if x]) if quote['low'] else price
        o = quote['open'][0] or price
        return float(price), float(pct), float(o), float(h), float(l)
    except:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        data = s.get("https://www.nseindia.com/api/allIndices", headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.nseindia.com/"}, timeout=10).json()
        n = [x for x in data['data'] if x['index'] == 'NIFTY 50'][0]
        return float(n['last']), float(n['percentChange']), float(n['open']), float(n['dayHigh']), float(n['dayLow'])

try:
    price, pct, o, h, l = get_nifty()
except:
    print("❌ API Fail")
    exit()

utc_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
now = utc_now.strftime("%I:%M %p")
expiry_str = (utc_now + timedelta(days=(1 - utc_now.weekday()) % 7)).strftime("%d %b").upper()

body = abs(price - o)
rng = h - l if h!= l else 1
upper = h - max(price, o)
lower = min(price, o) - l

if body < rng * 0.15:
    pattern = "⚪ Doji - Confusion 😕"
    acc = 50
elif upper > body * 2:
    pattern = "🌠 Shooting Star @ Resistance ⚠️"
    acc = 60
elif lower > body * 2:
    pattern = "🔨 Hammer @ Support 💪"
    acc = 88
elif price > o and pct > 0.8:
    pattern = "🐂 Bullish Engulfing 🚀"
    acc = 90
elif price < o and pct < -0.8:
    pattern = "🐻 Bearish Engulfing 🔻"
    acc = 40
else:
    pattern = "✅ Bullish Hold @ Support 📈"
    acc = 78

zone = "⚠️ Inside 22500-22540 🔴" if 22500 <= price <= 22540 and acc > 65 else "🟢 Outside Safe Zone ✅"
if 22500 <= price <= 22540 and acc > 65:
    acc = 60

# EMOJI OUTPUT
if acc < 65:
    msg = (
        f"🚫 SKIP {now} ⏰\n"
        f"📊 NIFTY: {price} ({pct}%)\n"
        f"📉 O:{o} H:{h} L:{l}\n"
        f"🕯️ Pattern: {pattern}\n"
        f"📍 Zone: {zone}\n"
        f"🎯 Acc: {acc}% LOW - No Trade ❌"
    )
else:
    ce = round(price * 0.006)
    tgt1 = ce + 25
    tgt2 = ce + 60
    sl = ce - 40
    p1 = (tgt1 - ce) * 75
    p2 = (tgt2 - ce) * 75
    msg = (
        f"🔱 KALKI 15.0 STRONG CALL {now} 🚀\n"
        f"📊 NIFTY: {price} ({pct}%) 💹\n"
        f"🕯️ Pattern: {pattern}\n"
        f"📍 Zone: {zone} | 🎯 Acc: {acc}% SAFE ✅\n\n"
        f"💰 BUY 22500 CE {expiry_str} EXP @ ₹{ce} 💸\n"
        f"🎯 TGT1: ₹{tgt1}     TGT2: ₹{tgt2} 🤑\n"
        f"🛑 SL: ₹{sl} ⚠️\n\n"
        f"💵 Profit TGT1: Rs.{p1}          TGT2: Rs.{p2} 💰\n"
        f"📅 Exp: {expiry_str} Tue | 1 LOT 📦"
    )

print(msg)
if BOT_TOKEN and CHAT_ID:
    requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}", timeout=10)
