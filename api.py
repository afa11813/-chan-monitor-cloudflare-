import time, requests, pandas as pd, numpy as np
from datetime import datetime, timezone

def fetch_okx_kline(symbol="BTC-USDT-SWAP", bar="15m", limit=100):
    url = "https://www.okx.com/api/v5/market/history-candles"
    r = requests.get(url, params={"instId": symbol, "bar": bar, "limit": limit})
    r.raise_for_status()
    data = r.json()["data"]
    df = pd.DataFrame(data, columns=["ts","o","h","l","c","v","volCcy","volCcyQuote","confirm"])
    df = df.astype(float)
    df["time"] = pd.to_datetime(df["ts"], unit="ms", utc=True).dt.tz_convert("Asia/Shanghai")
    return df.sort_values("time")

def detect_bottom_fractal(df):
    lows = df["l"].values
    res = []
    for i in range(1, len(lows)-1):
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            res.append((df["time"].iloc[i], lows[i]))
    return res

def detect_top_fractal(df):
    highs = df["h"].values
    res = []
    for i in range(1, len(highs)-1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            res.append((df["time"].iloc[i], highs[i]))
    return res

def bollinger(df, n=21, k=2):
    mid = df["c"].rolling(n).mean()
    std = df["c"].rolling(n).std()
    return mid, mid + k*std, mid - k*std

def check_signal(df):
    mid, up, low = bollinger(df)
    last = df.iloc[-1]
    top = detect_top_fractal(df)
    bottom = detect_bottom_fractal(df)
    msg = None
    if bottom and last["c"] < low.iloc[-1]:
        msg = f"📈 底分型靠近下轨：{last['c']:.2f}"
    elif top and last["c"] > up.iloc[-1]:
        msg = f"📉 顶分型靠近上轨：{last['c']:.2f}"
    return msg

if __name__ == "__main__":
    print("启动 OKX 缠论监控系统...")
    while True:
        try:
            df = fetch_okx_kline()
            msg = check_signal(df)
            if msg:
                print(f"[{datetime.now(timezone.utc).astimezone()}] {msg}")
        except Exception as e:
            print("错误:", e)
        time.sleep(600)  # 每 10 分钟检测一次
