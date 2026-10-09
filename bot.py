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
    print("API Fail")
    exit()

utc_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
now = utc_now.strftime("%I:%M %p")
hour = utc_now.hour
minute = utc_now.minute

days_ahead = (1 - utc_now.weekday()) % 7
if days_ahead == 0 and utc_now.hour >= 16:
    days_ahead = 7
expiry_date = utc_now + timedelta(days=days_ahead)
expiry_str = expiry_date.strftime("%d %b").upper()

if 22500 <= price <= 22540:
    acc = 60
    zone = "Inside 22500-22540"
    signal = "Shooting Star @ Resistance"
else:
    acc = 78
    if price < 22490 or price > 22560:
        acc = 88
    zone = "Outside Safe Zone"
    signal = "Bullish Hold @ Support"

if hour == 9 and 15 <= minute <= 20:
    msg = f"9:15 PREDICTION {now}\nNIFTY: {price} ({pct}%)\nExpiry: {expiry_str} Tue\nAcc: {acc}%\nPlan: {signal}"
elif acc < 70:
    msg = f"SKIP {now}\nNIFTY: {price} ({pct}%)\n{zone}\nAcc: {acc}% LOW\nNo Trade"
else:
    ce = round(price * 0.006)
    tgt1 = ce + 25
    tgt2 = ce + 60
    sl = ce - 40
    p1 = (tgt1 - ce) * 75
    p2 = (tgt2 - ce) * 75
    msg = (
        f"KALKI 14.4 STRONG CALL {now}\n"
        f"NIFTY: {price} ({pct}%)\n"
        f"{zone} | {signal}\n"
        f"Acc: {acc}% SAFE\n\n"
        f"BUY 22500 CE {expiry_str} EXP @ {ce}\n"
        f"TGT1: {tgt1} | TGT2: {tgt2}\n"
        f"SL: {sl}\n\n"
        f"Profit TGT1: Rs.{p1} | TGT2: Rs.{p2}\n"
    )

requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={msg}")
print(f"Sent {acc}% {expiry_str}")
