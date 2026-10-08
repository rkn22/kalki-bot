import os, yfinance as yf, asyncio, requests, json, re
from datetime import datetime
import pytz
from telegram import Bot
IST = pytz.timezone('Asia/Kolkata')

# ===== GEMINI 3.6 PRO ULTRA =====
def get_gemini_sentiment(symbol="NIFTY", spot=0):
    try:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            return "NEUTRAL", 0.5, "Add GEMINI_API_KEY in secrets"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-preview-05-06:generateContent?key={api_key}"

        prompt = f"""You are Kalki - God level Nifty trader with 90% accuracy.

Analyze:
- Symbol: {symbol} Spot: {spot}
- Date: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
- Factors: NSE OI, PCR, VIX, USD/INR, Dow Futures, FII/DII, RBI News, Global

Give EXACT JSON:
{{
  "sentiment": "BULLISH/BEARISH/NEUTRAL",
  "confidence": 0.0-1.0,
  "reason": "one line 10 words",
  "risk": "LOW/MEDIUM/HIGH"
}}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "topP": 0.8, "maxOutputTokens": 300}
        }
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code==200:
            text = r.json()['candidates'][0]['content']['parts'][0]['text']
            try:
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    return data.get('sentiment','NEUTRAL'), float(data.get('confidence',0.75)), data.get('reason','Gemini 3.6 analysis')
            except:
                pass
            upper = text.upper()
            sent = "BULLISH" if "BULLISH" in upper else "BEARISH" if "BEARISH" in upper else "NEUTRAL"
            return sent, 0.85, text[:90]
        else:
            return "NEUTRAL", 0.5, f"Gemini error {r.status_code}"
    except Exception as e:
        return "NEUTRAL", 0.5, f"Err {str(e)[:50]}"

def get_nse_data(symbol="NIFTY"):
    try:
        h={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
        s=requests.Session(); s.get("https://www.nseindia.com", headers=h, timeout=5)
        r=s.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}", headers=h, timeout=8)
        if r.status_code==200:
            d=r.json()
            ce_oi=sum([x['CE']['openInterest'] for x in d['records']['data'] if 'CE' in x])
            pe_oi=sum([x['PE']['openInterest'] for x in d['records']['data'] if 'PE' in x])
            pcr=pe_oi/ce_oi if ce_oi>0 else 1.0
            spot=d['records']['underlyingValue']
            atm=round(spot/50)*50 if symbol=="NIFTY" else round(spot/100)*100
            atm_d=next((x for x in d['records']['data'] if x['strikePrice']==atm), None)
            if atm_d:
                return pcr,ce_oi,pe_oi,atm_d.get('CE',{}).get('lastPrice',0),atm_d.get('PE',{}).get('lastPrice',0),atm_d.get('CE',{}).get('changeinOpenInterest',0),atm_d.get('PE',{}).get('changeinOpenInterest',0),spot
        return 1.0,0,0,0,0,0,0,25200
    except:
        return 1.0,0,0,0,0,0,0,25200

def calc_rsi(s,p=14):
    d=s.diff(); g=d.where(d>0,0).rolling(p).mean(); l=-d.where(d<0,0).rolling(p).mean()
    return 100-(100/(1+g/l))

def get_df(t):
    try:
        df=yf.Ticker(t).history(period="10d", interval="15m")
        if len(df)<50: df=yf.Ticker(t).history(period="20d", interval="1h")
        return df
    except: return None

def v8_logic(df_nifty, pcr, ce_oi, pe_oi, ce_chg, pe_chg, gem_sent, gem_conf):
    if df_nifty is None or len(df_nifty)<50: return None
    close=df_nifty['Close']
    ema9=close.ewm(span=9).mean(); ema21=close.ewm(span=21).mean(); ema50=close.ewm(span=50).mean()
    rsi=calc_rsi(close); ema12=close.ewm(span=12).mean(); ema26=close.ewm(span=26).mean()
    macd=ema12-ema26; sig=macd.ewm(span=9).mean()
    vwap=((df_nifty['High']+df_nifty['Low']+close)/3).rolling(20).mean()
    vol_avg=df_nifty['Volume'].rolling(20).mean()
    c=close.iloc[-1]; e9=ema9.iloc[-1]; e21=ema21.iloc[-1]; e50=ema50.iloc[-1]
    cr=rsi.iloc[-1]; cm=macd.iloc[-1]; cs=sig.iloc[-1]; cv=vwap.iloc[-1]
    vol=df_nifty['Volume'].iloc[-1]; vavg=vol_avg.iloc[-1]

    bullish=e9>e21 and e21>e50 and c>e50
    bearish=e9<e21 and e21<e50 and c<e50
    if not (bullish or bearish): return None
    if 48<=cr<=58: return None
    if vol < vavg*0.8: return None

    score=0; reasons=[]
    if bullish:
        if cr<58 or cm<cs: return None
        score=8; reasons.append("✅ EMA+RSI+MACD Perfect Bull")
        if pcr>1.0 and pe_oi>ce_oi: score+=3; reasons.append(f"✅ PCR {pcr:.2f} Bullish")
        else: return None
        if pe_chg>ce_chg: score+=2; reasons.append("✅ PE OI Buildup")
        if gem_sent=="BULLISH" and gem_conf>=0.65:
            score+=5; reasons.append(f"🤖 Gemini 3.6 BULLISH {gem_conf:.2f}")
        elif gem_sent=="BEARISH": return None
    else:
        if cr>48 or cm>cs: return None
        score=-8; reasons.append("✅ EMA+RSI+MACD Perfect Bear")
        if pcr<0.9 and ce_oi>pe_oi: score-=3; reasons.append(f"✅ PCR {pcr:.2f} Bearish")
        else: return None
        if ce_chg>pe_chg: score-=2; reasons.append("✅ CE OI Buildup")
        if gem_sent=="BEARISH" and gem_conf>=0.65:
            score-=5; reasons.append(f"🤖 Gemini 3.6 BEARISH {gem_conf:.2f}")
        elif gem_sent=="BULLISH": return None

    if abs(score)<11: return None
    trend="CE" if score>0 else "PE"
    conf="GEMINI 3.6 GOD 90%" if abs(score)>=16 else "VERY HIGH"
    return {"trend":trend,"conf":conf,"score":score,"reasons":reasons,"rsi":cr,"pcr":pcr,"gem":gem_sent,"gem_conf":gem_conf}

async def main():
    token=os.getenv("BOT_TOKEN"); chat_id=os.getenv("CHAT_ID")
    bot=Bot(token=token)
    now=datetime.now(IST); h=now.hour+now.minute/60
    symbol="NIFTY" if h<13.5 else "BANKNIFTY"
    if os.getenv("SYMBOL","") in ["NIFTY","BANKNIFTY"]: symbol=os.getenv("SYMBOL")

    df_nifty=get_df("^NSEI")
    pcr,ce_oi,pe_oi,ce_p,pe_p,ce_chg,pe_chg,spot_nse=get_nse_data(symbol)
    gem_sent, gem_conf, gem_reason = get_gemini_sentiment(symbol, spot_nse)

    spot=float(df_nifty['Close'].iloc[-1]) if df_nifty is not None and len(df_nifty)>0 else spot_nse
    if spot_nse>1000: spot=spot_nse

    ana=v8_logic(df_nifty, pcr, ce_oi, pe_oi, ce_chg, pe_chg, gem_sent, gem_conf)
    now_ist=datetime.now(IST).strftime('%d %b %I:%M %p')
    rnd=100 if symbol=="BANKNIFTY" else 50
    strike=int(round(spot/rnd)*rnd)

    if ana is None:
        msg=f"""🔱 KALKI V8 GEMINI 3.6 WAIT

