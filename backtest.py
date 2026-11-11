import numpy as np, pandas as pd
from common import fetch
from strategy import signal, SESSION, STATS

df5 = fetch("5min", 15000).reset_index(drop=True)
print("کندل‌ها:", len(df5), df5.time.iloc[0], "تا", df5.time.iloc[-1])

def rs(rule):
    r = df5.resample(rule, on="time").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    r["end"] = r.index + pd.Timedelta(rule)
    return r
H1, H4 = rs("1h"), rs("4h")
e1, e4 = H1.end.values, H4.end.values

sigs = []
for i in range(1000, len(df5) - 1):
    t0 = df5.time[i]
    if not (SESSION[0] <= t0.hour < SESSION[1]): continue
    t = np.datetime64(t0 + pd.Timedelta("5min"))
    j1 = np.searchsorted(e1, t, side="right")
    j4 = np.searchsorted(e4, t, side="right")
    d1 = H1.iloc[max(0, j1 - 150):j1].reset_index()
    d4 = H4.iloc[max(0, j4 - 60):j4].reset_index()
    s = signal(d4, d1, df5.iloc[i - 59:i + 1])
    if s:
        s["i"], s["time"] = i, t0
        sigs.append(s)

H, L = df5.high.values, df5.low.values

def sim(rr):
    res, busy = [], -1
    for s in sigs:
        i = s["i"]
        if i <= busy: continue
        buy = s["side"] == "BUY"
        risk = abs(s["entry"] - s["sl"])
        tp = s["entry"] + rr * risk if buy else s["entry"] - rr * risk
        r = None
        for j in range(i + 1, len(H)):
            hit_sl = L[j] <= s["sl"] if buy else H[j] >= s["sl"]
            hit_tp = H[j] >= tp if buy else L[j] <= tp
            if hit_sl: r = -1; break
            if hit_tp: r = rr; break
        if r is None: break
        res.append((s, r, tp)); busy = j
    return res

print("\nقیف فیلترها (تعداد کندل‌هایی که از هر مرحله رد شدند):")
for k, v in STATS.items(): print(" ", k, v)
print("  سیگنال نهایی", len(sigs))

print("\nنتیجه برای نسبت‌های مختلف ریسک به ریوارد:")
for rr in (1, 1.5, 2, 3):
    rl = [r for _, r, _ in sim(rr)]
    n = len(rl)
    if not n:
        print(f"RR={rr}: بدون معامله"); continue
    eq = np.cumsum(rl); dd = (np.maximum.accumulate(eq) - eq).max()
    print(f"RR={rr}: معامله={n} برد={sum(r > 0 for r in rl) / n * 100:.0f}% "
          f"سود={sum(rl):.1f}R افت={dd:.1f}R")

print("\nجزئیات معاملات (RR=2):")
for s, r, tp in sim(2):
    print(s["time"], s["side"], round(s["entry"], 2), round(s["sl"], 2),
          round(tp, 2), "برد" if r > 0 else "ضرر")
