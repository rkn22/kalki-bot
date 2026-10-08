import os, yfinance as yf, asyncio
from telegram import Bot

def get_signal():
    df = yf.Ticker("^NSEI").history(period="5d", interval="15m")
    if df.empty:
        return "NIFTY data not available"
    nifty = df['Close'].iloc[-1]
    prev = df.iloc[-2]
    last = df.iloc[-1]
    
    # Simple pattern logic
    if nifty < 22180:
        return f"🟢 BUY 22200 PE ~110-125\nNIFTY: {nifty:.2f} (Breakdown)\nSL 80 | TGT 180"
    elif nifty > 22250:
        return f"🔴 AVOID PE - NIFTY High {nifty:.2f}\nWait for 22200 break"
    else:
        return f"⏳ WAIT - NIFTY {nifty:.2f}\nZone: 22180-22250 | Watch Hammer/Engulfing"

async def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    bot = Bot(token=token)
    signal = get_signal()
    msg = f"🔱 KALKI DAILY SIGNAL\n\n{signal}\n\nTime: 15min Chart"
    await bot.send_message(chat_id=chat_id, text=msg)

asyncio.run(main())
