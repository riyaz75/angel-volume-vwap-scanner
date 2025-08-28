import os
from SmartApi import SmartConnect
from dotenv import load_dotenv
import logzero
import pyotp

# Load creds
load_dotenv("config.env")

API_KEY   = os.getenv("ANGEL_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD  = os.getenv("ANGEL_PASSWORD")
TOTP      = os.getenv("ANGEL_TOTP")  # optional if you have 2FA

# ---- LOGIN ----
obj = SmartConnect(api_key=API_KEY)

login_response = obj.generateSession(CLIENT_ID, PASSWORD, TOTP)
print("Login Response:", login_response)

# Extract jwtToken
jwt_token = login_response["data"]["jwtToken"]
print("Your JWT Token:", jwt_token)
