"""Fetch and cache the Nifty 50 constituent stock list."""

import json
import os
import time
from datetime import datetime, timedelta

import requests

from monitor.config import CACHE_FILE, CACHE_TTL_DAYS, NIFTY50_CSV_URL
from monitor.logger import setup_logger

logger = setup_logger()

# Hardcoded fallback list (as of early 2026)
_FALLBACK_SYMBOLS = [
    {"symbol": "ADANIENT", "company_name": "Adani Enterprises Ltd."},
    {"symbol": "ADANIPORTS", "company_name": "Adani Ports and Special Economic Zone Ltd."},
    {"symbol": "APOLLOHOSP", "company_name": "Apollo Hospitals Enterprise Ltd."},
    {"symbol": "ASIANPAINT", "company_name": "Asian Paints Ltd."},
    {"symbol": "AXISBANK", "company_name": "Axis Bank Ltd."},
    {"symbol": "BAJAJ-AUTO", "company_name": "Bajaj Auto Ltd."},
    {"symbol": "BAJFINANCE", "company_name": "Bajaj Finance Ltd."},
    {"symbol": "BAJAJFINSV", "company_name": "Bajaj Finserv Ltd."},
    {"symbol": "BPCL", "company_name": "Bharat Petroleum Corporation Ltd."},
    {"symbol": "BHARTIARTL", "company_name": "Bharti Airtel Ltd."},
    {"symbol": "BRITANNIA", "company_name": "Britannia Industries Ltd."},
    {"symbol": "CIPLA", "company_name": "Cipla Ltd."},
    {"symbol": "COALINDIA", "company_name": "Coal India Ltd."},
    {"symbol": "DIVISLAB", "company_name": "Divi's Laboratories Ltd."},
    {"symbol": "DRREDDY", "company_name": "Dr. Reddy's Laboratories Ltd."},
    {"symbol": "EICHERMOT", "company_name": "Eicher Motors Ltd."},
    {"symbol": "GRASIM", "company_name": "Grasim Industries Ltd."},
    {"symbol": "HCLTECH", "company_name": "HCL Technologies Ltd."},
    {"symbol": "HDFCBANK", "company_name": "HDFC Bank Ltd."},
    {"symbol": "HDFCLIFE", "company_name": "HDFC Life Insurance Company Ltd."},
    {"symbol": "HEROMOTOCO", "company_name": "Hero MotoCorp Ltd."},
    {"symbol": "HINDALCO", "company_name": "Hindalco Industries Ltd."},
    {"symbol": "HINDUNILVR", "company_name": "Hindustan Unilever Ltd."},
    {"symbol": "ICICIBANK", "company_name": "ICICI Bank Ltd."},
    {"symbol": "ITC", "company_name": "ITC Ltd."},
    {"symbol": "INDUSINDBK", "company_name": "IndusInd Bank Ltd."},
    {"symbol": "INFY", "company_name": "Infosys Ltd."},
    {"symbol": "JSWSTEEL", "company_name": "JSW Steel Ltd."},
    {"symbol": "KOTAKBANK", "company_name": "Kotak Mahindra Bank Ltd."},
    {"symbol": "LT", "company_name": "Larsen & Toubro Ltd."},
    {"symbol": "M&M", "company_name": "Mahindra & Mahindra Ltd."},
    {"symbol": "MARUTI", "company_name": "Maruti Suzuki India Ltd."},
    {"symbol": "NTPC", "company_name": "NTPC Ltd."},
    {"symbol": "NESTLEIND", "company_name": "Nestle India Ltd."},
    {"symbol": "ONGC", "company_name": "Oil & Natural Gas Corporation Ltd."},
    {"symbol": "POWERGRID", "company_name": "Power Grid Corporation of India Ltd."},
    {"symbol": "RELIANCE", "company_name": "Reliance Industries Ltd."},
    {"symbol": "SBILIFE", "company_name": "SBI Life Insurance Company Ltd."},
    {"symbol": "SBIN", "company_name": "State Bank of India"},
    {"symbol": "SUNPHARMA", "company_name": "Sun Pharmaceutical Industries Ltd."},
    {"symbol": "TCS", "company_name": "Tata Consultancy Services Ltd."},
    {"symbol": "TATACONSUM", "company_name": "Tata Consumer Products Ltd."},
    {"symbol": "TATAMOTORS", "company_name": "Tata Motors Ltd."},
    {"symbol": "TATASTEEL", "company_name": "Tata Steel Ltd."},
    {"symbol": "TECHM", "company_name": "Tech Mahindra Ltd."},
    {"symbol": "TITAN", "company_name": "Titan Company Ltd."},
    {"symbol": "ULTRACEMCO", "company_name": "UltraTech Cement Ltd."},
    {"symbol": "WIPRO", "company_name": "Wipro Ltd."},
    {"symbol": "SHRIRAMFIN", "company_name": "Shriram Finance Ltd."},
    {"symbol": "TRENT", "company_name": "Trent Ltd."},
]


def _cache_is_fresh() -> bool:
    if not os.path.exists(CACHE_FILE):
        return False
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data["cached_at"])
        return datetime.now() - cached_at < timedelta(days=CACHE_TTL_DAYS)
    except Exception:
        return False


def _load_cache() -> list[dict]:
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["symbols"]


def _save_cache(symbols: list[dict]) -> None:
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump({"cached_at": datetime.now().isoformat(), "symbols": symbols}, f)


def _fetch_from_nse() -> list[dict]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
    }
    # NSE requires a session cookie obtained from the main site first
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=headers, timeout=10)
    time.sleep(1)

    resp = session.get(NIFTY50_CSV_URL, headers=headers, timeout=15)
    resp.raise_for_status()

    symbols = []
    lines = resp.text.strip().splitlines()
    # CSV columns: Company Name,Industry,Symbol,Series,ISIN Code
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            symbols.append(
                {"symbol": parts[2], "company_name": parts[0]}
            )
    return symbols


def get_nifty50_symbols() -> list[dict]:
    """Return list of Nifty 50 stocks as [{'symbol': ..., 'company_name': ...}].

    Uses a local cache (refreshed every CACHE_TTL_DAYS days).
    Falls back to hardcoded list if NSE download fails.
    """
    if _cache_is_fresh():
        logger.debug("Loading Nifty 50 list from cache.")
        return _load_cache()

    logger.info("Fetching Nifty 50 constituent list from NSE...")
    try:
        symbols = _fetch_from_nse()
        if len(symbols) >= 40:
            _save_cache(symbols)
            logger.info("Nifty 50 list updated: %d stocks cached.", len(symbols))
            return symbols
        logger.warning("NSE returned only %d symbols; using fallback.", len(symbols))
    except Exception as exc:
        logger.warning("Failed to fetch from NSE (%s); using fallback list.", exc)

    return _FALLBACK_SYMBOLS
