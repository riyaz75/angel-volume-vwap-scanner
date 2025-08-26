# Angel Volume + VWAP Scanner

Scans stocks every 5 minutes:

- Volume ≥ 3 × avg(30 candles)
- Price > VWAP

✅ Sends Telegram alerts

## Setup

1. Clone repo
2. Add `OpenAPIScripMaster.json` (from Angel One SmartAPI) to root folder
3. Edit `config.env` with Angel + Telegram keys
4. List stocks in `watchlist.txt`
5. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
