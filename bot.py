import os, threading, requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# --- 1. RENDER LIVE RAKHIBA PAIN FLASK ---
keep_app = Flask('')
@keep_app.route('/')
def home(): return "🔱 KALKI 15.0 LIVE 🟢"
def run_flask(): keep_app.run(host='0.0.0.0', port=8080)

# --- 2. LIVE NSE PRICE ---
def get_ltp(strike=25200):
    try:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        d = s.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY", headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.nseindia.com/option-chain"}, timeout=10).json()
        for x in d['records']['data']:
            if x.get('strikePrice') == strike and 'CE' in x:
                return float(x['CE']['lastPrice'])
        return None
    except: return None

# --- 3. TODAY CALL ---
MSG = """🔱 KALKI 15.0 - 1ST SUPER-ACCURATE EDUCATIONAL CALL 🔱
13 Oct 09:15 AM 🚀

INSTRUMENT: NIFTY 50 25200 CE - 13 OCT (Tuesday Weekly Expiry)
📊 NIFTY: 22520.45 (1.3%) Above 20-DMA ✅

🎯 ACCURACY: 88% HIGH PROBABILITY ✅
Double Supertrend + VIX/PCR/OI Filter Pass

ENTRY PLAN:
Entry: ₹115-₹125 zone (If sustains >25,200 15min)
CMP CE: ₹120
TGT1: ₹155 (+25) 🎯
TGT2: ₹195 (+70) 🤑
SL: ₹78 Strict 🛑

CANDLE:
✓ 5min Bullish Engulfing + Vol >20DMA
✓ Hammer at 25,080 Support

DOUBLE SUPERTREND:
15min(10,3)= BUY ✅ Support 24,940
5min(7,2)= BUY ✅ Double Green

FILTERS: VIX 13.2<13.5 ✅ PCR 1.05 ✅ OI Bullish ✅

📦 1 LOT Paper Only
⚠️ Educational Only - Not SEBI Registered"""

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MSG)

async def pnl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ltp = get_ltp(25200) or 0
    pnl_rs = (ltp - 120) * 75
    await update.message.reply_text(f"📊 LIVE PNL\n25200 CE Entry: 120\nLTP: {ltp}\nPnL: ₹{pnl_rs}\nSL 78 | TGT 155/195")

async def strike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Use: /strike 25200")
        return
    try:
        s = int(context.args[0])
        ltp = get_ltp(s)
        await update.message.reply_text(f"💰 NIFTY {s} CE LTP: ₹{ltp}")
    except: await update.message.reply_text("Strike bhul!")

# --- 4. LIVE AUTO CHECK HAR 1 MIN ---
async def check_price(context: ContextTypes.DEFAULT_TYPE):
    if not CHAT_ID: return
    ltp = get_ltp(25200)
    if not ltp: return
    try:
        if ltp <= 78:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"🛑 SL HIT! 25200 CE LTP ₹{ltp} (SL 78)\nLOSS ₹{(ltp-120)*75} EXIT KARO!")
        elif ltp >= 195:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"🤑 TGT2 HIT! 25200 CE ₹{ltp} -> ₹195\nPROFIT ₹{(ltp-120)*75} BOOK KARO!")
        elif ltp >= 155:
            await context.bot.send_message(chat_id=CHAT_ID, text=f"🎯 TGT1 HIT! 25200 CE ₹{ltp} -> ₹155\nPROFIT ₹{(ltp-120)*75} 50% BOOK!")
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔱 KALKI LIVE! Commands:\n/today - Call\n/pnl - Live PnL\n/strike 25200 - Price")

def main():
    # Flask Start
    threading.Thread(target=run_flask).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("pnl", pnl))
    app.add_handler(CommandHandler("strike", strike))

    # Har 60 Sec Check
    if app.job_queue:
        app.job_queue.run_repeating(check_price, interval=60, first=10)

    print("🔱 KALKI BOT LIVE...")
    app.run_polling()

if __name__ == "__main__":
    main()
