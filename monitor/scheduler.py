"""APScheduler wiring for market-hours price checks."""

from __future__ import annotations

import signal
import sys

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from monitor.config import (
    CHECK_INTERVAL_MINUTES,
    MARKET_CLOSE,
    MARKET_OPEN,
    TIMEZONE,
)
from monitor.logger import setup_logger
from monitor.news_fetcher import format_news_report, search_news
from monitor.price_checker import PriceChecker

logger = setup_logger()

_tz = pytz.timezone(TIMEZONE)


def _run_check(checker: PriceChecker) -> None:
    """Single price-check tick: detect movers and fetch their news."""
    alerts = checker.check_moves()
    if not alerts:
        return

    for alert in alerts:
        articles = search_news(alert["company_name"], alert["symbol"])
        report = format_news_report(
            alert["symbol"],
            alert["company_name"],
            alert["pct_change"],
            articles,
        )
        logger.info(report)


def _end_of_day_summary(checker: PriceChecker) -> None:
    """Final check at market close + daily summary."""
    logger.info("=" * 70)
    logger.info("END-OF-DAY SUMMARY — running final price check...")
    logger.info("=" * 70)
    _run_check(checker)
    logger.info("End-of-day scan complete. Market closed.")


def start(checker: PriceChecker) -> None:
    """Initialise APScheduler and block until Ctrl-C or SIGTERM."""
    scheduler = BlockingScheduler(timezone=_tz)

    open_h, open_m = MARKET_OPEN
    close_h, close_m = MARKET_CLOSE

    # Intraday check: every CHECK_INTERVAL_MINUTES, Mon-Fri, within market hours
    # Cron 'hour' range covers 09-15; we filter edge minutes via start/end_date
    scheduler.add_job(
        _run_check,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=f"{open_h}-{close_h}",
            minute=f"*/{CHECK_INTERVAL_MINUTES}",
            timezone=_tz,
        ),
        args=[checker],
        id="intraday_check",
        name="Intraday price check",
        misfire_grace_time=60,
        coalesce=True,
    )

    # End-of-day job: exactly at market close, Mon-Fri
    scheduler.add_job(
        _end_of_day_summary,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=close_h,
            minute=close_m,
            timezone=_tz,
        ),
        args=[checker],
        id="eod_summary",
        name="End-of-day summary",
        misfire_grace_time=120,
    )

    # Graceful shutdown on SIGINT / SIGTERM
    def _shutdown(signum, frame):  # noqa: ANN001
        logger.info("Shutdown signal received. Stopping scheduler...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    logger.info(
        "Scheduler started. Monitoring %d Nifty 50 stocks. "
        "Market hours: %02d:%02d – %02d:%02d IST (Mon-Fri). "
        "Check interval: %d min.",
        len(checker.stocks),
        open_h, open_m, close_h, close_m,
        CHECK_INTERVAL_MINUTES,
    )

    scheduler.start()
