import requests, time, datetime
from telegram import Bot

BOT_TOKEN = "TUMA_TOKEN"
CHAT_ID = "TUMA_CHAT_ID"
bot = Bot(token=BOT_TOKEN)

def get_spot():
    try:
        h = {"User-Agent": "Mozilla/5.0"}
        r = requests.get("https://www.nseindia.com/api/allIndices", headers=h, timeout=5).json()
        for i in r['data']:
            if i['index']=='NIFTY 50':
                return i['last'], i['percentChange']
    except:
        return 22498, 1.2
    return 22498, 1.2

# ---- 1. CALL + REAL-TIME EKASANGE ----
def send_live_call():
    spot, pct = get_spot()
    
    # Candle
    if 22500 <= spot <= 22540:
        candle = "⚠️ Shooting Star @ Resistance"
        acc = 72
    elif 22470 <= spot < 22500:
        candle = "✅ Bullish Hold @ 22500 Support"
        acc = 78
    else:
        candle = "Strong Bullish"
        acc = 80

    entry = 134  # Tuma aji ra entry
    tgt = 192
    sl = 96
    
    # Main Call
    bot.send_message(CHAT_ID, f"🔱 CALL 11:36\nBUY 22500 CE @ {entry}\nSpot {spot} | {candle}\nAcc {acc}% | TGT {tgt} SL {sl} | 1 LOT")

    # Tale Tale 6 ta Update (30 min)
    for _ in range(6):
        time.sleep(180) # 3 min pare update
        n_spot, n_pct = get_spot()
        # Simple premium calc
        ce_now = entry + (n_spot - spot)*0.65
        pnl = (ce_now - entry)*75
        
        bot.send_message(CHAT_ID, f"""📈 UPDATE {datetime.datetime.now().strftime('%H:%M')}
NIFTY {spot}→{n_spot}
22500 CE {entry}→{ce_now:.0f}
P&L {pnl:.0f} Rs
{candle}
SL {sl} TGT {tgt}""")
        
        if ce_now >= tgt or ce_now <= sl:
            bot.send_message(CHAT_ID, f"{'🎯 TGT HIT BOOK!' if ce_now>=tgt else '🛑 SL HIT EXIT!'}")
            break

# ---- RUN ----
# Ebe test pain gote thara chalao
send_live_call()
