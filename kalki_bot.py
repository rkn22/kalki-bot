import requests, yfinance as yf, pytz, os
from datetime import datetime

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_msg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def get_nse_data(symbol):
    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/option-chain"
        }
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        res = session.get(url, headers=headers, timeout=10).json()
        
        spot = res['records']['underlyingValue']
        data = res['records']['data']
        atm_strike = min([d['strikePrice'] for d in data if 'CE' in d], key=lambda x: abs(x-spot))
        
        ce_oi = pe_oi = ce_ltp = pe_ltp = 0
        total_ce_oi = total_pe_oi = 0
        
        for item in data:
            if 'CE' in item: total_ce_oi += item['CE']['openInterest']
            if 'PE' in item: total_pe_oi += item['PE']['openInterest']
            if item['strikePrice'] == atm_strike:
                if 'CE' in item: 
                    ce_oi = item['CE']['openInterest']
                    ce_ltp = item['CE']['lastPrice']
                if 'PE' in item: 
                    pe_oi = item['PE']['openInterest']
                    pe_ltp = item['PE']['lastPrice']
        
        pcr = round(total_pe_oi/total_ce_oi, 2) if total_ce_oi>0 else 0
        
        if pcr > 1.1: trend = "BULLISH"; score = 85
        elif pcr < 0.9: trend = "BEARISH"; score = 85
        else: trend = "SIDEWAYS"; score = 65
        
        return {
            "spot": spot, "pcr": pcr, "trend": trend, "score": score,
            "ce_oi": round(ce_oi/100000, 1), "pe_oi": round(pe_oi/100000, 1),
            "ce_ltp": ce_ltp, "pe_ltp": pe_ltp,
            "total_ce": round(total_ce_oi/100000, 1), "total_pe": round(total_pe_oi/100000, 1)
        }
    except Exception as e:
        # === ETA JAGA RE ADD KARIBA BOLI KAHUTHILA ===
        print(f"NSE Fail {symbol}: {e}")
        sym = "^NSEBANK" if symbol=="BANKNIFTY" else "^NSEI"
        try:
            spot = yf.Ticker(sym).fast_info['last_price']
        except:
            spot = 54515.0 if symbol=="BANKNIFTY" else 22231.0
        return {"spot": round(float(spot),2), "pcr": 0.0, "trend": "MARKET CLOSED", "score": 0, "ce_oi": 0, "pe_oi": 0, "ce_ltp": 0, "pe_ltp": 0, "total_ce": 0, "total_pe": 0}

ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist).strftime("%d %b %I:%M %p")

bn = get_nse_data("BANKNIFTY")
nf = get_nse_data("NIFTY")

if bn['trend'] == "MARKET CLOSED":
    msg = f"🔱 KALKI V9 ⏰ {now}\n\n😴 MARKET CLOSED\nLast BANKNIFTY {bn['spot']}\nKali 9:15 AM ru LIVE asiba!"
else:
    msg = f"""🔱 KALKI V9 LIVE REPORT ⏰ {now}

-- BANKNIFTY --
📈 {bn['spot']} | PCR {bn['pcr']}
🤖 {bn['trend']} Score {bn['score']}%
📊 OI CE:{bn['ce_oi']}L PE:{bn['pe_oi']}L
💰 CE {bn['ce_ltp']} PE {bn['pe_ltp']}

-- NIFTY --
📈 {nf['spot']} | PCR {nf['pcr']}
🤖 {nf['trend']} Score {nf['score']}%
📊 OI CE:{nf['ce_oi']}L PE:{nf['pe_oi']}L
"""

send_msg(msg)
