"""Main orchestrator for trade monitor."""

import logging
import time
from datetime import datetime

import structlog

from .config import load_settings, Settings
from .models import CycleResult
from .binance_client import BinanceClient
from .yahoo_client import YahooClient
from .chart_renderer import ChartRenderer
from .uploader import ImageUploader
from .awtrix_client import AwtrixClient


def configure_logging(settings: Settings) -> None:
    """Configure structured logging."""
    import sys
    from pathlib import Path

    # Ensure log directory exists
    log_path = Path(settings.logging.file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.logging.level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(settings.logging.file),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def run_cycle(settings: Settings) -> CycleResult:
    """
    Execute one complete fetch-render-upload cycle.

    Returns:
        CycleResult with success/failure counts and timing
    """
    logger = structlog.get_logger()
    start_time = time.time()

    cycle_id = datetime.utcnow().isoformat()
    logger.info("cycle_start", cycle_id=cycle_id)

    # Initialize components
    binance = BinanceClient()
    yahoo = YahooClient()
    renderer = ChartRenderer(settings.chart)
    uploader = ImageUploader(settings.upload)
    awtrix = AwtrixClient(settings.awtrix)

    if settings.awtrix.enabled:
        try:
            if settings.awtrix.ticker:
                price = yahoo.get_ticker_price(settings.awtrix.ticker)
            else:
                price = binance.get_ticker_price("BTCUSDT")
            awtrix.push_price(price)
            logger.info("awtrix_update_success", price=price)
        except Exception as e:
            logger.error("awtrix_update_failed", error=str(e))

    success_count = 0
    error_count = 0
    errors: list[str] = []

    def process_asset(symbol, display_name, upload_host, fetch_fn):
        nonlocal success_count, error_count
        for tf in settings.timeframes:
            try:
                logger.debug("fetch_start", symbol=symbol, timeframe=tf.code)
                data = fetch_fn(
                    symbol=symbol,
                    display_name=display_name,
                    interval=tf.interval,
                    limit=tf.limit,
                )
                logger.debug("render_start", symbol=symbol, timeframe=tf.code)
                chart = renderer.render(data, tf.code)
                logger.debug("upload_start", host=upload_host, filename=chart.full_filename)
                result = uploader.upload(upload_host, chart)
                if result.success:
                    success_count += 1
                    logger.info("chart_success", symbol=display_name, timeframe=tf.code, host=upload_host)
                else:
                    error_count += 1
                    errors.append(f"{display_name}_{tf.code}: {result.error}")
                    logger.error("chart_failed", symbol=display_name, timeframe=tf.code, error=result.error)
            except Exception as e:
                error_count += 1
                errors.append(f"{display_name}_{tf.code}: {str(e)}")
                logger.error("processing_error", symbol=display_name, timeframe=tf.code, error=str(e))

    # Process crypto coins (Binance)
    for coin in settings.coins:
        logger.info("processing_coin", coin=coin.display_name)
        process_asset(coin.symbol, coin.display_name, coin.upload_host, binance.get_ohlcv)

    # Process stocks/indexes (Yahoo Finance)
    for stock in settings.stocks:
        logger.info("processing_stock", stock=stock.display_name)
        process_asset(stock.symbol, stock.display_name, stock.upload_host, yahoo.get_ohlcv)

    duration_ms = (time.time() - start_time) * 1000

    logger.info(
        "cycle_complete",
        cycle_id=cycle_id,
        success_count=success_count,
        error_count=error_count,
        duration_ms=round(duration_ms, 2),
    )

    return CycleResult(
        success_count=success_count,
        error_count=error_count,
        duration_ms=duration_ms,
        errors=errors,
    )


def main() -> int:
    """Entry point for cron execution."""
    try:
        settings = load_settings()
        configure_logging(settings)

        result = run_cycle(settings)

        # Exit with error code if any failures
        return 0 if result.error_count == 0 else 1

    except Exception as e:
        print(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
