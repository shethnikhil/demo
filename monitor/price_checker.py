"""Fetch current NSE prices via yfinance and detect ±N% moves."""

from __future__ import annotations

import yfinance as yf

from monitor.config import PRICE_CHANGE_THRESHOLD
from monitor.logger import setup_logger

logger = setup_logger()


def _yf_symbol(symbol: str) -> str:
    """Convert NSE symbol to Yahoo Finance ticker (append .NS)."""
    # Some symbols have special characters that yfinance handles differently
    return symbol.replace("&", "") + ".NS"


class PriceChecker:
    """Tracks previous closes and checks for significant intraday moves.

    Args:
        stocks: List of dicts with keys 'symbol' and 'company_name'.
        threshold: Minimum absolute % change to flag a stock.
    """

    def __init__(
        self, stocks: list[dict], threshold: float = PRICE_CHANGE_THRESHOLD
    ) -> None:
        self.stocks = stocks
        self.threshold = threshold
        self._prev_closes: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_previous_closes(self) -> None:
        """Seed previous-close prices from the last available trading session.

        Called once at startup before any check_moves() call.
        """
        logger.info("Loading previous close prices for %d stocks...", len(self.stocks))
        tickers = [_yf_symbol(s["symbol"]) for s in self.stocks]

        try:
            data = yf.download(
                tickers,
                period="5d",
                interval="1d",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as exc:
            logger.error("yfinance download error: %s", exc)
            return

        loaded = 0
        for stock in self.stocks:
            sym = stock["symbol"]
            yf_sym = _yf_symbol(sym)
            try:
                if len(tickers) == 1:
                    closes = data["Close"].dropna()
                else:
                    closes = data[yf_sym]["Close"].dropna()

                if len(closes) >= 2:
                    # Second-to-last row is the previous completed trading day
                    self._prev_closes[sym] = float(closes.iloc[-2])
                    loaded += 1
                elif len(closes) == 1:
                    self._prev_closes[sym] = float(closes.iloc[-1])
                    loaded += 1
            except Exception as exc:
                logger.debug("Could not get close for %s: %s", sym, exc)

        logger.info("Previous closes loaded for %d/%d stocks.", loaded, len(self.stocks))

    def check_moves(self) -> list[dict]:
        """Fetch latest prices and return stocks that moved beyond the threshold.

        Returns:
            List of dicts: {symbol, company_name, prev_close, current_price, pct_change}
        """
        if not self._prev_closes:
            logger.warning("Previous closes not loaded; call load_previous_closes() first.")
            return []

        tickers = [_yf_symbol(s["symbol"]) for s in self.stocks]
        logger.debug("Fetching current prices for %d tickers...", len(tickers))

        try:
            data = yf.download(
                tickers,
                period="1d",
                interval="1m",
                group_by="ticker",
                auto_adjust=True,
                progress=False,
                threads=True,
            )
        except Exception as exc:
            logger.error("yfinance intraday download error: %s", exc)
            return []

        alerts = []
        for stock in self.stocks:
            sym = stock["symbol"]
            yf_sym = _yf_symbol(sym)
            prev = self._prev_closes.get(sym)
            if prev is None or prev == 0:
                continue

            try:
                if len(tickers) == 1:
                    closes = data["Close"].dropna()
                else:
                    closes = data[yf_sym]["Close"].dropna()

                if closes.empty:
                    continue

                current = float(closes.iloc[-1])
                pct = ((current - prev) / prev) * 100

                logger.debug(
                    "%s: prev=%.2f current=%.2f change=%.2f%%",
                    sym, prev, current, pct,
                )

                if abs(pct) >= self.threshold:
                    alerts.append(
                        {
                            "symbol": sym,
                            "company_name": stock["company_name"],
                            "prev_close": round(prev, 2),
                            "current_price": round(current, 2),
                            "pct_change": round(pct, 2),
                        }
                    )
            except Exception as exc:
                logger.debug("Could not check %s: %s", sym, exc)

        logger.info(
            "Price check complete. %d/%d stocks triggered ±%.1f%% alert.",
            len(alerts), len(self.stocks), self.threshold,
        )
        return alerts
