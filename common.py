import os, requests, pandas as pd

TD_KEY = os.environ.get("TD_KEY", "")
TG_TOKEN = os.environ.get("TG_TOKEN", "")
TG_CHAT = os.environ.get("TG_CHAT", "")

def fetch(interval, size, symbol="XAU/USD"):
    out, end = [], None
    while size > 0:
        n = min(size, 5000)
        p = dict(symbol=symbol, interval=interval, outputsize=n,
                 apikey=TD_KEY, order="DESC")
        if end: p["end_date"] = end
        r = requests.get("https://api.twelvedata.com/time_series",
                         params=p, timeout=60).json()
        if "values" not in r:
            if out: break
            raise RuntimeError(r)
        out += r["values"]
        size -= n
        end = r["values"][-1]["datetime"]
        if len(r["values"]) < n: break
    df = pd.DataFrame(out)
    df["time"] = pd.to_datetime(df["datetime"])
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c].astype(float)
    df = df.drop_duplicates("time").sort_values("time").reset_index(drop=True)
    return df[["time", "open", "high", "low", "close"]]

def send(text):
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  data={"chat_id": TG_CHAT, "text": text}, timeout=30)
