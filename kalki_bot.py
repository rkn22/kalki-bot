import requests, yfinance as yf, pytz, os, time
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(text):
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id":CHAT_ID, "text":text}, timeout=10)
    except: pass

def get_pcr(sym):
    for _ in range(2):
        try:
            s=requests.Session()
            h={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36","Accept":"application/json","Referer":"https://www.nseindia.com/option-chain"}
            s.get("https://www.nseindia.com", headers=h, timeout=15)
            time.sleep(1)
            r=s.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={sym}", headers=h, timeout=15).json()
            spot=r['records']['underlyingValue']; data=r['records']['data']
            t_ce=t_pe=0
            for i in data:
                if 'CE' in i and i['CE']: t_ce+=i['CE'].get('openInterest',0)
                if 'PE' in i and i['PE']: t_pe+=i['PE'].get('openInterest',0)
            pcr=round(t_pe/t_ce,2) if t_ce else 1.0
            if pcr>1.2: tr="STRONG BULLISH"
            elif pcr>1.05: tr="BULLISH"
            elif pcr<0.8: tr="STRONG BEARISH"
            elif pcr<0.95: tr="BEARISH"
            else: tr="SIDEWAYS"
            return {"spot":spot,"pcr":pcr,"tr":tr,"t_ce":round(t_ce/1e5,1),"t_pe":round(t_pe/1e5,1)}
        except Exception as e:
            print(f"PCR err {sym} {e}")
            time.sleep(2)
    return None

def get_scalp(ysym):
    try:
        df=yf.download(ysym, period="5d", interval="5m", progress=False, auto_adjust=True)
        if len(df)<30: 
            df=yf.download(ysym, period="1d", interval="5m", progress=False, auto_adjust=True)
        if len(df)<20: return None
        close=df['Close']; 
        ema9=close.ewm(span=9).mean().iloc[-1]; ema21=close.ewm(span=21).mean().iloc[-1]
        delta=close.diff(); gain=(delta.where(delta>0,0)).rolling(14).mean(); loss=(-delta.where(delta<0,0)).rolling(14).mean()
        rs=gain/loss; rsi=100-(100/(1+rs)); rsi_val=float(rsi.iloc[-1]); price=float(close.iloc[-1])
        vwap=float((df['Close']*df['Volume']).sum()/df['Volume'].sum()) if df['Volume'].sum()>0 else price
        mult=80 if "BANK" in ysym else 40
        if price>float(ema9)>float(ema21) and rsi_val>55 and price>vwap: sig="🚀 BUY"; sl=price-mult; t1=price+mult; sc=85
        elif price<float(ema9)<float(ema21) and rsi_val<45 and price<vwap: sig="🔻 SELL"; sl=price+mult; t1=price-mult; sc=85
        else: sig="⚠️ WAIT"; sl=0; t1=0; sc=50
        return {"price":round(price,1),"sig":sig,"rsi":round(rsi_val,1),"ema9":round(float(ema9),1),"ema21":round(float(ema21),1),"vwap":round(vwap,1),"sl":round(sl,1),"t1":round(t1,1),"sc":sc}
    except Exception as e:
        print(f"Scalp err {ysym} {e}")
        return None

ist=pytz.timezone('Asia/Kolkata')
now=datetime.now(ist)
time_str=now.strftime("%d %b %I:%M %p")

# 1. MARKET CLOSED CHECK - 7 AM re 0 asiba nahi
is_weekend = now.weekday()>=5
is_before = now.hour<9 or (now.hour==9 and now.minute<15)
is_after = now.hour>=15 and now.minute>30
if is_weekend or is_before or is_after:
    # Suba 9:15 parjyanta chup
    if not (now.hour>=9 and now.hour<15 and not is_weekend):
        # Jodi test karucha bele bi message dia
        if os.getenv("GITHUB_EVENT_NAME")=="workflow_dispatch":
            pass # allow manual test
        else:
            print("Market Closed, skipping")
            exit()

nf_pcr=get_pcr("NIFTY")
bn_pcr=get_pcr("BANKNIFTY")
nf_sc=get_scalp("^NSEI")
bn_sc=get_scalp("^NSEBANK")

if not nf_pcr or not bn_pcr:
    send_msg(f"🔱 KALKI ⏰ {time_str}\n\n⚠️ NSE Server Busy\n5 min pare puni try kariba\nGitHub IP re NSE block karuchi, 9:15 AM re thik heijiba")
    exit()

# fallback for scalp
if not nf_sc: nf_sc={"price":nf_pcr['spot'],"sig":"⚠️ WAIT","rsi":0,"ema9":0,"ema21":0,"vwap":0,"sl":0,"t1":0,"sc":0}
if not bn_sc: bn_sc={"price":bn_pcr['spot'],"sig":"⚠️ WAIT","rsi":0,"ema9":0,"ema21":0,"vwap":0,"sl":0,"t1":0,"sc":0}

final="STRONG BUY" if 'BULLISH' in bn_pcr['tr'] and 'BUY' in bn_sc['sig'] else "STRONG SELL" if 'BEARISH' in bn_pcr['tr'] and 'SELL' in bn_sc['sig'] else "SIDEWAYS"

msg=f"""🔱 KALKI ULTIMATE ⏰ {time_str}

=== NIFTY {nf_pcr['spot']} ===
PCR {nf_pcr['pcr']} {nf_pcr['tr']} | CE {nf_pcr['t_ce']}L PE {nf_pcr['t_pe']}L
SCALP: {nf_sc['sig']} | P {nf_sc['price']} RSI {nf_sc['rsi']}
EMA9 {nf_sc['ema9']} EMA21 {nf_sc['ema21']} VWAP {nf_sc['vwap']}
SL {nf_sc['sl']} TGT {nf_sc['t1']}

=== BANKNIFTY {bn_pcr['spot']} ===
PCR {bn_pcr['pcr']} {bn_pcr['tr']} | CE {bn_pcr['t_ce']}L PE {bn_pcr['t_pe']}L
SCALP: {bn_sc['sig']} | P {bn_sc['price']} RSI {bn_sc['rsi']}
EMA9 {bn_sc['ema9']} EMA21 {bn_sc['ema21']} VWAP {bn_sc['vwap']}
SL {bn_sc['sl']} TGT {bn_sc['t1']}

🔥 FINAL: {final}
"""

send_msg(msg)
