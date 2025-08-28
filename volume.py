import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv

# Load credentials from config.env
load_dotenv("config.env")
API_KEY = os.getenv("API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
PASSWORD = os.getenv("PASSWORD")

LOGIN_URL = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
HIST_URL = "https://apiconnect.angelone.in/rest/secure/angelbroking/historical/v1/getCandleData"

# ----------------- LOGIN -----------------
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

# ----------------- HISTORY API -----------------
def get_history(jwt_token, symboltoken, interval, from_date, to_date):
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
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

# ----------------- MAIN -----------------
if __name__ == "__main__":
    # Login first to get jwt_token
    jwt_token = angel_login()

    # Load scrip master and find Reliance token
    with open("OpenAPIScripMaster.json", "r") as f:
        scrip_master = json.load(f)
    df = pd.DataFrame(scrip_master)

    row = df[df["symbol"] == "RELIANCE"]
    if row.empty:
        print("Reliance not found in scrip master!")
        exit(1)
    token = str(row.iloc[0]["token"])

    # Date range (full trading day)
    from_date = "2025-08-25 09:15"
    to_date   = "2025-08-25 15:30"

    candles = get_history(jwt_token, token, "FIVE_MINUTE", from_date, to_date)

    if not candles:
        print("No data returned for Reliance")
        exit(1)

    hist = pd.DataFrame(candles, columns=["time","open","high","low","close","volume"])
    hist["time"] = pd.to_datetime(hist["time"])
    hist[["open","high","low","close","volume"]] = hist[["open","high","low","close","volume"]].astype(float)

    # Last 30 candles
    last30 = hist.tail(30)

    print("\n--- Last 30 Candles for Reliance (5-min) ---")
    print(last30[["time","volume"]])

    print("\nTotal Volume (last 30 candles):", int(last30["volume"].sum()))
