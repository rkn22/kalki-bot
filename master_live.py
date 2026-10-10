import os, json, asyncio
from datetime import time, datetime
from telegram import Bot
from telegram.ext import Application, CommandHandler
try:
    import yfinance as yf
    YF=True
except:
    YF=False

BOT=os.getenv("BOT_TOKEN")
CHAT=os.getenv("CHAT_ID")
ENTRY=120
TGT1,TGT2,SL=155,195,78
MIN_ACC=70
VIX_MAX=18

# ============ PURUNA CODE - NO CHANGE ============
def fetch_live_nifty():
    if YF:
        try:
            d=yf.Ticker("^NSEI").history(period="1mo",interval="1d")
            if len(d)>=20:
                o=float(d['Open'].iloc[-1]); h=float(d['High'].iloc[-1]); l=float(d['Low'].iloc[-1]); c=float(d['Close'].iloc[-1])
                po=float(d['Open'].iloc[-2]); pc=float(d['Close'].iloc[-2])
                vol=float(d['Volume'].iloc[-1]); avg=float(d['Volume'].tail(20).mean())
                vix=float(yf.Ticker("^INDIAVIX").history(period="1d")['Close'].iloc[-1])
                return o,h,l,c,po,pc,vol,avg,vix,1.05,"BUY","BUY",c
        except: pass
    return 25150,25240,25170,25220,25200,25160,150000,100000,13.2,1.05,"BUY","BUY",25220

def fetch_live_bank():
    if YF:
        try:
            d=yf.Ticker("^NSEBANK").history(period="1mo",interval="1d")
            if len(d)>=20:
                o=float(d['Open'].iloc[-1]); h=float(d['High'].iloc[-1]); l=float(d['Low'].iloc[-1]); c=float(d['Close'].iloc[-1])
                po=float(d['Open'].iloc[-2]); pc=float(d['Close'].iloc[-2])
                vol=float(d['Volume'].iloc[-1]); avg=float(d['Volume'].tail(20).mean())
                return o,h,l,c,po,pc,vol,avg,c
        except: pass
    return 52200,52400,52100,52300,52250,52150,120000,90000,52300

def check_pattern_CE(o,h,l,c,po,pc,vol,avg):
    body=abs(c-o)
    if (h-l)==0: return {"signal":False,"pat":"None"}
    lw=min(o,c)-l
    uw=h-max(o,c)
    bull=(pc<po) and (c>o) and (c>po) and (o<pc)
    ham=(lw>body*2) and (uw<body*0.3) and (body>0)
    vok=vol>avg*1.2
    doji=body<(h-l)*0.1
    if doji: return {"signal":False,"pat":"DOJI"}
    if (bull or ham) and vok:
        return {"signal":True,"pat":"BULL-ENGULF" if bull else "HAMMER"}
    return {"signal":False,"pat":"No Pattern"}

def build_msg_CE(nifty,bank,acc,pat):
    return f"""💯 🔱 MASTER LIVE - NIFTY + BANK CE | {datetime.now().strftime('%I:%M %p')} 🔱
📊 NIFTY: {nifty:.0f} | BANK: {bank:.0f} | Acc: {acc}% 
Pattern: {pat} BULL ✅
🟢 NIFTY {round(nifty/50)*50} CE BUY
🟢 BANK {round(bank/100)*100} CE BUY
ENTRY {ENTRY} TGT1 {TGT1} TGT2 {TGT2} SL {SL}
🔱 JAI JAGANNATH"""

def calculate_acc(c_ok,s15,s5,vix_ok,pcr_ok,vol_ok):
    sc=0
    if c_ok: sc+=30
    if s15: sc+=25
    if s5: sc+=25
    if vix_ok and pcr_ok and vol_ok: sc+=20
    return sc

# ============ NUA ADD - PE - PURUNA DELETE NAHI ============
def check_pattern_PE(o,h,l,c,po,pc,vol,avg):
    body=abs(c-o)
    if (h-l)==0: return {"signal":False,"pat":"None"}
    uw=h-max(o,c)
    bear=(pc>po) and (c<o) and (c<po) and (o>pc)
    star=(uw>body*2) and (body<(h-l)*0.4) and (body>0)
    vok=vol>avg*1.2
    doji=body<(h-l)*0.1
    if doji: return {"signal":False,"pat":"DOJI"}
    if (bear or star) and vok:
        return {"signal":True,"pat":"BEAR-ENGULF" if bear else "SHOOT-STAR"}
    return {"signal":False,"pat":"No Pattern"}

def build_msg_PE(nifty,bank,acc,pat):
    return f"""🔴 🔱 MASTER LIVE - NIFTY + BANK PE | {datetime.now().strftime('%I:%M %p')} 🔱
📊 NIFTY: {nifty:.0f} | BANK: {bank:.0f} | Acc: {acc}% 
Pattern: {pat} BEAR 🔴
🔴 NIFTY {round(nifty/50)*50} PE BUY
🔴 BANK {round(bank/100)*100} PE BUY
ENTRY {ENTRY} TGT1 {TGT1} TGT2 {TGT2} SL {SL}
🔱 JAI JAGANNATH"""

