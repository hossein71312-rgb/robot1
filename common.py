import os, requests, pandas as pd

TD_KEY = os.environ.get("TD_KEY", "")
TG_TOKEN = os.environ.get("TG_TOKEN", "")
TG_CHAT = os.environ.get("TG_CHAT", "")

def fetch(interval, size, symbol="XAU/USD"):
    r = requests.get("https://api.twelvedata.com/time_series", params=dict(
        symbol=symbol, interval=interval, outputsize=size,
        apikey=TD_KEY, order="ASC"), timeout=30).json()
    if "values" not in r:
        raise RuntimeError(r)
    df = pd.DataFrame(r["values"])
    df["time"] = pd.to_datetime(df["datetime"])
    for c in ["open", "high", "low", "close"]:
        df[c] = df[c].astype(float)
    return df[["time", "open", "high", "low", "close"]]

def send(text):
    requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
                  data={"chat_id": TG_CHAT, "text": text}, timeout=30)
