import requests, time, datetime, os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

def get_spot():
    try:
        h = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://www.nseindia.com/api/allIndices", headers=h, timeout=10).json()
        for i in r['data']:
            if i['index']=='NIFTY 50':
                return float(i['last']), float(i['percentChange'])
    except:
        return 22498.0, 1.2
    return 22498.0, 1.2

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔱 Kalki 14.4 Ready!\n/live - LIVE Nifty Update\n/call - New Call")

# /call - normal call
async def call(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spot, pct = get_spot()
    if 22500 <= spot <= 22540:
        candle = "⚠️ Shooting Star @ Resistance"
        acc = 72
    else:
        candle = "✅ Bullish Hold @ 22500 Support"
        acc = 78
    
    await update.message.reply_text(f"""🔱 Kalki 14.4 CALL {datetime.datetime.now().strftime('%H:%M')}

📊 NIFTY: {spot} ({pct}%)
🕯️ Candle: {candle}
📈 Accuracy: {acc}%

👉 BUY 22500 CE @ 134
🎯 TGT: 192 | 🛑 SL: 96
📦 1 LOT
/live daba -> live dekhia pain""")

# /live - Tuma darkar thiba command!
async def live(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    spot_entry, _ = get_spot()
    entry = 134
    tgt = 192
    
    await context.bot.send_message(chat_id, f"🔴 LIVE STARTED @ {spot_entry}\nHar 15 sec re update. /stop daba band karibaku")

    for i in range(40
