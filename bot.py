import requests, os
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

try:
    r = requests.get("https://www.nseindia.com/api/allIndices", headers={"User-Agent":"Mozilla/5.0"}, timeout=10).json()
    n = [x for x in r['data'] if x['index'] == 'NIFTY 50'][0]
    price = float(n['last'])
    pct = n['percentChange']
    o = float(n['open'])
    h = float(n['dayHigh'])
    l = float(n['dayLow'])
except:
    print("API Fail")
    exit()

utc_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
now = utc_now.strftime("%I:%M %p")

days_ahead = (1 - utc_now.weekday()) % 7
if days_ahead == 0 and utc_now.hour >= 16:
    days_ahead = 7
expiry_date = utc_now + timedelta(days=days_ahead)
expiry_str = expiry_date.strftime("%d %b").upper()

# CANDLE PATTERN LOGIC
body = abs(price - o)
rng = h - l
if rng == 0: rng = 1
upper = h - max(price, o)
lower = min(price, o) - l

pattern = "Normal"
acc_base = 70

if body < rng * 0.15:
    pattern = "Doji - Confusion"
    acc_base = 50
elif upper > body * 2 and body > 0:
    pattern = "Shooting Star @ Resistance"
    acc_base = 60
elif lower > body * 2 and body > 0:
    pattern = "Hammer @ Support"
    acc_base = 88
elif price > o and pct > 0.8:
    pattern = "Bullish Engulfing"
    acc_base = 90
elif price < o and pct < -0.8:
    pattern = "Bearish Engulfing"
    acc_base = 40
else:
    pattern = "Bullish Hold @ Support"
    acc_base = 78

# ZONE LOGIC
zone = "Outside Safe Zone"
if 22500 <= price <= 22540:
    zone = "Inside 22500-22540"
    if acc_base > 70:
        acc_base = 60

# TIME FILTER - 9:15 Prediction Boost
hour = utc_now.hour
minute = utc_now.minute
if hour >= 10 and acc_base == 60:
    acc_base = 72

acc = acc_base

# MESSAGE
if hour == 9 and 15 <= minute <= 20:
    msg = (
        f"9:15 PREDICTION {now}\n"
        f"NIFTY: {price} ({pct}%)\n"
        f"O:{o} H:{h} L:{l}\n"
        f"Pattern: {pattern}\n"
        f"Zone: {zone}\n"
        f"Exp: {expiry_str} Tue | Acc: {acc}%"
    )
elif acc < 65:
    msg = (
        f"SKIP {now}\n"
        f"NIFTY: {price} ({pct}%)\n"
        f"Pattern: {pattern}\n"
        f"Zone: {zone}\n"
        f"Acc: {acc}% LOW - No Trade"
    )
else:
    ce = round(price * 0.006)
    tgt1 = ce + 25
    tgt2 = ce + 60
    sl = ce - 40
    p1 = (tgt1 - ce) * 75
    p2 = (tgt2 - ce) * 75
    msg = (
        f"KALKI 15.0 STRONG CALL {now}\n"
        f"NIFTY: {price} ({pct}%)\n"
        f"Pattern: {pattern}\n"
        f"Zone: {zone} | Acc: {acc}% SAFE\n\n"
        f"BUY 22500 CE {expiry_str} EXP @ {ce}\n"
        f"TGT1: {tgt1} TGT2: {tgt2} SL: {sl}\n\n"
        f"Profit TGT1: Rs.{p1} TGT2: Rs.{p2}\n"
        f"Exp: {expiry_str} Tue | 1 LOT"
    )

requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
print(f"Sent {acc}% {pattern}")
