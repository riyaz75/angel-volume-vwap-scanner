from SmartApi import SmartConnect
import os
from dotenv import load_dotenv

load_dotenv("config.env")

API_KEY   = os.getenv("ANGEL_HIS_API_KEY")
CLIENT_ID = os.getenv("ANGEL_CLIENT_ID")
PASSWORD  = os.getenv("ANGEL_HIS_API_PW")
TOTP      = os.getenv("ANGEL_TOTP_SECRET")  # optional if you have 2FA
MPIN    =os.getenv("ANGEL_MPIN")


obj=SmartConnect(api_key=API_KEY)
data = obj.generateSession(CLIENT_ID,PASSWORD,TOTP)
