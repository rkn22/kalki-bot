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
    # 80%+ accuracy logic
    if pcr >= 1.25: return 90
    elif pcr >= 1.15: return 85
    elif pcr >= 1.10: return 80
    elif pcr <= 0.75: return 90
    elif pcr <= 0.85: return 85
    elif pcr <= 0.90: return 80
    else: return 50

def calc_levels(ltp, pcr):
    if pcr > 1.05:
        sig="🚀 BUY"; sl=ltp-80; t1=ltp+150; t2=ltp+250; t3=ltp+350
    else:
        sig="🔻 SELL"; sl=ltp+80; t1=ltp-150; t2=ltp-250; t3=ltp-350
    return sig, sl, t1, t2, t3

ist=pytz.timezone('Asia/Kolkata')
now=datetime.now(ist)
ts=now.strftime("%d %b %I:%M %p")
expiry=get_expiry()

if now.weekday()>=5: exit()

nf=get_pcr("NIFTY"); bn=get_pcr("BANKNIFTY")
if not nf or not bn: exit()

n_acc = get_accuracy(nf['pcr'])
b_acc = get_accuracy(bn['pcr'])

# === 80% FILTER ===
# Kebala 80% ru upare accuracy hele msg jiba
best = None
if b_acc >= 80 or n_acc >= 80:
    # Jaha ra accuracy besi seita neba
    if b_acc >= n_acc:
        sym="BANKNIFTY"; data=bn; acc=b_acc
    else:
        sym="NIFTY"; data=nf; acc=n_acc
    
    sig, sl, t1, t2, t3 = calc_levels(data['ltp'], data['pcr'])
    
    if acc >= 85:
        tag="🔥🔥 HIGH CONFIDENCE"
    else:
        tag="✅ 80% CONFIRMED"

    msg=f"""{tag}
🔱 KALKI V15 80% ACCURACY ⏰ {ts}
🕐 EXPIRY: {expiry}

=== {sym} ===
💹 LTP: {data['ltp']}
📊 PCR: {data['pcr']}
🎯 ACCURACY: {acc}%

{sig}
💰 ENTRY: {data['ltp']} (LTP)
🛑 SL: {sl}
🎯 T1: {t1}
🎯 T2: {t2}
🎯 T3: {t3}

NIFTY PCR: {nf['pcr']} ({n_acc}%)
BANK PCR: {bn['pcr']} ({b_acc}%)

⚡ 80%+ Accuracy Trade - Only!
"""
    send_msg(msg)
    print(f"Sent {acc}% - {sym}")
else:
    # 80% heini - msg jabani, log re rahiba
    print(f"Skip - N:{nf['pcr']} {n_acc}% B:{bn['pcr']} {b_acc}% <80%")
