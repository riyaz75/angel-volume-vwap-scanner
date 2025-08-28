import os
import time
import json
import pandas as pd
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load config
load_dotenv("config.env")

API_KEY = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD = os.getenv("ANGEL_PASSWORD")
EXCHANGE = os.getenv("EXCHANGE", "NSE")

INTERVAL = int(os.getenv("INTERVAL_MINUTES", "5"))
AVG_BARS = int(os.getenv("AVG_BARS", "30"))
VOL_MULT = float(os.getenv("VOLUME_MULTIPLIER", "3"))

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ---- Helpers ----
def send_telegram(msg: str):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("[!] Telegram not configured")
        return
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg})
    except Exception as e:
        print("Telegram error:", e)

def load_tokens():
    with open("OpenAPIScripMaster.json","r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)

    with open("watchlist.txt") as f:
        symbols = [s.strip() for s in f if s.strip()]
    # Some versions use 'exch_seg' instead of 'exchange'
    col_exchange = "exchange" if "exchange" in df.columns else "exch_seg"

    watch = df[(df[col_exchange]==EXCHANGE) & (df["symbol"].isin(symbols))]


    #watch = df[(df["exchange"]==EXCHANGE) & (df["symbol"].isin(symbols))]
    return dict(zip(watch["symbol"], watch["token"]))

def get_5min_data(symbol, token, jwt_token):
    url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/market/v1/history"
    headers = {
        "X-PrivateKey": os.getenv("ANGEL_API_KEY"),
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "exchange": "NSE",
        "symboltoken": token,
        "interval": "FIVE_MINUTE",
        "fromdate": (datetime.now() - pd.Timedelta(minutes=5*30)).strftime("%Y-%m-%d %H:%M"),
        "todate": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    resp = requests.post(url, json=payload, headers=headers).json()
    candles = resp.get("data", {}).get("candles", [])
    df = pd.DataFrame(candles, columns=["datetime","open","high","low","close","volume"])
    return df

    # Example DataFrame with OHLCV + datetime
    now = datetime.now()
    df = pd.DataFrame({
        "datetime": pd.date_range(now.replace(second=0, microsecond=0)-pd.Timedelta(minutes=5*AVG_BARS),
                                  periods=AVG_BARS+1, freq="5min"),
        "close": [100+i*0.1 for i in range(AVG_BARS+1)],
        "volume": [1000+(i%5)*200 for i in range(AVG_BARS+1)]
    })
    return df

def check_signal(df):
    avg_vol = df["volume"].tail(AVG_BARS).mean()
    last = df.iloc[-1]
    vwap = (df["close"]*df["volume"]).cumsum().iloc[-1] / df["volume"].cumsum().iloc[-1]

    if last["volume"] >= VOL_MULT * avg_vol and last["close"] > vwap:
        return True, last["close"], last["volume"], avg_vol, vwap
    return False, last["close"], last["volume"], avg_vol, vwap


# ---- Main ----
def main():
    stocks = load_tokens()
    print("Monitoring:", stocks)

    while True:
        for sym, token in stocks.items():
            df = get_5min_data(sym, token)
            ok, close, vol, avgv, vwap = check_signal(df)
            if ok:
                msg = (f"🚨 {sym} | 5m Volume Spike + Above VWAP\n"
                       f"Close: {close:.2f} | VWAP: {vwap:.2f}\n"
                       f"Vol: {vol} ≥ {VOL_MULT}× Avg({AVG_BARS}): {avgv:.0f}\n"
                       f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(msg)
                send_telegram(msg)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sleeping {INTERVAL}min...")
        time.sleep(INTERVAL*60)

if __name__ == "__main__":
    main()



