import pandas as pd
import requests
import datetime, os, json, sys
from dotenv import load_dotenv

# 🔹 Load credentials from config.env
load_dotenv("config.env")
API_KEY   = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PASSWORD  = os.getenv("PASSWORD")

# 🔹 Setup AngelOne connection
obj = SmartConnect(api_key=API_KEY)
obj.generateSession(CLIENT_ID, PASSWORD)

# -------------------
# Load tokens from OpenAPIScripMaster.json
# -------------------
def load_tokens():
    with open("OpenAPIScripMaster.json","r") as f:
        df = pd.DataFrame(json.load(f))

    # Handle column names (exchange vs exch_seg)
    col_exchange = "exchange" if "exchange" in df.columns else "exch_seg"

    # NSE EQ filter only
    df = df[df[col_exchange]=="NSE"]

    return dict(zip(df["symbol"], df["token"]))

# -------------------
# Fetch Historical Candles
# -------------------
def get_history(symboltoken, date, exchange="NSE", interval="5minute"):
    start = f"{date} 09:15"
    end   = f"{date} 15:30"

    params = {
        "exchange": exchange,
        "symboltoken": str(symboltoken),
        "interval": interval,
        "fromdate": start,
        "todate": end
    }

    res = obj.getCandleData(params)
    if "data" not in res:
        print(f"⚠️ No data for token {symboltoken}")
        return pd.DataFrame()

    df = pd.DataFrame(res["data"], columns=["time","open","high","low","close","volume"])
    df["time"] = pd.to_datetime(df["time"])
    return df

# -------------------
# Strategy Condition: Volume Spike & Price above VWAP
# -------------------
def check_conditions(df):
    if df.empty:
        return []

    # VWAP calculation
    df["cum_pv"] = (df["close"]*df["volume"]).cumsum()
    df["cum_vol"] = df["volume"].cumsum()
    df["vwap"] = df["cum_pv"] / df["cum_vol"]

    # Rolling average of last 30 candles
    df["avg_vol30"] = df["volume"].rolling(30).mean()

    signals = []
    for i, row in df.iterrows():
        if row["avg_vol30"] > 0:  # avoid NaN early candles
            if row["volume"] >= 3 * row["avg_vol30"] and row["close"] > row["vwap"]:
                signals.append((row["time"], row["close"], row["volume"]))
    return signals

# -------------------
# Main
# -------------------
def main():
    # Take date from CLI args
    if len(sys.argv) < 2:
        print("Usage: python historyscanner.py YYYY-MM-DD")
        sys.exit(1)

    date = sys.argv[1]

    tokens = load_tokens()

    # Read watchlist
    with open("watchlist.txt") as f:
        watchlist = [line.strip() for line in f if line.strip()]

    for stock in watchlist:
        if stock not in tokens:
            print(f"⚠️ {stock} not found in token map, skipping...")
            continue

        df = get_history(tokens[stock], date=date)
        signals = check_conditions(df)

        if signals:
            print(f"\n🚨 {stock} Signals on {date}:")
            for sig in signals:
                print(f"  Time={sig[0]}, Price={sig[1]}, Volume={sig[2]}")
        else:
            print(f"{stock}: No signal found on {date}.")

if __name__ == "__main__":
    main()
