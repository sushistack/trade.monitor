from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import pandas as pd

@dataclass
class OHLCVData:
    """OHLCV candlestick data."""
    symbol: str
    display_name: str
    interval: str
    data: pd.DataFrame  # Columns: Open, High, Low, Close, Volume with DatetimeIndex
    currency: str = "USDT"
    fetched_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ChartImage:
    """Generated chart image."""
    symbol: str
    display_name: str
    timeframe_code: str
    filename: str
    image_bytes: bytes

    @property
    def full_filename(self) -> str:
        return f"{self.display_name}_{self.timeframe_code}.jpg"

@dataclass
class UploadResult:
    """Result of upload operation."""
    success: bool
    host: str
    filename: str
    error: Optional[str] = None
    duration_ms: float = 0.0

@dataclass
class CycleResult:
    """Result of one complete fetch-render-upload cycle."""
    success_count: int
    error_count: int
    duration_ms: float
    errors: list[str] = field(default_factory=list)
