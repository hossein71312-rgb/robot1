import json, os
import pandas as pd
from common import fetch, send
from strategy import signal

df5 = fetch("5min", 1500).iloc[:-1].reset_index(drop=True)
now = df5.time.iloc[-1] + pd.Timedelta("5min")

def rs(rule):
    r = df5.resample(rule, on="time").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    r = r[r.index + pd.Timedelta(rule) <= now]
    return r.reset_index()

s = signal(rs("4h"), rs("1h"), df5)
if s:
    st = json.load(open("state.json")) if os.path.exists("state.json") else {}
    last = pd.Timestamp(st["t"]) if "t" in st else None
    if st.get("side") == s["side"] and last is not None and now - last < pd.Timedelta("1h"):
        print("سیگنال تکراری")
    else:
        e = "🟢" if s["side"] == "BUY" else "🔴"
        send(f"{e} {s['side']} طلا (XAUUSD)\n"
             f"ورود: {s['entry']:.2f}\nحد ضرر: {s['sl']:.2f}\n"
             f"تارگت: {s['tp']:.2f}  (R:R = 1:{s['rr']:.0f})\n"
             f"ناحیه ۱ساعته: {s['zone']}\nزمان کندل: {now} UTC\n"
             f"⚠️ ممکن است چند دقیقه تأخیر داشته باشد؛ قبل از ورود قیمت را چک کنید")
        json.dump({"side": s["side"], "t": str(now)}, open("state.json", "w"))
else:
    print("سیگنالی نیست")
