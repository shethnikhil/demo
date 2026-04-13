import os

# Price move threshold (percent) that triggers a news search
PRICE_CHANGE_THRESHOLD = float(os.getenv("PRICE_CHANGE_THRESHOLD", "5.0"))

# Indian market hours (IST = UTC+5:30)
MARKET_OPEN = (9, 15)    # 9:15 AM
MARKET_CLOSE = (15, 30)  # 3:30 PM

# How often to poll prices during market hours (minutes)
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))

# NSE official CSV listing all Nifty 50 constituents
NIFTY50_CSV_URL = (
    "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"
)

# Local cache file path and TTL
CACHE_FILE = "nifty50_cache.json"
CACHE_TTL_DAYS = 7

# Max news articles returned per alert
NEWS_MAX_RESULTS = int(os.getenv("NEWS_MAX_RESULTS", "5"))

# Timezone for all scheduling
TIMEZONE = "Asia/Kolkata"
