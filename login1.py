import os
import pyotp
from SmartApi import SmartConnect
from dotenv import load_dotenv

# Load creds
load_dotenv("config.env")

API_KEY     = os.getenv("ANGEL_API_KEY")
CLIENT_ID   = os.getenv("ANGEL_CLIENT_ID")
PASSWORD    = os.getenv("ANGEL_PASSWORD")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")  # base32 secret, not the OTP
print("Loaded secret:", TOTP_SECRET)
# ---- LOGIN ----
obj = SmartConnect(api_key=API_KEY)


# Auto-generate 6-digit OTP
totp = pyotp.TOTP(TOTP_SECRET).now()

print("Generated OTP:", totp)

login_response = obj.generateSession(CLIENT_ID, PASSWORD, totp)
print("Login Response:", login_response)

if login_response.get("status") and login_response.get("data"):
    jwt_token = login_response["data"]["jwtToken"]
    refresh_token = login_response["data"]["refreshToken"]
    feed_token = obj.getfeedToken()

    print("\n✅ Login Successful")
    print("JWT Token:", jwt_token)
    print("Refresh Token:", refresh_token)
    print("Feed Token:", feed_token)
else:
    print("\n❌ Login failed:", login_response)