⏳ {symbol} SPOT: {spot:.2f}
📊 PCR: {pcr:.2f} | OI CE:{ce_oi/100000:.1f}L PE:{pe_oi/100000:.1f}L
🤖 Gemini 3.6: {gem_sent} ({gem_conf:.2f})
📝 {gem_reason}
🚫 Filter Fail - 90% Rule - No Trade
⏰ {now_ist} | Next 15min"""
    else:
        entry=int(ce_p if ana['trend']=="CE" and ce_p>10 else pe_p if pe_p>10 else 120)
        if entry<10: entry=120
        tpts=150 if "GOD" in ana['conf'] else 100
        spts=20 if "GOD" in ana['conf'] else 35
        if symbol=="BANKNIFTY": tpts+=150; spts+=30
        target=entry+tpts
        qty=f"{max(1,10000//max(entry,1))} Lots (~10k base)"
        logic="\n".join(ana['reasons'][:6])
        msg=f"""🔥 KALKI V8 GEMINI 3.6 {ana['conf']} | Score {ana['score']}/18

📊 {symbol} {strike} {ana['trend']} BUY
💰 Entry: {entry} | Target: {target} | SL: {spts}
📦 {qty} | PCR: {ana['pcr']:.2f}

🤖 GEMINI 3.6 PRO: {ana['gem']} {ana['gem_conf']:.2f}
🧠 RSI: {ana['rsi']:.0f} | Score: {ana['score']}
📜 V8 GOD LOGIC:
{logic}
💬 Gemini: {gem_reason}

⏰ {now_ist} | 10k Base | 90% Target
✅ @Rakun_biswalbot | V8 FINAL"""

    await bot.send_message(chat_id=chat_id, text=msg)

if __name__=="__main__":
    asyncio.run(main())
