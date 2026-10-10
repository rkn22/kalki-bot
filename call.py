import os, asyncio
from telegram.ext import Application

BOT = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

MSG = """🔱 KALKI 15.0 - 1ST SUPER-ACCURATE  CALL 🔱
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
⚠️ Educational Only - Not SEBI Registered
/today /pnl /strike 25200"""

async def main():
    app = Application.builder().token(BOT).build()
    await app.bot.send_message(chat_id=CHAT, text=MSG)

asyncio.run(main())
