"""Yahoo Finance client for stock and index data."""

import logging

import pandas as pd
import yfinance as yf

from .models import OHLCVData

logger = logging.getLogger(__name__)

# Map our interval codes to yfinance period strings that cover enough history
_PERIOD_MAP = {
    "1m": "5d",
    "5m": "5d",
    "15m": "5d",
    "30m": "5d",
    "1h": "5d",
    "1d": "2mo",
    "1wk": "1y",
}


class YahooClient:
    """Client for fetching stock and index data via Yahoo Finance."""

    def get_ticker_price(self, symbol: str) -> float:
        """Fetch current price for a symbol."""
        try:
            df = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=True)
            if df.empty:
                raise ValueError(f"No price data for {symbol}")
            return float(df["Close"].iloc[-1].item())
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            raise

    def get_ohlcv(
        self, symbol: str, display_name: str, interval: str, limit: int = 30
    ) -> OHLCVData:
        """
        Fetch OHLCV data from Yahoo Finance.

        Args:
            symbol: Yahoo Finance symbol (e.g., "^GSPC", "^IXIC")
            display_name: Display name (e.g., "SP500", "NASDAQ")
            interval: Candle interval (e.g., "1h", "1d")
            limit: Number of candles to return

        Returns:
            OHLCVData with pandas DataFrame
        """
        try:
            period = _PERIOD_MAP.get(interval, "2mo")
            df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=True)

            if df.empty:
                raise ValueError(f"No data returned for {symbol}")

            df.index = pd.to_datetime(df.index)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)

            # yf.download may return MultiIndex columns when downloading a single ticker
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df[["Open", "High", "Low", "Close", "Volume"]].tail(limit)

            logger.debug(f"Fetched {len(df)} candles for {symbol}")

            return OHLCVData(
                symbol=symbol, display_name=display_name, interval=interval, data=df,
                currency="USD",
            )

        except Exception as e:
            logger.error(f"Error fetching {symbol} from Yahoo Finance: {e}")
            raise
