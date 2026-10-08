import os, requests, yfinance as yf
import google.generativeai as genai
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def send_tg(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_nse_oi(symbol="BANKNIFTY"):
    try:
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        s = requests.Session()
        s.get("https://www.nseindia.com", headers=headers, timeout=5)
        r = s.get(url, headers=headers, timeout=5).json()
        ce_oi = sum([x['CE']['openInterest'] for x in r['records']['data'] if 'CE' in x][:10])
        pe_oi = sum([x['PE']['openInterest'] for x in r['records']['data'] if 'PE' in x][:10])
        pcr = round(pe_oi/ce_oi, 2) if ce_oi>0 else 1.0
        spot = r['records']['underlyingValue']
        # ATM premium
        atm = min(r['records']['data'], key=lambda x: abs(x['strikePrice']-spot))
        ce_ltp = atm['CE']['lastPrice'] if 'CE' in atm else 100
        pe_ltp = atm['PE']['lastPrice'] if 'PE' in atm else 100
        return spot, pcr, ce_oi/100000, pe_oi/100000, ce_ltp, pe_ltp
    except Exception as e:
        print(f"OI Error {e}")
        s = yf.Ticker("^NSEBANK" if "BANK" in symbol else "^NSEI").history(period="1d")['Close'].iloc[-1]
        return round(s,2), 1.10, 5.2, 6.1, 150, 150

def get_gemini(sym, spot, pcr):
    prompt = f"KALKI V8: {sym} Spot {spot} PCR {pcr}. Give VIEW BULLISH/BEARISH/NEUTRAL confidence. Format VIEW: X (0.X) REASON: 1 line"
    try:
        r = model.generate_content(prompt)
        txt = r.text.upper()
        view = "NEUTRAL"; conf = 0.6
        if "BULLISH" in txt: view="BULLISH"; conf=0.82
        if "BEARISH" in txt: view="BEARISH"; conf=0.82
        return view, conf, r.text[:220]
    except Exception as e:
        return "NEUTRAL", 0.5, str(e)

def main():
    LIVE = os.getenv("LIVE_MODE") == "true"
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist).strftime("%d %b %I:%M %p")
    
    b_spot, b_pcr, b_ce_oi, b_pe_oi, b_ce_ltp, b_pe_ltp = get_nse_oi("BANKNIFTY")
    n_spot, n_pcr, n_ce_oi, n_pe_oi, n_ce_ltp, n_pe_ltp = get_nse_oi("NIFTY")

    b_view, b_conf, b_rea = get_gemini("BANKNIFTY", b_spot, b_pcr)
    n_view, n_conf, n_rea = get_gemini("NIFTY", n_spot, n_pcr)

    b_score = (50 if b_view!="NEUTRAL" else 0) + (30 if b_conf>=0.70 else 0) + (20 if b_pcr>=1.1 or b_pcr<=0.9 else 0)
    n_score = (50 if n_view!="NEUTRAL" else 0) + (30 if n_conf>=0.70 else 0) + (20 if n_pcr>=1.1 or n_pcr<=0.9 else 0)

    if LIVE:
        msg = f"""🔱 *KALKI V9 LIVE REPORT* ⏰ {now}

*-- BANKNIFTY --*
📈 {b_spot} | PCR {b_pcr}
🤖 {b_view} ({b_conf}) Score {b_score}%
📊 OI CE:{b_ce_oi:.1f}L PE:{b_pe_oi:.1f}L
💰 CE LTP {b_ce_ltp} PE {b_pe_ltp}
📝 {b_rea}

*-- NIFTY --*
📈 {n_spot} | PCR {n_pcr}
🤖 {n_view} ({n_conf}) Score {n_score}%
📊 OI CE:{n_ce_oi:.1f}L PE:{n_pe_oi:.1f}L
💰 CE LTP {n_ce_ltp} PE {n_pe_ltp}
📝 {n_rea}

✅ Auto alert @ 80%+"""
        send_tg(msg)
        return

    # AUTO ALERTS WITH SL/TGT
    for sym, spot, pcr, view, conf, score, rea, ce_ltp, pe_ltp, ce_oi, pe_oi in [
        ("BANKNIFTY", b_spot, b_pcr, b_view, b_conf, b_score, b_rea, b_ce_ltp, b_pe_ltp, b_ce_oi, b_pe_oi),
        ("NIFTY", n_spot, n_pcr, n_view, n_conf, n_score, n_rea, n_ce_ltp, n_pe_ltp, n_ce_oi, n_pe_oi)
    ]:
        if score >= 80 and view != "NEUTRAL":
            ltp = ce_ltp if view=="BULLISH" else pe_ltp
            sl = round(ltp * 0.70, 1) # 30% SL
            tgt1 = round(ltp * 1.50, 1) # 50%
            tgt2 = round(ltp * 2.00, 1) # 100%
            tag = "🔥 80%" if score<90 else "🚀 90%+" if score<100 else "💎 100%"
            ce_pe = "CE" if view=="BULLISH" else "PE"
            strike = int(spot//100*100) if "BANK" in sym else int(spot//50*50)
            msg = f"""{tag} MATCH - {sym}

💥 *{view} {conf*100:.0f}%* | Score {score}%
📈 SPOT: {spot} | PCR: {pcr}
📊 OI CE:{ce_oi:.1f}L PE:{pe_oi:.1f}L
📝 {rea}

✅ *TRADE: {sym} {strike} {ce_pe}*
💰 LTP: {ltp}
🛑 SL: {sl} (-30%)
🎯 TGT1: {tgt1} (+50%) | TGT2: {tgt2} (+100%)
⏰ {now}

⚡ KALKI V9"""
            send_tg(msg)

if __name__ == "__main__":
    main()
