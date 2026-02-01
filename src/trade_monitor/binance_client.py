"""Binance API client for fetching OHLCV data."""

import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

from .models import OHLCVData

logger = logging.getLogger(__name__)


class BinanceClient:
    """Client for fetching cryptocurrency data from Binance."""

    def __init__(self, api_key: str = "", api_secret: str = ""):
        """Initialize Binance client. Keys optional for public endpoints."""
        self.client = Client(api_key or "", api_secret or "")

    def get_ticker_price(self, symbol: str) -> float:
        """Fetch current price for a symbol."""
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker["price"])
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise

    def get_ohlcv(
        self, symbol: str, display_name: str, interval: str, limit: int = 30
    ) -> OHLCVData:
        """
        Fetch OHLCV candlestick data from Binance.

        Args:
            symbol: Trading pair (e.g., "ETHUSDT")
            display_name: Display name (e.g., "ETH")
            interval: Kline interval (e.g., "1d", "1h")
            limit: Number of candles to fetch

        Returns:
            OHLCVData with pandas DataFrame

        Raises:
            BinanceAPIException: On API error
        """
        try:
            klines = self.client.get_klines(
                symbol=symbol, interval=interval, limit=limit
            )

            # Convert to DataFrame with mplfinance-compatible columns
            df = pd.DataFrame(
                klines,
                columns=[
                    "timestamp",
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                    "close_time",
                    "quote_volume",
                    "trades",
                    "taker_buy_base",
                    "taker_buy_quote",
                    "ignore",
                ],
            )

            # Convert types
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)

            for col in ["Open", "High", "Low", "Close", "Volume"]:
                df[col] = df[col].astype(float)

            # Keep only OHLCV columns
            df = df[["Open", "High", "Low", "Close", "Volume"]]

            logger.debug(f"Fetched {len(df)} candles for {symbol}")

            return OHLCVData(
                symbol=symbol, display_name=display_name, interval=interval, data=df
            )

        except BinanceAPIException as e:
            logger.error(f"Binance API error for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            raise
