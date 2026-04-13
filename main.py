#!/usr/bin/env python3
"""Nifty 50 Stock News Monitor.

Monitors all Nifty 50 stocks during Indian market hours (9:15 AM – 3:30 PM IST).
When any stock moves ±5% (configurable) from its previous close, it fetches
recent Google News articles that might explain the move.

Usage:
    python main.py

Configuration (via environment variables or .env):
    PRICE_CHANGE_THRESHOLD  — default 5.0 (percent)
    CHECK_INTERVAL_MINUTES  — default 15
    NEWS_MAX_RESULTS        — default 5
"""

from monitor.config import PRICE_CHANGE_THRESHOLD
from monitor.logger import setup_logger
from monitor.nifty50 import get_nifty50_symbols
from monitor.price_checker import PriceChecker
from monitor import scheduler

logger = setup_logger()


def main() -> None:
    logger.info("Nifty 50 Stock News Monitor starting up...")
    logger.info("Alert threshold: ±%.1f%%", PRICE_CHANGE_THRESHOLD)

    # 1. Fetch Nifty 50 constituent list (cached locally)
    stocks = get_nifty50_symbols()
    logger.info("Loaded %d Nifty 50 stocks.", len(stocks))

    # 2. Initialise price checker and seed previous closes
    checker = PriceChecker(stocks)
    checker.load_previous_closes()

    # 3. Start scheduler — blocks until Ctrl-C or SIGTERM
    scheduler.start(checker)


if __name__ == "__main__":
    main()
