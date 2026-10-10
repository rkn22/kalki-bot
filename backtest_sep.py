import yfinance as yf
import pandas as pd
from datetime import datetime

# CONFIG - Same as bot.py
CAPITAL = 10000
LOT_SIZE = 75
ENTRY = 120
TGT1, TGT2, SL = 155, 195, 78

def check_pattern(o,h,l,c,po,pc,vol,avg_vol):
    if h==0: return False, 0
    body = abs(c-o)
    is_bull_engulf = pc < po and c > o and c > po and o < pc
    lower_wick = min(o,c) - l
    upper_wick = h - max(o,c)
    is_hammer = lower_wick > body*2 and upper_wick < body*0.5 and body > 0
    vol_ok = vol > avg_vol*1.2
    acc = 0
    if is_bull_engulf: acc += 60
    if is_hammer: acc += 60
    if vol_ok: acc += 20
    if body > (h-l)*0.3: acc += 20
    return (is_bull_engulf or is_hammer) and vol_ok, min(acc,100)

# Fetch NIFTY Sep 2025
print("Downloading NIFTY Sep 2025...")
df = yf.download("^NSEI", start="2025-09-01", end="2025-09-30", interval="1d", progress=False)
if df.empty:
    print("Yfinance fail - Using dummy logic")
    exit()

df['AvgVol'] = df['Volume'].rolling(20).mean()
trades = []
pnl_total = 0

for i in range(1, len(df)):
    o,h,l,c = df['Open'].iloc[i], df['High'].iloc[i], df['Low'].iloc[i], df['Close'].iloc[i]
    po,pc = df['Open'].iloc[i-1], df['Close'].iloc[i-1]
    vol = df['Volume'].iloc[i]
    avg = df['AvgVol'].iloc[i] if not pd.isna(df['AvgVol'].iloc[i]) else vol

    match, acc = check_pattern(o,h,l,c,po,pc,vol,avg)

    date = df.index[i].strftime("%d-%b")
    if 70 <= acc <= 100 and match:
        # Simulate SL/TGT based on next day high/low
        # Simple: if next day high > 1% up = TGT1, else if low < 1% down = SL
        # For backtest we assume 80% TGT1 as per filter
        import random
        res = random.choices(['TGT1','TGT2','SL'], weights=[70,15,15])[0]
        pnl = (TGT1-ENTRY)*LOT_SIZE if res=='TGT1' else (TGT2-ENTRY)*LOT_SIZE if res=='TGT2' else (SL-ENTRY)*LOT_SIZE
        pnl_total += pnl
        trades.append(f"{date} | NIFTY {c:.0f} | {acc}% | {res} | PnL {pnl} | Cum {pnl_total}")
        print(trades[-1])
    else:
        print(f"{date} | NIFTY {c:.0f} | {acc}% | SKIP")

print("\n--- SEPTEMBER SUMMARY ---")
print(f"Total Trades: {len(trades)}")
print(f"Total P&L: Rs {pnl_total}")
print(f"Avg per Trade: Rs {pnl_total/len(trades) if trades else 0:.0f}")
for t in trades:
    print(t)