def build_msg_MIX(nifty,bank,acc_n,acc_b,pat_n,pat_b,dir_n,dir_b):
    return f"""💯 🔱 MASTER LIVE - 4 IN 1 | {datetime.now().strftime('%I:%M %p')} 🔱
📊 NIFTY: {nifty:.0f} ({dir_n}) {pat_n} {acc_n}% 
📊 BANK: {bank:.0f} ({dir_b}) {pat_b} {acc_b}%
{ '🟢' if dir_n=='CE' else '🔴' } NIFTY {round(nifty/50)*50} {dir_n} BUY
{ '🟢' if dir_b=='CE' else '🔴' } BANK {round(bank/100)*100} {dir_b} BUY
ENTRY {ENTRY} TGT1 {TGT1} TGT2 {TGT2} SL {SL}
🔱 JAI JAGANNATH"""

# ============ PURUNA FINAL - UPDATE ONLY ADD ============
async def final_master(context):
    o,h,l,c,po,pc,vol,avg,vix,pcr,st15,st5,n_price = fetch_live_nifty()
    bo,bh,bl,bc,bpo,bpc,bvol,bavg,b_price = fetch_live_bank()
    
    if vix>VIX_MAX:
        print(f"VIX HIGH {vix} SKIP")
        return False,0,"VIX-HIGH"
    
    # PURUNA CE CHECK - NO CHANGE
    ce_n = check_pattern_CE(o,h,l,c,po,pc,vol,avg)
    ce_b = check_pattern_CE(bo,bh,bl,bc,bpo,bpc,bvol,bavg)
    
    # NUA PE CHECK - ADD
    pe_n = check_pattern_PE(o,h,l,c,po,pc,vol,avg)
    pe_b = check_pattern_PE(bo,bh,bl,bc,bpo,bpc,bvol,bavg)
    
    # ACC CALCULATE
    s15_ok = st15=="BUY"
    s5_ok = st5=="BUY"
    s15_ok_pe = st15=="SELL"
    s5_ok_pe = st5=="SELL"
    vix_ok = vix<14
    pcr_ok = pcr>1.0
    vol_ok = vol>avg
    bvol_ok = bvol>bavg
    
    acc_ce_n = calculate_acc(ce_n["signal"], s15_ok, s5_ok, vix_ok, pcr_ok, vol_ok)
    acc_ce_b = calculate_acc(ce_b["signal"], s15_ok, s5_ok, vix_ok, pcr_ok, bvol_ok)
    acc_pe_n = calculate_acc(pe_n["signal"], s15_ok_pe, s5_ok_pe, vix_ok, pcr_ok, vol_ok)
    acc_pe_b = calculate_acc(pe_b["signal"], s15_ok_pe, s5_ok_pe, vix_ok, pcr_ok, bvol_ok)
    
    # DECIDE BEST DIR
    dir_n = "CE" if acc_ce_n >= acc_pe_n else "PE"
    dir_b = "CE" if acc_ce_b >= acc_pe_b else "PE"
    best_acc_n = max(acc_ce_n, acc_pe_n)
    best_acc_b = max(acc_ce_b, acc_pe_b)
    best_pat_n = ce_n["pat"] if dir_n=="CE" else pe_n["pat"]
    best_pat_b = ce_b["pat"] if dir_b=="CE" else pe_b["pat"]
    
    avg_acc = (best_acc_n + best_acc_b)//2
    
    # DATA SAVE
    try:
        json.dump({"nifty":n_price,"bank":b_price,"acc_n":best_acc_n,"acc_b":best_acc_b,"avg":avg_acc,"dir_n":dir_n,"dir_b":dir_b,"pat_n":best_pat_n,"pat_b":best_pat_b,"vix":vix,"time":datetime.now().strftime("%H:%M")}, open('data.json','w'))
    except: pass
    
    if avg_acc >= MIN_ACC and (ce_n["signal"] or pe_n["signal"] or ce_b["signal"] or pe_b["signal"]):
        msg = build_msg_MIX(n_price,b_price,best_acc_n,best_acc_b,best_pat_n,best_pat_b,dir_n,dir_b)
        await context.bot.send_message(chat_id=CHAT, text=msg)
        print(f"✅ MASTER SENT {dir_n}/{dir_b} N:{best_acc_n}% B:{best_acc_b}% AVG:{avg_acc}%")
        return True, avg_acc, f"{best_pat_n}/{best_pat_b} {dir_n}/{dir_b}"
    
    print(f"SKIP N CE:{acc_ce_n}% PE:{acc_pe_n}% B CE:{acc_ce_b}% PE:{acc_pe_b}% AVG:{avg_acc}%")
    return False, avg_acc, "No Pattern"

class DummyContext:
    def __init__(self,bot):
        self.bot=bot

async def github_run():
    bot=Bot(token=BOT)
    ctx=DummyContext(bot)
    print("✅ MASTER LIVE CE+PE 4 IN 1 START")
    for i in range(13):
        if i==0:
            print("⏳ 10min skip")
            await asyncio.sleep(600)
            continue
        ok,acc,pat = await final_master(ctx)
        if ok:
            print(f"✅ DONE {pat} {acc}%")
            return
        print(f"⏳ Try {i+1}/13 Acc {acc}% <70% Wait 10min")
        if i<12:
            await asyncio.sleep(600)
    print("❌ 11:15 heigala")

def main():
    if os.getenv("GITHUB_ACTIONS")=="true":
        asyncio.run(github_run())
    else:
        app=Application.builder().token(BOT).build()
        app.job_queue.run_daily(lambda ctx: asyncio.create_task(github_run()), time=time(hour=3,minute=45))
        print("✅ LOCAL MASTER CE+PE")
        app.run_polling()

if __name__=="__main__":
    main()
