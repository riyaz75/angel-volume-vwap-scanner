from SmartApi import SmartConnect
import pyotp
import os
from dotenv import load_dotenv

# 🔑 Load credentials (replace with your actual values or use env variables)
load_dotenv("config.env")
API_KEY     = os.getenv("ANGEL_API_KEY")
CLIENT_CODE = os.getenv("ANGEL_CLIENT_ID")
MPIN        = os.getenv("ANGEL_MPIN")
TOTP_SECRET = os.getenv("ANGEL_TOTP_SECRET")  # from Angel One app

# Initialize SmartConnect
smartApi = SmartConnect(api_key=API_KEY)

# Generate TOTP dynamically
totp = pyotp.TOTP(TOTP_SECRET).now()
print("Generated OTP:", totp)

try:
    # ✅ Login using MPIN + TOTP
    login_response = smartApi.generateSessionByMPIN(clientCode=CLIENT_CODE, mpin=MPIN, totp=totp)
    print("Login Response:", login_response)

    if login_response.get("status"):
        jwt_token = login_response["data"]["jwtToken"]
        refresh_token = login_response["data"]["refreshToken"]
        print("✅ Logged in successfully")
        print("JWT Token:", jwt_token)
        print("Refresh Token:", refresh_token)
    else:
        print("❌ Login failed:", login_response)

except Exception as e:
    print("⚠️ Error during login:", str(e))
