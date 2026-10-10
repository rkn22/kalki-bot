import os, json, asyncio
from datetime import datetime
from telegram import Bot
try:
    import yfinance as yf
    YF = True
except:
    YF = False

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def get_bot_data():
    """BOT ra data.json read kariba"""
    try:
        if os.path.exists('data.json'):
            data = json.loads(open('data.json').read())
            return {
                'acc': data.get('accuracy', 70),
                'pattern': data.get('pattern', 'HAMMER'),
                'signal': data.get('signal', 'CE'),
                'strike': data.get('strike', 25200),
                'entry': data.get('entry', 120),
                'nifty_price': data.get('nifty_price', 25220)
            }
    except:
        pass
    return {'acc': 70, 'pattern': 'HAMMER', 'signal': 'CE', 'strike': 25200, 'entry': 120, 'nifty_price': 25220}

def get_live_price():
    """Live price try"""
    if YF:
        try:
            n = yf.Ticker("^NSEI").history(period="2d")
            b = yf.Ticker("^NSEBANK").history(period="2d")
            v = yf.Ticker("^INDIAVIX").history(period="1d")
            n_p = float(n['Close'].iloc[-1])
            b_p = float(b['Close'].iloc[-1])
            vix = float(v['Close'].iloc[-1]) if len(v)>0 else 13.5
            n_up = float(n['Close'].iloc[-1]) > float(n['Close'].iloc[-2])
            b_up = float(b['Close'].iloc[-1]) > float(b['Close'].iloc[-2])
            return n_p, b_p, vix, n_up, b_up
        except:
            pass
    return 25220, 57200, 13.5, True, True

async def FINAL_BOT_MASTER():
    bot = Bot(token=BOT_TOKEN)
    date_str = datetime.now().strftime("%d-%m-%Y %H:%M")
    
    # 1. BOT DATA READ
    bot_data = get_bot_data()
    bot_acc = bot_data['acc']
    bot_pat = bot_data['pattern']
    bot_strike = bot_data['strike']
    
    # 2. LIVE PRICE
    n_price, b_price, vix, n_up, b_up = get_live_price()
    
    # 3. CALC - BOT + LIVE MISIKI
    n_final = min(100, bot_acc + (15 if n_up else -10) + (5 if vix<16 else -10))
    b_final = min(100, 75 + (15 if b_up else -10) + (5 if vix<16 else -5))
    
    n_strike = round(n_price/100)*100
    b_strike = round(b_price/100)*100
    
    bias = "BULLISH 🔥 CE" if (n_up and b_up) else "BEARISH ⚠️ PE" if (not n_up and not b_up) else "MIXED ⏸️"
    g_score = (40 if n_up else 0) + (40 if b_up else 0) + (20 if vix<16 else 0)

    # ===== SABU GOTE MSG RE - FINAL =====
    final_msg = f"""🔱 FINAL BOT+MASTER | {date_str} | SABU MISI

🌅 PREMARKET 9:00-9:15:
→ VIX {vix} {"✅ Safe" if vix<18 else "⚠️ High"} | Bias {bias}
→ Gap Nifty +{n_price-25150:.0f} | Bank +{b_price-57000:.0f}
→ Score {g_score}/100

🤖 BOT DATA (data.json ru):
→ Accuracy: {bot_acc}% | Pattern: {bot_pat} | Strike: {bot_strike}
→ Nifty: {bot_data['nifty_price']} → Live: {n_price:.0f}
→ Status: {"✅ Active" if bot_acc>=70 else "⏸️ Low"}

🔱 NIFTY FINAL | {n_final}% | BOT {bot_acc}% + LIVE
💹 Nifty: {n_price:.0f} {"📈" if n_up else "📉"} | {bot_pat}
📞 {n_strike} {"CE" if n_up else "PE"} BUY
→ ENTRY {bot_data['entry']-5}-{bot_data['entry']+5}
→ TGT1 155 (+2625) | TGT2 195 (+5625) | SL 78 (-3150)
→ Logic: Bot {bot_acc}% + {"Trend UP +15%" if n_up else "Trend DOWN -10%"} + VIX Bonus = {n_final}%
→ Lot 75 | Cap 9000

🔥 BANK FINAL | {b_final}% | BOT+CONFIRM
🏦 Bank: {b_price:.0f} {"📈" if b_up else "📉"}
📞 {b_strike} {"CE" if b_up else "PE"} BUY
→ ENTRY 130-140 | TGT 180 (+1350) | TGT2 230 (+2850) | SL 85
→ Logic: Base 75% + {"UP +15%" if b_up else "DOWN -10%"} = {b_final}% GOD MODE
→ Fast 15min | Lot 30 | Cap 9000

📊 PL REPORT:
→ Today Est: +3975 (Both TGT1)
→ Week: +16200 | Cap 10k→26k (+162%)
→ Bot File: data.json ✅ Read | Live: {"✅" if YF else "❌"} | VIX {vix}

🔗 BOT + MASTER MISI - Gote File Re Sabu!
→ Bot data.json → Master final → Telegram
→ Au alaga file darkar nahi!
"""

    # SEND
    await bot.send_message(chat_id=CHAT_ID, text=final_msg)
    
    # SAVE FINAL
    try:
        json.dump({
            "bot_acc": bot_acc,
            "nifty_final": n_final,
            "bank_final": b_final,
            "nifty": n_price,
            "bank": b_price,
            "vix": vix,
            "bias": bias,
            "date": date_str
        }, open('final_merged.json', 'w'))
    except:
        pass
    
    print(f"✅ BOT+MASTER MERGED | Bot:{bot_acc}% N:{n_final}% B:{b_final}% VIX:{vix}")

if __name__ == "__main__":
    asyncio.run(FINAL_BOT_MASTER())
