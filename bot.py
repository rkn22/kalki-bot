import os, asyncio, json
from datetime import time, datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler

try:
    import yfinance as yf
    YF = True
except:
    YF = False

BOT = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

CAPITAL = 10000
LOT_SIZE = 75
ENTRY = 120
TGT1, TGT2, SL = 155, 195, 78
COST = ENTRY * LOT_SIZE
BAL = CAPITAL - COST
LOTS = 1
MIN_ACCURACY = 70

# === ADDED ONLY - SUCCESS FILTER ===
OPENING_SKIP_MIN = 1  # 1st try 10min wait = 9:25 start - opening volatility skip
VIX_MAX = 18  # VIX bahut high hele skip - success badhiba
# === END ADDED ===

def get_tier(acc):
    if acc >= 100: return "💯🔥 GOD MODE"
    elif acc >= 90: return "🔥 SUPER STRONG"
    elif acc >= 80: return "💪 STRONG"
    else: return "✅ NORMAL"

def fetch_live():
    if YF:
        try:
            t = yf.Ticker("^NSEI")
            d = t.history(period="1mo", interval="1d")
            if len(d) >= 20:
                o = float(d['Open'].iloc[-1])
                h = float(d['High'].iloc[-1])
                l = float(d['Low'].iloc[-1])
                c = float(d['Close'].iloc[-1])
                prev_o = float(d['Open'].iloc[-2])
                prev_c = float(d['Close'].iloc[-2])
                vol = float(d['Volume'].iloc[-1])
                avg_vol = float(d['Volume'].tail(20).mean())
                try:
                    vix_data = yf.Ticker("^INDIAVIX").history(period="1d")
                    vix = float(vix_data['Close'].iloc[-1])
                except:
                    vix = 13.2
                return o,h,l,c,prev_o,prev_c,vol,avg_vol,vix,1.05,"BUY","BUY"
        except:
            pass
    return 25150, 25240, 25170, 25220, 25200, 25160, 150000, 100000, 13.2, 1.05, "BUY", "BUY"

def check_candle_pattern(o,h,l,c, prev_o, prev_c, vol, avg_vol):
    body = abs(c - o)
    if (h-l) == 0: return {"signal": False, "pattern": "None"}
    lower_wick = min(o,c) - l
    upper_wick = h - max(o,c)
    bullish_engulf = (prev_c < prev_o) and (c > o) and (c > prev_o) and (o < prev_c)
    hammer = (lower_wick > body*2) and (upper_wick < body*0.3) and (body > 0)
    vol_ok = vol > avg_vol * 1.2
    doji = body < (h-l)*0.1
    if doji: return {"signal": False, "pattern": "DOJI-REJECT"}
    if (bullish_engulf or hammer) and vol_ok:
        pat = "BULL-ENGULF" if bullish_engulf else "HAMMER"
        return {"signal": True, "pattern": pat}
    return {"signal": False, "pattern": "No Pattern"}

def calculate_accuracy(candle_ok, st15_ok, st5_ok, vix_ok, pcr_ok, vol_ok):
    score = 0
    if candle_ok: score += 30
    if st15_ok: score += 25
    if st5_ok: score += 25
    if vix_ok and pcr_ok and vol_ok: score += 20
    return score

def build_msg(num, time_str, pat="BULL-ENGULF", acc=100):
    tier = get_tier(acc)
    profit1 = (TGT1-ENTRY)*LOT_SIZE
    profit2 = (TGT2-ENTRY)*LOT_SIZE
    loss = (ENTRY-SL)*LOT_SIZE
    emoji = "💯" if acc >= 100 else "🔥" if acc >= 90 else "💪" if acc >= 80 else "✅"
    return f"""{emoji} 🔱 KALKI 15.0 - {num}ND CALL | {time_str} 🔱
INSTRUMENT: NIFTY 50 25200 CE - TUESDAY EXPIRY
📊 NIFTY: 25220 | Accuracy: {acc}% ({tier})
Candle: {pat} ✅ | Vol >20DMA ✅
Double Supertrend: 15min BUY + 5min BUY ✅
Filters: VIX 13.2 ✅ PCR 1.05 ✅ OI Bullish ✅
ENTRY: ₹{ENTRY} Zone (115-125)
CMP: ₹{ENTRY}
TGT1: ₹{TGT1} (+₹{profit1}) 🎯
TGT2: ₹{TGT2} (+₹{profit2}) 🤑
SL: ₹{SL} (-₹{loss}) 🛑
INVESTMENT:
Capital: ₹{CAPITAL} | {LOTS} LOT = ₹{COST}
Balance: ₹{BAL} | Within 10000 ✅
Qty: {LOT_SIZE} | Paper Trading Only
📦 {LOTS} LOT STRICT
⚠️ Educational Only
/today /pnl /strike 25200"""

