import requests, os
from datetime import datetime, timedelta
from telegram.ext import Application, CommandHandler
from telegram import Update

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

active_trade = {"strike": None, "ce_entry": 0, "tgt1":0, "tgt2":0, "sl":0, "active":False, "pnl":0}

def get_nifty():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1m&range=1d"
        r = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}, timeout=10).json()
        meta = r['chart']['result'][0]['meta']
        price = meta['regularMarketPrice']
        prev = meta['chartPreviousClose']
        pct = round((price-prev)/prev*100,2)
        quote = r['chart']['result'][0]['indicators']['quote'][0]
        h = max([x for x in quote['high'] if x]) if quote['high'] else price
        l = min([x for x in quote['low'] if x]) if quote['low'] else price
        o = quote['open'][0] or price
        return float(price), float(pct), float(o), float(h), float(l)
    except:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        data = s.get("https://www.nseindia.com/api/allIndices", headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.nseindia.com/"}, timeout=10).json()
        n = [x for x in data['data'] if x['index'] == 'NIFTY 50'][0]
        return float(n['last']), float(n['percentChange']), float(n['open']), float(n['dayHigh']), float(n['dayLow'])

def get_option_ltp(strike):
    try:
        s = requests.Session()
        s.get("https://www.nseindia.com", headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        data = s.get("https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY", headers={"User-Agent":"Mozilla/5.0","Referer":"https://www.nseindia.com/option-chain"}, timeout=10).json()
        for d in data['records']['data']:
            if d.get('strikePrice') == strike and 'CE' in d:
                return float(d['CE']['lastPrice'])
        return None
    except:
        return None

def get_expiry():
    ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    days_ahead = (1 - ist.weekday()) % 7
    if days_ahead == 0 and ist.hour >= 15:
        days_ahead = 7
    expiry = ist + timedelta(days=days_ahead)
    return expiry.strftime("%d %b").upper()

async def morning_call(context):
    global active_trade
    try:
        price, pct, o, h, l = get_nifty()
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        now = ist_now.strftime("%I:%M %p")
        expiry_str = get_expiry()
        atm = round(price / 50) * 50

        body = abs(price - o)
        rng = h - l if h!= l else 1
        upper = h - max(price, o)
        lower = min(price, o) - l

        if body < rng * 0.15: acc = 50
        elif upper > body * 2: acc = 60
        elif lower > body * 2: acc = 88
        elif price > o and pct > 0.8: acc = 90
        elif price < o and pct < -0.8: acc = 40
        else: acc = 78

        if acc < 65:
            msg = f"🚫 SKIP {now}\n📊 NIFTY: {price} ({pct}%)\n🎯 Acc: {acc}% LOW ❌"
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)
            return

        ce = get_option_ltp(atm) or round(price * 0.006)
        tgt1 = ce + 25
        tgt2 = ce + 60
        sl = ce - 40
        active_trade = {"strike": atm, "ce_entry": ce, "tgt1": tgt1, "tgt2": tgt2, "sl": sl, "active": True, "pnl": 0}

        msg = f"🔱 KALKI 15.0 STRONG CALL {now} 🚀\n📊 NIFTY: {price} ({pct}%) 💹\n🎯 Acc: {acc}% SAFE ✅\n\n💰 BUY {atm} CE {expiry_str} @ ₹{ce} 💸\n🎯 TGT1: ₹{tgt1} TGT2: ₹{tgt2} 🤑\n🛑 SL: ₹{sl} ⚠️\n📦 1 LOT (75 Qty)"
        await context.bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print(f"Error: {e}")

async def live_check(context):
    global active_trade
    if not active_trade["active"]:
        return
    try:
        ltp = get_option_ltp(active_trade["strike"])
        if not ltp: return
        if ltp >= active_trade["tgt2"]:
            profit = (ltp - active_trade["ce_entry"]) * 75
            active_trade["pnl"] = profit
            msg = f"🎯 TGT2 HIT! 🤑\n{active_trade['strike']} CE: {active_trade['ce_entry']} -> {ltp}\n💰 Profit: ₹{profit}\nBOOK KARO!"
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)
            active_trade["active"] = False
        elif ltp >= active_trade["tgt1"]:
            profit = (ltp - active_trade["ce_entry"]) * 75
            active_trade["pnl"] = profit
            msg = f"✅ TGT1 HIT!\n{active_trade['strike']} CE: {active_trade['ce_entry']} -> {ltp}\n💰 Profit: ₹{profit}\n50% BOOK!"
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)
        elif ltp <= active_trade["sl"]:
            loss = (ltp - active_trade["ce_entry"]) * 75
            active_trade["pnl"] = loss
            msg = f"🛑 SL HIT! ⚠️\n{active_trade['strike']} CE: {active_trade['ce_entry']} -> {ltp}\n💸 Loss: ₹{loss}\nEXIT!"
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)
            active_trade["active"] = False
    except Exception as e:
        print(f"Live Error: {e}")

# --- COMMANDS ---

async def start(update: Update, context):
    await update.message.reply_text(
        "🔱 KALKI 15.0 FnO Bot Ready! 🚀\n\n"
        "/today - Aji Trade\n"
        "/pnl - Profit/Loss\n"
        "/stop - Band Kara\n"
        "/strike 25000 - LTP Dekha"
    )

async def today(update: Update, context):
    if not active_trade["strike"]:
        await update.message.reply_text("🚫 Aji Kichi Trade Nahi!")
        return
    ltp = get_option_ltp(active_trade["strike"]) or 0
    status = "🟢 ACTIVE" if active_trade["active"] else "🔴 CLOSED"
    msg = (
        f"📊 TODAY TRADE {status}\n\n"
        f"Strike: {active_trade['strike']} CE\n"
        f"Entry: ₹{active_trade['ce_entry']}\n"
        f"LTP: ₹{ltp}\n"
        f"TGT1: ₹{active_trade['tgt1']}\n"
        f"TGT2: ₹{active_trade['tgt2']}\n"
        f"SL: ₹{active_trade['sl']}"
    )
    await update.message.reply_text(msg)

async def pnl(update: Update, context):
    pnl_val = active_trade.get("pnl", 0)
    emoji = "🤑" if pnl_val > 0 else "💸" if pnl_val < 0 else "😐"
    await update.message.reply_text(f"💰 PNL: ₹{pnl_val} {emoji}\nStrike: {active_trade.get('strike','-')} CE")

async def stop(update: Update, context):
    global active_trade
    active_trade["active"] = False
    await update.message.reply_text("🛑 Trade Band Hela! Au Alert Asibani.")

async def strike(update: Update, context):
    if not context.args:
        await update.message.reply_text("Use: /strike 25000")
        return
    try:
        stk = int(context.args[0])
        ltp = get_option_ltp(stk)
        if ltp:
            await update.message.reply_text(f"📊 {stk} CE LTP: ₹{ltp} 💹")
        else:
            await update.message.reply_text("❌ Data Miluni, Tike Pare Try Kara")
    except:
        await update.message.reply_text("❌ Sahi Strike Dia - Ex: /strike 25000")

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("pnl", pnl))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("strike", strike))

    app.job_queue.run_daily(morning_call, time=datetime.strptime("03:45", "%H:%M").time(), days=(0,1,2,3,4))
    app.job_queue.run_repeating(live_check, interval=300, first=10)

    print("Bot Started...")
    app.run_polling()
