import requests, os, pytz
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(text):
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id":CHAT_ID, "text":text}, timeout=15)

def get_expiry():
    today=datetime.now(pytz.timezone('Asia/Kolkata')).date()
    days_ahead = 3 - today.weekday()
    if days_ahead <= 0: days_ahead += 7
    exp = today + timedelta(days=days_ahead)
    if today.weekday()==3: exp=today
    return exp.strftime("%d %b (%a)")

def get_pcr(sym):
    try:
        s=requests.Session()
        h={"User-Agent":"Mozilla/5.0","Referer":"https://www.nseindia.com/option-chain"}
        s.get("https://www.nseindia.com", headers=h, timeout=10)
        r=s.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={sym}", headers=h, timeout=10).json()
        spot=float(r['records']['underlyingValue'])
        d=r['records']['data']; ce=pe=0
        for i in d:
            if 'CE' in i and i['CE']: ce+=i['CE'].get('openInterest',0)
            if 'PE' in i and i['PE']: pe+=i['PE'].get('openInterest',0)
        pcr=round(pe/ce,2) if ce else 1.0
        return {"ltp":spot,"pcr":pcr}
    except: return None

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
        sig="🚀 BUY"; trend="BULLISH"
        sl=ltp-sl_pts; t1=ltp+t1_pts; t2=ltp+t2_pts; t3=ltp+t3_pts
        remark="TRADE NOW" if get_accuracy(pcr)[0]>=80 else "WAIT"
    elif pcr < 0.95:
        sig="🔻 SELL"; trend="BEARISH"
        sl=ltp+sl_pts; t1=ltp-t1_pts; t2=ltp-t2_pts; t3=ltp-t3_pts
        remark="TRADE NOW" if get_accuracy(pcr)[0]>=80 else "WAIT"
    else:
        sig="⚠️ WAIT"; trend="SIDEWAYS"
        sl=0; t1=t2=t3=0
        remark="NO TRADE"
    return sig, trend, sl, t1, t2, t3, remark, sl_pts

ist=pytz.timezone('Asia/Kolkata')
now=datetime.now(ist)
ts=now.strftime("%d %b %I:%M %p")
expiry=get_expiry()

if now.weekday()>=5:
    send_msg(f"🔱 KALKI V14 ⏰ {ts}\nWeekend Bandh")
    exit()

nf=get_pcr("NIFTY"); bn=get_pcr("BANKNIFTY")
if not nf or not bn:
    send_msg(f"🔱 KALKI V14 ⏰ {ts}\nExpiry:{expiry}\n⚠️ NSE Busy")
    exit()

n_acc, n_tag = get_accuracy(nf['pcr'])
b_acc, b_tag = get_accuracy(bn['pcr'])

n_sig, n_trend, n_sl, n_t1, n_t2, n_t3, n_remark, n_sl_pts = calc_levels(nf['ltp'], nf['pcr'], False)
b_sig, b_trend, b_sl, b_t1, b_t2, b_t3, b_remark, b_sl_pts = calc_levels(bn['ltp'], bn['pcr'], True)

msg=f"""🔱 KALKI V14 + ACCURACY ⏰ {ts}
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
print("Sent V14+Acc")
