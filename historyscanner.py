import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv

# Load API keys and credentials from config.env
load_dotenv("config.env")

API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PASSWORD = os.getenv("PASSWORD")

LOGIN_URL = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
HIST_URL = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"

# ---------------- LOGIN (same as scanner.py) ----------------
def angel_login():
    payload = {
        "clientcode": CLIENT_ID,
        "password": PASSWORD
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-PrivateKey": API_KEY
    }
    r = requests.post(LOGIN_URL, json=payload, headers=headers)
    data = r.json()

    if not data.get("status"):
        raise Exception("Login failed: " + str(data))

    return data["data"]["jwtToken"]

# ---------------- HISTORY API ----------------
def get_history(jwt_token, symboltoken, interval, from_date, to_date):
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-ClientLocalIP": "127.0.0.1",
        "X-ClientPublicIP": "127.0.0.1",
        "X-MACAddress": "XX:XX:XX:XX:XX:XX",
        "X-PrivateKey": API_KEY,
    }
    payload = {
        "exchange": "NSE",
        "symboltoken": symboltoken,
        "interval": interval,
        "fromdate": from_date,
        "todate": to_date,
    }
    r = requests.post(HIST_URL, headers=headers, json=payload)
    data = r.json()
    return data.get("data", [])

# ---------------- UTILITIES ----------------
def load_watchlist():
    with open("watchlist.txt") as f:
        return [line.strip() for line in f if line.strip()]

def calculate_vwap(df):
    q = df["volume"]
    p = (df["high"] + df["low"] + df["close"]) / 3
    return (p * q).cumsum() / q.cumsum()

# ---------------- SCANNER LOGIC ----------------
def scan_history(date):
    with open("OpenAPIScripMaster.json", "r") as f:
        scrip_master = json.load(f)
    df = pd.DataFrame(scrip_master)

    jwt_token = angel_login()
    watchlist = load_watchlist()
    results = {}

    from_date = f"{date} 09:15"
    to_date   = f"{date} 15:30"

    for symbol in watchlist:
        row = df[df["symbol"] == symbol]
        if row.empty:
            continue

        token = str(row.iloc[0]["token"])

        candles = get_history(jwt_token, token, "FIVE_MINUTE", from_date, to_date)
        if not candles:
            continue

        hist = pd.DataFrame(candles, columns=["time", "open", "high", "low", "close", "volume"])
        hist["time"] = pd.to_datetime(hist["time"])
        hist[["open","high","low","close","volume"]] = hist[["open","high","low","close","volume"]].astype(float)

        # VWAP
        hist["vwap"] = calculate_vwap(hist)

        # Volume + VWAP condition
        if len(hist) >= 31:
            last_vol = hist.iloc[-1]["volume"]
            avg_vol = hist.iloc[-31:-1]["volume"].mean()
            last_close = hist.iloc[-1]["close"]
            last_vwap = hist.iloc[-1]["vwap"]

            if last_vol > 3 * avg_vol and last_close > last_vwap:
                results[symbol] = {
                    "last_close": round(last_close,2),
                    "last_vol": int(last_vol),
                    "avg_vol": int(avg_vol),
                    "last_vwap": round(last_vwap,2),
                }

    return results

# ---------------- MAIN ----------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python historyscanner.py YYYY-MM-DD")
        exit(1)

    date = sys.argv[1]
    print(f"[History Scanner] Checking {date}...")

    alerts = scan_history(date)
    print("Alerts:", json.dumps(alerts, indent=2))
