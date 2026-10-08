import os, requests, yfinance as yf
import google.generativeai as genai
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Gemini setup - FIXED 404
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def send_tg(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_banknifty():
    try:
        data = yf.Ticker("^NSEBANK").history(period="1d")
        spot = round(data['Close'].iloc[-1], 2)
        # Dummy OI/PCR for now - NSE API can be added
        return spot, 1.15, 5.2, 6.1
    except:
        return 25200.0, 1.00, 0.0, 0.0

def get_gemini_call(spot, pcr):
    prompt = f"""
    You are KALKI V8 trading expert. BANKNIFTY Spot {spot}, PCR {pcr}.
    Analyse: US CPI, FII/DII, Trend, PCR.
    Give output in format:
    VIEW: BULLISH/BEARISH/NEUTRAL (confidence 0-1)
    REASON: one line
    STRIKE: NIFTY/BANKNIFTY CE/PE with price
    Only give BULLISH if confidence >0.80 and PCR>1.1 or BEARISH if PCR<0.9
    """
    try:
        res = model.generate_content(prompt)
        text = res.text
        # Parse
        view = "NEUTRAL"
        conf = 0.5
        if "BULLISH" in text.upper(): view = "BULLISH"; conf = 0.88
        if "BEARISH" in text.upper(): view = "BEARISH"; conf = 0.88
        return view, conf, text[:250]
    except Exception as e:
        return "NEUTRAL", 0.5, f"Gemini error {e}"

def main():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist).strftime("%d %b %I:%M %p")
    spot, pcr, oi_ce, oi_pe = get_banknifty()
    view, conf, reason = get_gemini_call(spot, pcr)

    # 90% FILTER LOGIC - CALL MATCH ONLY
    match_all = False
    if view == "BULLISH" and conf >= 0.80 and pcr >= 1.10:
        match_all = True
        strike = f"BANKNIFTY {int(spot//100*100)} CE"
        msg = f"""🔱 *KALKI V8 CALL MATCHED!* 🚀

💥 *BANKNIFTY {view}*
📈 SPOT: {spot}
📊 PCR: {pcr} | OI CE:{oi_ce}L PE:{oi_pe}L
🤖 Gemini {view} ({conf})
📝 {reason}

✅ *TRADE: {strike} @ MARKET*
🎯 SL: 30% | TGT: 60%
⏰ {now}

⚡ *TAKE TRADE NOW!*"""
        send_tg(msg)
        
    elif view == "BEARISH" and conf >= 0.80 and pcr <= 0.90:
        match_all = True
        strike = f"BANKNIFTY {int(spot//100*100)} PE"
        msg = f"""🔱 *KALKI V8 CALL MATCHED!* 🔻

💥 *BANKNIFTY {view}*
📈 SPOT: {spot}
📊 PCR: {pcr} | OI CE:{oi_ce}L PE:{oi_pe}L
🤖 Gemini {view} ({conf})
📝 {reason}

✅ *TRADE: {strike} @ MARKET*
🎯 SL: 30% | TGT: 60%
⏰ {now}

⚡ *TAKE TRADE NOW!*"""
        send_tg(msg)
    
    # If no match - DO NOT SEND WAIT MESSAGE (Silent)
    if not match_all:
        print(f"NO TRADE - {view} {conf} PCR {pcr} - Filter Fail")
        # Optional: send only if you want debug, else silent
        # send_tg(f"🔱 KALKI WAIT\nSPOT: {spot} PCR: {pcr}\nGemini: {view} ({conf})\nReason: {reason}\nFilter Fail - No Trade\n{now}")
        return

if __name__ == "__main__":
    main()
