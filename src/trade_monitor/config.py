from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class CoinConfig(BaseModel):
    symbol: str
    display_name: str
    upload_host: str


class ChartConfig(BaseModel):
    width: int = 240
    height: int = 240
    style: str = "tradingview"
    jpeg_quality: int = 85


class UploadConfig(BaseModel):
    timeout: float = 30.0
    retries: int = 3
    dir: str = "/image/"


class AwtrixConfig(BaseModel):
    enabled: bool = False
    host: str = "192.168.0.23"
    app_name: str = "bitcoin"
    icon: str = "10814"
    color: list[int] = [255, 153, 0]


class TimeframeConfig(BaseModel):
    code: str
    interval: str
    limit: int = 30


class LoggingConfig(BaseModel):
    level: str = "INFO"
    file: str = "logs/trade_monitor.log"


class Settings(BaseModel):
    coins: list[CoinConfig]
    chart: ChartConfig = Field(default_factory=ChartConfig)
    upload: UploadConfig = Field(default_factory=UploadConfig)
    awtrix: AwtrixConfig = Field(default_factory=AwtrixConfig)
    timeframes: list[TimeframeConfig]
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_settings(config_path: Optional[str] = None) -> Settings:
    """Load settings from YAML config file."""
    import os

    path = Path(config_path or os.getenv("CONFIG_PATH", "config/settings.yaml"))
    with open(path) as f:
        data = yaml.safe_load(f)
    return Settings(**data)
