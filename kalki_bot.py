import requests, yfinance as yf, pytz, os
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(t): requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": t})

def get_data(sym):
    try:
        s=requests.Session(); h={"User-Agent":"Mozilla/5.0","Referer":"https://www.nseindia.com/option-chain"}
        s.get("https://www.nseindia.com", headers=h, timeout=10)
        r=s.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={sym}", headers=h, timeout=10).json()
        spot=r['records']['underlyingValue']; data=r['records']['data']
        atm=min([d['strikePrice'] for d in data if 'CE' in d], key=lambda x: abs(x-spot))
        ce=pe=ce_ltp=pe_ltp=t_ce=t_pe=0
        for i in data:
            if 'CE' in i: t_ce+=i['CE']['openInterest']
            if 'PE' in i: t_pe+=i['PE']['openInterest']
            if i['strikePrice']==atm:
                if 'CE' in i: ce=i['CE']['openInterest']; ce_ltp=i['CE']['lastPrice']
                if 'PE' in i: pe=i['PE']['openInterest']; pe_ltp=i['PE']['lastPrice']
        pcr=round(t_pe/t_ce,2) if t_ce else 0; diff=t_pe-t_ce
        if pcr>1.2: tr="STRONG BULLISH"; sc=90; rs=f"PE {t_pe/1e5:.1f}L > CE {t_ce/1e5:.1f}L by {diff/1e5:.1f}L | PCR {pcr}>1.2 = Heavy Put writing"
        elif pcr>1.05: tr="BULLISH"; sc=75; rs=f"PE {t_pe/1e5:.1f}L > CE {t_ce/1e5:.1f}L | PCR {pcr}=Bullish"
        elif pcr<0.8: tr="STRONG BEARISH"; sc=90; rs=f"CE {t_ce/1e5:.1f}L > PE {t_pe/1e5:.1f}L by {abs(diff)/1e5:.1f}L | PCR {pcr}<0.8=Heavy Call writing"
        elif pcr<0.95: tr="BEARISH"; sc=75; rs=f"CE {t_ce/1e5:.1f}L > PE {t_pe/1e5:.1f}L | PCR {pcr}=Bearish"
        else: tr="SIDEWAYS"; sc=60; rs=f"CE {t_ce/1e5:.1f}L ≈ PE {t_pe/1e5:.1f}L | PCR {pcr}=Balanced"
        return {"spot":spot,"pcr":pcr,"tr":tr,"sc":sc,"rs":rs,"ce":round(ce/1e5,1),"pe":round(pe/1e5,1),"t_ce":round(t_ce/1e5,1),"t_pe":round(t_pe/1e5,1),"diff":round(diff/1e5,1),"ce_ltp":ce_ltp,"pe_ltp":pe_ltp}
    except:
        ysym="^NSEBANK" if sym=="BANKNIFTY" else "^NSEI"
        try: spot=yf.Ticker(ysym).fast_info['last_price']
        except: spot=54515 if sym=="BANKNIFTY" else 25230
        return {"spot":float(spot),"pcr":0,"tr":"MARKET CLOSED","sc":0,"rs":"Market bandh","ce":0,"pe":0,"t_ce":0,"t_pe":0,"diff":0,"ce_ltp":0,"pe_ltp":0}

ist=pytz.timezone('Asia/Kolkata'); now=datetime.now(ist).strftime("%d %b %I:%M %p")
nf=get_data("NIFTY"); bn=get_data("BANKNIFTY")

if nf['tr']=="MARKET CLOSED":
    msg=f"🔱 KALKI V10 ⏰ {now}\n\n😴 MARKET CLOSED\nNIFTY Last {nf['spot']} | BANKNIFTY {bn['spot']}\nReason: Market bandh achi\n9:15 AM ru LIVE asiba!"
else:
    # CHECKLIST LOGIC
    def checklist(d):
        c=[]
        c.append(f"{'✅' if d['pcr']>1.05 else '❌'} PCR {d['pcr']} {'>1.05 Bullish' if d['pcr']>1.05 else '<0.95 Bearish' if d['pcr']<0.95 else '=Sideways'}")
        c.append(f"{'✅' if d['diff']>0 else '❌'} OI Diff {d['diff']}L {'PE Dominant' if d['diff']>0 else 'CE Dominant'}")
        c.append(f"{'✅' if d['pe']>d['ce'] else '❌'} ATM PE {d['pe']}L {'>' if d['pe']>d['ce'] else '<'} CE {d['ce']}L")
        c.append(f"{'✅' if d['sc']>=75 else '⚠️' if d['sc']>=60 else '❌'} Score {d['sc']}%")
        return "\n".join(c)

    msg=f"""🔱 KALKI V10 LIVE ⏰ {now}

=== 1. NIFTY {nf['spot']} | PCR {nf['pcr']} ===
🤖 {nf['tr']} {nf['sc']}%
📝 {nf['rs']}
💰 ATM CE:{nf['ce_ltp']} PE:{nf['pe_ltp']}
📊 Total CE:{nf['t_ce']}L PE:{nf['t_pe']}L

📋 CHECKLIST NIFTY:
{checklist(nf)}

=== 2. BANKNIFTY {bn['spot']} | PCR {bn['pcr']} ===
🤖 {bn['tr']} {bn['sc']}%
📝 {bn['rs']}
💰 ATM CE:{bn['ce_ltp']} PE:{bn['pe_ltp']}
📊 Total CE:{bn['t_ce']}L PE:{bn['t_pe']}L

📋 CHECKLIST BANKNIFTY:
{checklist(bn)}

🔱 Final: {nf['tr']} / {bn['tr']} | Trade with SL!
"""

send_msg(msg)
