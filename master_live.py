import yfinance as yf, json, os, requests
BOT=os.getenv("BOT_TOKEN"); CHAT=os.getenv("CHAT_ID")
def send(m):
  try: requests.post(f"https://api.telegram.org/bot{BOT}/sendMessage", json={"chat_id":CHAT,"text":m,"parse_mode":"HTML"}, timeout=10)
  except: pass
def intraday():
  try:
    d=yf.Ticker("^NSEI").history(period="1d", interval="5m")
    o=float(d['Open'].iloc[0]); l=float(d['Close'].iloc[-1])
    return l, l-o, True
  except: return 0,0,False
def main():
  try: d=json.load(open('data.json'))
  except: return
  live,move,ok = intraday()
  if not ok: return
  opt = 120 + move*0.48
  if opt >= 195: send(f"🤑 TGT2 HIT! ENTRY 120 → {opt:.0f} MOVE {move:+.0f} FULL +₹5625"); return
  if opt >= 155: send(f"🎯 TGT1 HIT! ENTRY 120 → {opt:.0f} MOVE {move:+.0f} +₹2625 50% BOOK"); return
  if opt <= 78: send(f"🛑 SL HIT! ENTRY 120 → {opt:.0f} LOSS -₹3150"); return
if __name__=="__main__": main()
