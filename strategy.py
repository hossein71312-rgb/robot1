import pandas as pd

def atr(df, n=14):
    pc = df.close.shift()
    tr = pd.concat([df.high - df.low, (df.high - pc).abs(),
                    (df.low - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def swings(df, n):
    h, l = df.high.values, df.low.values
    sh, sl = [], []
    for i in range(n, len(df) - n):
        if h[i] == max(h[i - n:i + n + 1]): sh.append((i, h[i]))
        if l[i] == min(l[i - n:i + n + 1]): sl.append((i, l[i]))
    return sh, sl

def trend_4h(df):
    """1=صعودی (HH+HL)  -1=نزولی (LH+LL)  0=نامشخص"""
    sh, sl = swings(df, 2)
    if len(sh) < 2 or len(sl) < 2: return 0
    if sh[-1][1] > sh[-2][1] and sl[-1][1] > sl[-2][1]: return 1
    if sh[-1][1] < sh[-2][1] and sl[-1][1] < sl[-2][1]: return -1
    return 0

def zones_1h(df, d):
    """FVG و Order Block حل‌نشده، فقط در Discount (خرید) یا Premium (فروش)"""
    df = df.tail(80).reset_index(drop=True)
    body = (df.close - df.open).abs()
    zs = []
    for i in range(2, len(df) - 1):
        if d == 1 and df.low[i] > df.high[i - 2]:
            zs.append((df.high[i - 2], df.low[i], "FVG", i))
        if d == -1 and df.high[i] < df.low[i - 2]:
            zs.append((df.high[i], df.low[i - 2], "FVG", i))
        big = body[i] > 1.5 * body[max(0, i - 20):i].mean()
        if big and d == 1 and df.close[i] > df.open[i] and df.close[i - 1] < df.open[i - 1]:
            zs.append((df.low[i - 1], df.high[i - 1], "OB", i))
        if big and d == -1 and df.close[i] < df.open[i] and df.close[i - 1] > df.open[i - 1]:
            zs.append((df.low[i - 1], df.high[i - 1], "OB", i))
    mid = (df.high.max() + df.low.min()) / 2
    out = []
    for lo, hi, k, i in zs:
        later = df.iloc[i + 1:]
        if d == 1 and ((later.close < lo).any() or lo > mid): continue
        if d == -1 and ((later.close > hi).any() or hi < mid): continue
        out.append((lo, hi, k))
    return out

def entry_5m(df, d, zones, rr=2.0):
    """لمس ناحیه + Liquidity Sweep + CHoCH"""
    d5 = df.tail(40).reset_index(drop=True)
    rec, prior = d5.tail(10), d5.iloc[:-10]
    z = next((z for z in zones if rec.low.min() <= z[1] and rec.high.max() >= z[0]), None)
    if z is None: return None
    a = atr(d5).iloc[-1]
    last = d5.iloc[-1]
    if d == 1:
        if not rec.low.min() < prior.tail(20).low.min(): return None
        k = rec.low.idxmin()
        if k >= len(d5) - 1 or not last.close > d5.high[max(0, k - 3):k + 1].max(): return None
        sl = rec.low.min() - 0.1 * a
        risk = last.close - sl
        if risk <= 0 or risk > 3 * a: return None
        return dict(side="BUY", entry=last.close, sl=sl, tp=last.close + rr * risk, zone=z[2], rr=rr)
    else:
        if not rec.high.max() > prior.tail(20).high.max(): return None
        k = rec.high.idxmax()
        if k >= len(d5) - 1 or not last.close < d5.low[max(0, k - 3):k + 1].min(): return None
        sl = rec.high.max() + 0.1 * a
        risk = sl - last.close
        if risk <= 0 or risk > 3 * a: return None
        return dict(side="SELL", entry=last.close, sl=sl, tp=last.close - rr * risk, zone=z[2], rr=rr)

def signal(df4, df1, df5):
    if len(df4) < 20 or len(df1) < 60 or len(df5) < 40: return None
    d = trend_4h(df4)
    if d == 0: return None
    zs = zones_1h(df1, d)
    if not zs: return None
    return entry_5m(df5, d, zs)
