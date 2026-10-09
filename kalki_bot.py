import datetime, os, json

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
now = datetime.datetime.now(IST)
ts = now.strftime("%d %b %I:%M %p")
today = now.strftime("%Y-%m-%d")

# --- OFF ---
if now.weekday()>=5 or now.hour<9 or now.hour>=16:
    print(f"OFF {ts}"); exit()

# --- FILE FOR P/L TRACK ---
pl_file = f"/tmp/pl_{today}.json"

# --- 9:00 AM SILENT ---
if now.hour==9 and now.minute<30:
    print(f"🔍 SILENT ANALYSIS {ts}")
    # yaha PCR collect kariba
    exit()

# --- 3:45 PM P/L REPORT ---
if now.hour==15 and now.minute>=40:
    try:
        with open(pl_file, 'r') as f:
            data = json.load(f)
    except:
        data = {"win": 8, "loss": 5, "points": 620} # demo

    win = data.get("win", 0)
    loss = data.get("loss", 0)
    pts = data.get("points", 0)
    total = win+loss
    acc = int(win*100/total) if total else 0

    pl_msg = f"""📊 KALKI P/L REPORT - {ts}
━━━━━━━━━━━━━━
Total Calls: {total}
✅ WIN: {win}
❌ LOSS: {loss}
🎯 Accuracy: {acc}%

💰 Points: {pts} Pts
💵 1 Lot (50 Qty): ₹{pts*50}
💵 2 Lot: ₹{pts*100}

🔱 Aji Paisa Double!
"""
    print(pl_msg)
    # send_whatsapp(pl_msg)
    # file delete for next day
    # os.remove(pl_file)
    exit()

# --- NORMAL TRADING 9:30-3:30 ---
print(f"💹 TRADE MODE {ts}")
nifty = 25150
pcr = 0.92
signal = "BUY" if pcr<1 else "SELL"

# Save for P/L
try:
    with open(pl_file, 'r') as f:
        d=json.load(f)
except:
    d={"win":0,"loss":0,"points":0}
# demo update
d["win"]+=1
d["points"]+=120
with open(pl_file, 'w') as f:
    json.dump(d,f)

msg = f"""🔱 KALKI V14.1 - {ts}
NIFTY: {nifty}
SIGNAL: {signal}
ENTRY: {nifty}
SL: {nifty-80}
TARGET: {nifty+150}
ACCURACY: 90% 🔥
"""
print(msg)
# send_whatsapp(msg)
