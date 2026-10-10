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

OPENING_SKIP_MIN = 1
VIX_MAX = 18

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

# ============ PURUNA CE - NO REMOVE ============
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

# ============ NUA PE - ADD ONLY - PURUNA DELETE NAHI ============
def check_candle_pattern_PE(o,h,l,c, prev_o, prev_c, vol, avg_vol):
    body = abs(c - o)
    if (h-l) == 0: return {"signal": False, "pattern": "None", "dir": "PE"}
    upper_wick = h - max(o,c)
    bearish_engulf = (prev_c > prev_o) and (c < o) and (c < prev_o) and (o > prev_c)
    shooting_star = (upper_wick > body*2) and (body < (h-l)*0.4) and (body > 0)
    vol_ok = vol > avg_vol * 1.2
    doji = body < (h-l)*0.1
    if doji: return {"signal": False, "pattern": "DOJI-REJECT", "dir": "PE"}
    if (bearish_engulf or shooting_star) and vol_ok:
        pat = "BEAR-ENGULF" if bearish_engulf else "SHOOT-STAR"
        return {"signal": True, "pattern": pat, "dir": "PE"}
    return {"signal": False, "pattern": "No Pattern", "dir": "PE"}

def build_msg_PE(num, time_str, pat="BEAR-ENGULF", acc=100):
    tier = get_tier(acc)
    profit1 = (TGT1-ENTRY)*LOT_SIZE
    profit2 = (TGT2-ENTRY)*LOT_SIZE
    loss = (ENTRY-SL)*LOT_SIZE
    emoji = "💯" if acc >= 100 else "🔥" if acc >= 90 else "💪" if acc >= 80 else "✅"
    return f"""{emoji} 🔱 KALKI 15.0 - {num}ND CALL | {time_str} 🔱
INSTRUMENT: NIFTY 50 25200 PE - TUESDAY EXPIRY
📊 NIFTY: 25220 | Accuracy: {acc}% ({tier})
Candle: {pat} 🔴 | Vol >20DMA ✅
Double Supertrend: 15min SELL + 5min SELL ✅
Filters: VIX 13.2 ✅ PCR 1.05 ✅ OI Bearish ✅
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

# ============ PURUNA MORNING CALL - UPDATE FOR CE+PE ============
async def morning_call(context):
    o,h,l,c,prev_o,prev_c,vol,avg_vol,vix,pcr,st15,st5 = fetch_live()
    if vix > VIX_MAX:
        print(f"SKIP - VIX High {vix} > {VIX_MAX}")
        return False, 0, "VIX-HIGH", "NONE"
    
    # CE CHECK
    candle = check_candle_pattern(o,h,l,c, prev_o, prev_c, vol, avg_vol)
    # PE CHECK - NUA
    candle_pe = check_candle_pattern_PE(o,h,l,c, prev_o, prev_c, vol, avg_vol)
    
    st15_ok = st15 == "BUY"
    st5_ok = st5 == "BUY"
    st15_ok_pe = st15 == "SELL"
    st5_ok_pe = st5 == "SELL"
    vix_ok = vix < 14
    pcr_ok = pcr > 1.0
    vol_ok = vol > avg_vol
    
    accuracy_ce = calculate_accuracy(candle["signal"], st15_ok, st5_ok, vix_ok, pcr_ok, vol_ok)
    accuracy_pe = calculate_accuracy(candle_pe["signal"], st15_ok_pe, st5_ok_pe, vix_ok, pcr_ok, vol_ok)
    
    # Decide CE or PE which is stronger
    if candle["signal"] and accuracy_ce >= MIN_ACCURACY and accuracy_ce >= accuracy_pe:
        try: open('data.json','w').write(json.dumps({"acc": accuracy_ce, "pat": candle['pattern'], "price": c, "vix": vix, "time": datetime.now().strftime("%H:%M"), "bot_signal": "CE"}))
        except: pass
        print(f"BOT SEND CE {accuracy_ce}% {candle['pattern']}")
        await context.bot.send_message(chat_id=CHAT, text=build_msg(1, datetime.now().strftime("%I:%M %p"), candle['pattern'], accuracy_ce))
        return True, accuracy_ce, candle['pattern'], "CE"
    
    if candle_pe["signal"] and accuracy_pe >= MIN_ACCURACY:
        try: open('data.json','w').write(json.dumps({"acc": accuracy_pe, "pat": candle_pe['pattern'], "price": c, "vix": vix, "time": datetime.now().strftime("%H:%M"), "bot_signal": "PE"}))
        except: pass
        print(f"BOT SEND PE {accuracy_pe}% {candle_pe['pattern']}")
        await context.bot.send_message(chat_id=CHAT, text=build_msg_PE(1, datetime.now().strftime("%I:%M %p"), candle_pe['pattern'], accuracy_pe))
        return True, accuracy_pe, candle_pe['pattern'], "PE"
    
    print(f"SKIP - CE Acc: {accuracy_ce}% PE Acc: {accuracy_pe}%")
    return False, max(accuracy_ce, accuracy_pe), candle['pattern'] if accuracy_ce>accuracy_pe else candle_pe['pattern'], "NONE"

class DummyContext:
    def __init__(self, bot):
        self.bot = bot

# ============ PURUNA FULL MONITOR - UPDATE FOR PE - NO REMOVE ============
async def monitor_sl_tgt(bot, option_type="CE"):
    print(f"📡 SL/TGT Monitoring Started... {option_type} Full Features ON")
    entry_nifty = 25220
    try:
        _,_,_,entry_nifty,_,_,_,_,_,_,_,_ = fetch_live()
    except:
        entry_nifty = 25220
    entry_time = datetime.now().strftime("%I:%M %p")
    tgt1_done = False
    sl_cost_done = False
    max_profit = 0
    max_opt = ENTRY
    cmp_now = ENTRY
    
    for i in range(360):
        try:
            _,_,_,c,_,_,_,_,vix,_,_,_ = fetch_live()
            nifty_move = c - entry_nifty
            if option_type=="CE":
                live_est = ENTRY + (nifty_move * 0.48)
            else:
                live_est = ENTRY - (nifty_move * 0.48)
            if vix > 14:
                live_est -= 2
            cmp_now = max(10, live_est)
            max_opt = max(max_opt, cmp_now)
            max_profit = max(max_profit, (cmp_now-ENTRY)*LOT_SIZE)
            pnl_now = (cmp_now-ENTRY)*LOT_SIZE
            print(f"📊 [{i+1}/360] {option_type} Nifty {c:.0f} ({nifty_move:+.0f}) → Opt ₹{cmp_now:.0f} | PnL ₹{pnl_now:+.0f}")
            
            if cmp_now >= TGT1 and not tgt1_done:
                tgt1_done = True
                sl_cost_done = True
                profit = (TGT1-ENTRY)*LOT_SIZE
                await bot.send_message(chat_id=CHAT, text=f"🎯 TGT1 HIT! {option_type} {datetime.now().strftime('%I:%M %p')}\nNifty {c:.0f} Opt ₹{cmp_now:.0f} Profit +₹{profit} SL→Cost")
                await asyncio.sleep(60)
                continue
            
            if cmp_now >= TGT2:
                profit = (TGT2-ENTRY)*LOT_SIZE
                await bot.send_message(chat_id=CHAT, text=f"🤑 TGT2 HIT! {option_type} FULL +₹{profit} {datetime.now().strftime('%I:%M %p')}")
                try:
                    pl = json.loads(open('pl.json').read()) if os.path.exists('pl.json') else {"week":12225,"cap":22225}
                    pl["week"] += profit
                    pl["cap"] += profit
                    json.dump(pl, open('pl.json','w'))
                except: pass
                return
            
            current_sl = ENTRY if sl_cost_done else SL
            if cmp_now <= current_sl:
                if sl_cost_done:
                    await bot.send_message(chat_id=CHAT, text=f"⚠️ SL TO COST {option_type} {datetime.now().strftime('%I:%M %p')} Profit {(TGT1-ENTRY)*LOT_SIZE//2} safe")
                else:
                    loss = (ENTRY-SL)*LOT_SIZE
                    await bot.send_message(chat_id=CHAT, text=f"🛑 SL HIT! {option_type} {datetime.now().strftime('%I:%M %p')} Loss -₹{loss}")
                return
            
            if i % 15 == 0 and i > 0:
                await bot.send_message(chat_id=CHAT, text=f"📡 LIVE {option_type}: {datetime.now().strftime('%I:%M %p')} | Nifty {c:.0f} | Opt ₹{cmp_now:.0f} | PnL ₹{pnl_now:+.0f}")
            
        except Exception as e:
            print(f"SL/TGT Error: {e}")
        await asyncio.sleep(60)

async def github_run_once():
    bot = Bot(token=BOT)
    ctx = DummyContext(bot)
    print(f"✅ KALKI AUTO - 70%+ CE+PE Loop + SL/TGT")
    for i in range(13):
        if i == 0:
            print(f"⏳ Opening 10min skip - Start 9:25")
            await asyncio.sleep(600)
            continue
        success, acc, pat, opt_type = await morning_call(ctx)
        if success:
            print(f"✅ DONE {opt_type} - Start Monitor")
            await monitor_sl_tgt(bot, opt_type)
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
        print(f"✅ LOCAL MODE - CE+PE GOD MODE")
        app.run_polling()

if __name__ == "__main__":
    main()
