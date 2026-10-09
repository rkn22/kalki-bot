import requests, yfinance as yf, pytz, os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ===== PCR DATA =====
def get_pcr(sym):
    try:
        s=requests.Session(); h={"User-Agent":"Mozilla/5.0","Referer":"https://www.nseindia.com/option-chain"}
        s.get("https://www.nseindia.com", headers=h, timeout=10)
        r=s.get(f"https://www.nseindia.com/api/option-chain-indices?symbol={sym}", headers=h, timeout=10).json()
        spot=r['records']['underlyingValue']; data=r['records']['data']
        t_ce=t_pe=0
        for i in data:
            if 'CE' in i: t_ce+=i['CE']['openInterest']
            if 'PE' in i: t_pe+=i['PE']['openInterest']
        pcr=round(t_pe/t_ce,2) if t_ce else 0
        if pcr>1.2: tr="STRONG BULLISH"
        elif pcr>1.05: tr="BULLISH"
        elif pcr<0.8: tr="STRONG BEARISH"
        elif pcr<0.95: tr="BEARISH"
        else: tr="SIDEWAYS"
        return {"spot":spot,"pcr":pcr,"tr":tr,"t_ce":round(t_ce/1e5,1),"t_pe":round(t_pe/1e5,1)}
    except:
        return {"spot":0,"pcr":0,"tr":"CLOSED","t_ce":0,"t_pe":0}

# ===== SCALP SIGNAL =====
def get_scalp(ysym):
    try:
        df=yf.download(ysym, period="1d", interval="5m", progress=False)
        close=df['Close']; ema9=close.ewm(9).mean().iloc[-1]; ema21=close.ewm(21).mean().iloc[-1]
        delta=close.diff(); gain=(delta.where(delta>0,0)).rolling(14).mean(); loss=(-delta.where(delta<0,0)).rolling(14).mean()
        rsi=100-(100/(1+gain/loss)); rsi_val=float(rsi.iloc[-1]); price=float(close.iloc[-1])
        vwap=float((df['Close']*df['Volume']).sum()/df['Volume'].sum())
        is_bank="BANK" in ysym; mult=80 if is_bank else 40
        if price>ema9>ema21 and rsi_val>55 and price>vwap:
            sig="🚀 BUY"; sl=price-mult; t1=price+mult; sc=85
        elif price<ema9<ema21 and rsi_val<45 and price<vwap:
            sig="🔻 SELL"; sl=price+mult; t1=price-mult; sc=85
        else:
            sig="⚠️ WAIT"; sl=0; t1=0; sc=50
        return {"price":round(price,1),"sig":sig,"ema9":round(float(ema9),1),"ema21":round(float(ema21),1),"rsi":round(rsi_val,1),"vwap":round(vwap,1),"sl":round(sl,1),"t1":round(t1,1),"sc":sc}
    except: return {"price":0,"sig":"WAIT","ema9":0,"ema21":0,"rsi":0,"vwap":0,"sl":0,"t1":0,"sc":0}

def full_report():
    ist=pytz.timezone('Asia/Kolkata'); now=datetime.now(ist).strftime("%d %b %I:%M %p")
    nf_pcr=get_pcr("NIFTY"); bn_pcr=get_pcr("BANKNIFTY")
    nf_sc=get_scalp("^NSEI"); bn_sc=get_scalp("^NSEBANK")
    return f"""🔱 KALKI ULTIMATE ⏰ {now}

=== 1. NIFTY SPOT {nf_pcr['spot']} ===
PCR {nf_pcr['pcr']} {nf_pcr['tr']} | CE {nf_pcr['t_ce']}L PE {nf_pcr['t_pe']}L
SCALP: {nf_sc['sig']} {nf_sc['sc']}% | Price {nf_sc['price']} RSI {nf_sc['rsi']}
EMA9 {nf_sc['ema9']} EMA21 {nf_sc['ema21']} VWAP {nf_sc['vwap']}
Entry {nf_sc['price']} SL {nf_sc['sl']} TGT {nf_sc['t1']}

📋 CHECKLIST: {'✅ PCR>1.05' if nf_pcr['pcr']>1.05 else '❌ PCR Bearish'} | {'✅ RSI>55' if nf_sc['rsi']>55 else '❌ RSI<45' if nf_sc['rsi']<45 else '⚠️ RSI Mid'}

=== 2. BANKNIFTY SPOT {bn_pcr['spot']} ===
PCR {bn_pcr['pcr']} {bn_pcr['tr']} | CE {bn_pcr['t_ce']}L PE {bn_pcr['t_pe']}L
SCALP: {bn_sc['sig']} {bn_sc['sc']}% | Price {bn_sc['price']} RSI {bn_sc['rsi']}
EMA9 {bn_sc['ema9']} EMA21 {bn_sc['ema21']} VWAP {bn_sc['vwap']}
Entry {bn_sc['price']} SL {bn_sc['sl']} TGT {bn_sc['t1']}

📋 CHECKLIST: {'✅ PCR>1.05' if bn_pcr['pcr']>1.05 else '❌ PCR Bearish'} | {'✅ BUY Setup' if bn_sc['sig']=='🚀 BUY' else '✅ SELL Setup' if bn_sc['sig']=='🔻 SELL' else '⚠️ WAIT'}

🔥 FINAL VERDICT: {bn_pcr['tr']} + {bn_sc['sig']} = {'STRONG BUY' if 'BULLISH' in bn_pcr['tr'] and 'BUY' in bn_sc['sig'] else 'STRONG SELL' if 'BEARISH' in bn_pcr['tr'] and 'SELL' in bn_sc['sig'] else 'SIDEWAYS - NO TRADE'}
"""

async def start(u,c): await u.message.reply_text("🔱 ULTIMATE READY!\n/report - Full PCR+Scalp\n/pcr - Only PCR\n/scalp - Only Scalp\n/nifty /bank")
async def report(u,c): await u.message.reply_text(full_report())
async def pcr(u,c): 
    nf=get_pcr("NIFTY"); bn=get_pcr("BANKNIFTY")
    await u.message.reply_text(f"NIFTY PCR {nf['pcr']} {nf['tr']}\nBANK PCR {bn['pcr']} {bn['tr']}")
async def scalp(u,c):
    nf=get_scalp("^NSEI"); bn=get_scalp("^NSEBANK")
    await u.message.reply_text(f"NIFTY {nf['sig']} RSI {nf['rsi']} SL {nf['sl']} TGT {nf['t1']}\nBANK {bn['sig']} RSI {bn['rsi']} SL {bn['sl']} TGT {bn['t1']}")
async def handle(u,c): await u.message.reply_text(full_report())

app=Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("report", report))
app.add_handler(CommandHandler("pcr", pcr))
app.add_handler(CommandHandler("scalp", scalp))
app.add_handler(CommandHandler("nifty", report))
app.add_handler(CommandHandler("bank", report))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
print("Ultimate Bot Started")
app.run_polling()
