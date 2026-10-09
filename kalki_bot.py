import requests, os, pytz, time
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(text):
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id":CHAT_ID, "text":text}, timeout=15)

def get_expiry():
    today=datetime.now(pytz.timezone('Asia/Kolkata')).date()
    # Thursday expiry fix
    days_ahead = (3 - today.weekday()) % 7
    if days_ahead == 0:
        exp = today
    else:
        exp = today + timedelta(days=days_ahead)
    return exp.strftime("%d %b (%a)")

def get_pcr(sym):
    for attempt in range(3): # 3 thara try kariba
        try:
            s=requests.Session()
            h={
                "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept":"application/json, text/plain, */*",
                "Referer":"https://www.nseindia.com/option-chain",
                "Accept-Language":"en-US,en;q=0.9"
            }
            s.get("https://www.nseindia.com", headers=h, timeout=15)
            time.sleep(2)
            r=s.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={sym}", headers=h, timeout=15).json()
            spot=float(r['records']['underlyingValue'])
            d=r['records']['data']; ce=pe=0
            for i in d:
                if 'CE' in i and i['CE']: ce+=i['CE'].get('openInterest',0)
                if 'PE' in i and i['PE']: pe+=i['PE'].get('openInterest',0)
            pcr=round(pe/ce,2) if ce else 1.0
            return {"ltp":spot,"pcr":pcr}
        except Exception as e:
            print(f"Attempt {attempt+1} fail for {sym}: {e}")
            time.sleep(3)
    return None

def get_accuracy(pcr):
    if pcr >= 1.25: return 90, "🔥🔥 ULTRA HIGH"
    elif pcr >= 1.15: return 85, "🔥 HIGH"
    elif pcr >= 1.10: return 80, "✅ GOOD - TRADE"
    elif pcr <= 0.75: return 90, "🔥🔥 ULTRA HIGH"
    elif pcr <= 0.85: return 85, "🔥 HIGH"
    elif pcr <= 0.90: return 80, "✅ GOOD - TRADE"
    elif pcr >= 1.05 or pcr <= 0.95: return 60, "⚠️ LOW - WAIT"
    else: return 50, "❌ NO TRADE"

def calc_levels(ltp, pcr, is_bank):
    sl_pts = 80 if is_bank else 40
    t1_pts = 150 if is_bank else 80
    t2_pts = 250 if is_bank else 120
    t3_pts = 350 if is_bank else 180
    if pcr > 1.05:
        sig="🚀 BUY"; trend="BULLISH"; sl=ltp-sl_pts; t1=ltp+t1_pts; t2=ltp+t2_pts; t3=ltp+t3_pts; remark="TRADE NOW" if get_accuracy(pcr)[0]>=80 else "WAIT"
    elif pcr < 0.95:
        sig="🔻 SELL"; trend="BEARISH"; sl=ltp+sl_pts; t1=ltp-t1_pts; t2=ltp-t2_pts; t3=ltp-t3_pts; remark="TRADE NOW" if get_accuracy(pcr)[0]>=80 else "WAIT"
    else:
        sig="⚠️ WAIT"; trend="SIDEWAYS"; sl=0; t1=t2=t3=0; remark="NO TRADE"
    return sig, trend, sl, t1, t2, t3, remark, sl_pts

ist=pytz.timezone('Asia/Kolkata')
now=datetime.now(ist)
ts=now.strftime("%d %b %I:%M %p")
expiry=get_expiry()

# Market time check - 9:15 AM to 3:45 PM only
if now.weekday()>=5:
    print("Weekend skip")
    exit()
if now.hour < 9 or (now.hour==9 and now.minute<15) or now.hour >=16:
    # Ebe market bandh - msg patha nahin, kebala log
    print(f"Market closed at {ts} - Skip NSE Busy")
    exit()

nf=get_pcr("NIFTY"); bn=get_pcr("BANKNIFTY")
if not nf or not bn:
    send_msg(f"🔱 KALKI V14.1 ⏰ {ts}\nExpiry:{expiry}\n⚠️ NSE Busy - Next 15min re try kariba\nMarket 9:15 AM ru khuliba")
    exit()

n_acc, n_tag = get_accuracy(nf['pcr'])
b_acc, b_tag = get_accuracy(bn['pcr'])
n_sig, n_trend, n_sl, n_t1, n_t2, n_t3, n_remark, n_sl_pts = calc_levels(nf['ltp'], nf['pcr'], False)
b_sig, b_trend, b_sl, b_t1, b_t2, b_t3, b_remark, b_sl_pts = calc_levels(bn['ltp'], bn['pcr'], True)

msg=f"""🔱 KALKI V14.1 + ACCURACY ⏰ {ts}
🕐 EXPIRY: {expiry}

=== NIFTY ===
💹 LTP: {nf['ltp']}
📊 PCR: {nf['pcr']} {n_trend}
🎯 ACCURACY: {n_acc}% {n_tag}
{n_sig} | {n_remark}
💰 ENTRY: {nf['ltp']} (LTP)
🛑 SL: {n_sl} (-{n_sl_pts})
🎯 T1: {n_t1} | T2: {n_t2} | T3: {n_t3}

=== BANKNIFTY ===
💹 LTP: {bn['ltp']}
📊 PCR: {bn['pcr']} {b_trend}
🎯 ACCURACY: {b_acc}% {b_tag}
{b_sig} | {b_remark}
💰 ENTRY: {bn['ltp']} (LTP)
🛑 SL: {b_sl} (-{b_sl_pts})
🎯 T1: {b_t1} | T2: {b_t2} | T3: {b_t3}

🔥 FINAL: {b_sig} {b_remark} @ {bn['ltp']} ({b_acc}%)
NIFTY: {n_acc}% | BANK: {b_acc}%
"""
send_msg(msg)
print("Sent V14.1")