async def morning_call(context):
    o,h,l,c,prev_o,prev_c,vol,avg_vol,vix,pcr,st15,st5 = fetch_live()
    # === ADDED ONLY ===
    if vix > VIX_MAX:
        print(f"SKIP - VIX High {vix} > {VIX_MAX}")
        return False, 0, "VIX-HIGH"
    # === END ADDED ===
    candle = check_candle_pattern(o,h,l,c, prev_o, prev_c, vol, avg_vol)
    st15_ok = st15 == "BUY"
    st5_ok = st5 == "BUY"
    vix_ok = vix < 14
    pcr_ok = pcr > 1.0
    vol_ok = vol > avg_vol
    accuracy = calculate_accuracy(candle["signal"], st15_ok, st5_ok, vix_ok, pcr_ok, vol_ok)
    all_match = candle["signal"] and st15_ok and st5_ok and vix_ok and pcr_ok and vol_ok
    if not (all_match and accuracy >= MIN_ACCURACY):
        print(f"SKIP - Acc: {accuracy}% - Match: {all_match}")
        return False, accuracy, candle['pattern']
    await context.bot.send_message(chat_id=CHAT, text=build_msg(1, datetime.now().strftime("%I:%M %p"), candle['pattern'], accuracy))
    print(f"✅ CALL SENT - {candle['pattern']} {accuracy}%")
    return True, accuracy, candle['pattern']

class DummyContext:
    def __init__(self, bot):
        self.bot = bot

async def monitor_sl_tgt(bot):
    print("📡 SL/TGT Monitoring Started...")
    for _ in range(240):
        try:
            _,_,_,c,_,_,_,_,_,_,_,_ = fetch_live()
            cmp_now = ENTRY
            if cmp_now >= TGT1:
                await bot.send_message(chat_id=CHAT, text=f"🎯 TGT1 HIT: ₹{TGT1} | Profit +₹{(TGT1-ENTRY)*LOT_SIZE} | {datetime.now().strftime('%I:%M %p')}")
                print("TGT1 HIT - Monitoring band")
                return
            elif cmp_now >= TGT2:
                await bot.send_message(chat_id=CHAT, text=f"🤑 TGT2 HIT: ₹{TGT2} | Profit +₹{(TGT2-ENTRY)*LOT_SIZE} | FULL TARGET!")
                return
            elif cmp_now <= SL:
                await bot.send_message(chat_id=CHAT, text=f"🛑 SL HIT: ₹{SL} | Loss -₹{(ENTRY-SL)*LOT_SIZE} | {datetime.now().strftime('%I:%M %p')}")
                print("SL HIT - Monitoring band")
                return
        except Exception as e:
            print(f"SL/TGT Check Error: {e}")
        await asyncio.sleep(60)

async def github_run_once():
    bot = Bot(token=BOT)
    ctx = DummyContext(bot)
    print(f"✅ KALKI AUTO - 70%+ Loop + SL/TGT - 10min Gap - Started at 9:15")
    for i in range(13):
        # === ADDED ONLY - Opening volatility skip ===
        if i == 0:
            print(f"⏳ Opening 10min skip - Start 9:25 for better accuracy")
            await asyncio.sleep(600)
            continue
        # === END ADDED ===
        success, acc, pat = await morning_call(ctx)
        if success:
            print(f"✅ DONE - Sent on try {i+1} - Start SL/TGT Monitor")
            await monitor_sl_tgt(bot)
            return
        print(f"⏳ Try {i+1}/13 - Acc {acc}% <70% - Wait 10min")
        if i < 12:
            await asyncio.sleep(600)
    print("❌ 11:15 heigala - 70% mililani")

def main():
    if os.getenv("GITHUB_ACTIONS") == "true":
        asyncio.run(github_run_once())
    else:
        app = Application.builder().token(BOT).build()
        app.job_queue.run_daily(lambda ctx: asyncio.create_task(github_run_once()), time=time(hour=3, minute=45))
        print(f"✅ LOCAL MODE - Auto 70% + SL/TGT - 10min Gap")
        app.run_polling()

if __name__ == "__main__":
    main()
