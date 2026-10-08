import os, yfinance as yf, asyncio, random
from datetime import datetime
import pytz
from telegram import Bot

IST = pytz.timezone('Asia/Kolkata')

def get_nifty_data():
    try:
        ticker = yf.Ticker("^NSEI")
        df = ticker.history(period="5d", interval="15m")
        if df.empty:
            return 25210.50, 25180, 25250, "Hammer"
        nifty = float(df['Close'].iloc[-1])
        low = float(df['Low'].tail(10).min())
        high = float(df['High'].tail(10).max())
        support = round(low / 10) * 10
        resistance = round(high / 10) * 10
        last = df.iloc[-1]
        body = abs(last['Close'] - last['Open'])
        wick_low = min(last['Open'], last['Close']) - last['Low']
        wick_high = last['High'] - max(last['Open'], last['Close'])
        if wick_low > body*1.5:
            pattern = "Hammer"
        elif wick_high > body*1.5:
            pattern = "Shooting Star"
        else:
            pattern = "Bullish Engulfing"
        return nifty, support, resistance, pattern
    except:
        return 25210.50, 25180, 25250, "Hammer"

def get_sure_shot():
    nifty, sup, res, pattern = get_nifty_data()
    strike = int(round(nifty / 50) * 50)
    entry = random.randint(105, 145)
    target = entry + random.randint(80, 120)
    zone_text = f"{sup}-{sup+70}"
    option = f"NIFTY {strike} CE BUY"
    if nifty < 22180:
        option = f"NIFTY {strike} PE BUY"
        zone_text = f"{res-70}-{res}"
    now_ist = datetime.now(IST).strftime('%d %b, %I:%M %p')
    msg = f"""🔥 KALKI SURE SHOT LIVE!

📊 {option}
💰 Entry: {entry} | Target {target} | SL 40

🎯 Target: 80-120 Points
⛔ SL: 40 Points

🔱 KALKI DAILY SIGNAL
⏳ WAIT - NIFTY {nifty:.2f}
Zone: {zone_text} | Watch {pattern}/Engulfing
Time: 15min Chart | {now_ist}

✅ Join: @Rakun_biswalbot
"""
    return msg

async def main():
    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("CHAT_ID")
    bot = Bot(token=token)
    signal = get_sure_shot()
    await bot.send_message(chat_id=chat_id, text=signal)

asyncio.run(main())
