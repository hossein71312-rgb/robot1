import numpy as np, pandas as pd
from common import fetch
from strategy import signal

df5 = fetch("5min", 5000)
def rs(rule):
    r = df5.resample(rule, on="time").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    r["end"] = r.index + pd.Timedelta(rule)
    return r
H1, H4 = rs("1h"), rs("4h")
e1, e4 = H1.end.values, H4.end.values

def outcome(i, s):
    for j in range(i + 1, len(df5)):
        h, l = df5.high[j], df5.low[j]
        if s["side"] == "BUY":
            if l <= s["sl"]: return -1, j
            if h >= s["tp"]: return s["rr"], j
        else:
            if h >= s["sl"]: return -1, j
            if l <= s["tp"]: return s["rr"], j
    return None, len(df5)

res, i = [], 1000
while i < len(df5) - 1:
    t = np.datetime64(df5.time[i] + pd.Timedelta("5min"))
    d1 = H1.iloc[:np.searchsorted(e1, t, side="right")].reset_index()
    d4 = H4.iloc[:np.searchsorted(e4, t, side="right")].reset_index()
    s = signal(d4, d1, df5.iloc[i - 59:i + 1])
    if s:
        r, j = outcome(i, s)
        if r is None: break
        res.append(r); i = j
    i += 1

n = len(res)
if n:
    eq = np.cumsum(res); dd = (np.maximum.accumulate(eq) - eq).max()
    print(f"تعداد معامله: {n}\nدرصد برد: {sum(r > 0 for r in res) / n * 100:.1f}%")
    print(f"مجموع سود (R): {sum(res):.1f}\nحداکثر افت (R): {dd:.1f}")
else:
    print("سیگنالی پیدا نشد")
