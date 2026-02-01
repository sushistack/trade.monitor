"""Main orchestrator for trade monitor."""

import logging
import time
from datetime import datetime

import structlog

from .config import load_settings, Settings
from .models import CycleResult
from .binance_client import BinanceClient
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
    renderer = ChartRenderer(settings.chart)
    uploader = ImageUploader(settings.upload)
    awtrix = AwtrixClient(settings.awtrix)

    if settings.awtrix.enabled:
        try:
            btc_price = binance.get_ticker_price("BTCUSDT")
            awtrix.push_price(btc_price)
            logger.info("awtrix_update_success", price=btc_price)
        except Exception as e:
            logger.error("awtrix_update_failed", error=str(e))

    success_count = 0
    error_count = 0
    errors: list[str] = []

    # Process each coin
    for coin in settings.coins:
        logger.info("processing_coin", coin=coin.display_name)

        # Fetch and render for each timeframe
        for tf in settings.timeframes:
            try:
                # Fetch data
                logger.debug("fetch_start", symbol=coin.symbol, timeframe=tf.code)

                data = binance.get_ohlcv(
                    symbol=coin.symbol,
                    display_name=coin.display_name,
                    interval=tf.interval,
                    limit=tf.limit,
                )

                # Render chart
                logger.debug("render_start", symbol=coin.symbol, timeframe=tf.code)

                chart = renderer.render(data, tf.code)

                # Upload
                logger.debug(
                    "upload_start", host=coin.upload_host, filename=chart.full_filename
                )

                result = uploader.upload(coin.upload_host, chart)

                if result.success:
                    success_count += 1
                    logger.info(
                        "chart_success",
                        coin=coin.display_name,
                        timeframe=tf.code,
                        host=coin.upload_host,
                    )
                else:
                    error_count += 1
                    error_msg = f"{coin.display_name}_{tf.code}: {result.error}"
                    errors.append(error_msg)
                    logger.error(
                        "chart_failed",
                        coin=coin.display_name,
                        timeframe=tf.code,
                        error=result.error,
                    )

            except Exception as e:
                error_count += 1
                error_msg = f"{coin.display_name}_{tf.code}: {str(e)}"
                errors.append(error_msg)
                logger.error(
                    "processing_error",
                    coin=coin.display_name,
                    timeframe=tf.code,
                    error=str(e),
                )

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
