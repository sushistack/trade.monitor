# Trade Monitor

Automated cryptocurrency chart monitoring system that fetches real-time data from Binance, generates TradingView-style candlestick charts, and uploads them to embedded devices via HTTP multipart.

## Features

- **Real-time Data**: Fetches OHLCV candlestick data from Binance API for ETH, XRP, and SOL
- **Chart Generation**: Renders professional TradingView-style charts as 240×240px JPEG images
- **Multi-timeframe**: Generates 1-day and 1-month charts for each cryptocurrency
- **Reliable Uploads**: HTTP multipart uploads with configurable retry logic and exponential backoff
- **Automated Execution**: Cron-based scheduling for minute-level monitoring
- **Structured Logging**: Comprehensive logging with structlog for monitoring and debugging
- **Configurable**: YAML-based configuration for coins, timeframes, and upload targets

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://astral.sh/uv/) package manager
- Linux/Unix system (for cron support)

### Installation

1. Clone or download the project
2. Run the installation script:

```bash
cd /path/to/trade.monitor
./scripts/install.sh
```

This will:
- Create a Python virtual environment using `uv`
- Install all dependencies
- Create necessary directories
- Make scripts executable

### Configuration

Edit `config/settings.yaml` to customize your setup:

```yaml
coins:
  - symbol: "ETHUSDT"      # Binance trading pair
    display_name: "ETH"     # Display name for filenames
    upload_host: "192.168.0.20"  # Target device IP

timeframes:
  - code: "1D"             # Chart timeframe code
    interval: "1d"         # Binance kline interval
    limit: 30              # Number of candles to fetch

chart:
  width: 240               # Chart width in pixels
  height: 240              # Chart height in pixels
  style: "tradingview"     # Chart style (TradingView dark theme)
  jpeg_quality: 85         # JPEG compression quality (1-100)

upload:
  timeout: 30.0            # Upload timeout in seconds
  retries: 3               # Number of retry attempts
  dir: "/image/"           # Target directory on device
```

### Environment Variables (Optional)

For Binance API authentication (optional for public endpoints):

```bash
cp .env.example .env
```

Edit `.env` if using authenticated Binance endpoints:

```
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
CONFIG_PATH=config/settings.yaml
```

## Usage

### Manual Test Run

Test the application with a single execution cycle:

```bash
./scripts/run.sh
```

This will:
- Fetch the latest candlestick data from Binance
- Generate charts for each configured coin and timeframe
- Upload charts to all configured devices
- Display results and timing information

### Automated Execution

Manage the cron job easily with the Python helper script:

```bash
# Add cron job (runs every minute by default)
source venv/bin/activate
python scripts/manage_cron.py add

# Add with custom interval (e.g., every 5 minutes)
python scripts/manage_cron.py add --interval 5

# List active jobs
python scripts/manage_cron.py list

# Remove cron job
python scripts/manage_cron.py remove
```

### Manual Execution

Run directly from the project directory:

```bash
source venv/bin/activate
python -m trade_monitor
```

### Remove Cron Job

To uninstall the cron job:

```bash
./scripts/uninstall_cron.sh
```

## Project Structure

```
trade.monitor/
├── config/
│   └── settings.yaml              # Main configuration file
├── src/trade_monitor/
│   ├── __init__.py
│   ├── __main__.py                # Entry point for python -m
│   ├── main.py                    # Main orchestrator
│   ├── config.py                  # Settings loader (Pydantic)
│   ├── models.py                  # Data models (OHLCVData, ChartImage, etc.)
│   ├── binance_client.py          # Binance API client
│   ├── chart_renderer.py          # Chart rendering with mplfinance
│   ├── uploader.py                # HTTP multipart uploader
│   └── styles.py                  # TradingView chart styling
├── scripts/
│   ├── install.sh                 # Installation script
│   ├── run.sh                      # Execution wrapper (for cron)
│   ├── install_cron.sh            # Cron job installer
│   └── uninstall_cron.sh          # Cron job removal
├── logs/                          # Application logs (created at runtime)
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## Architecture

### Execution Flow

```
┌─────────────────────────────────────────────────────┐
│         main() - Load settings & logging            │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│  run_cycle() - Execute fetch-render-upload cycle   │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    ┌──────┐   ┌──────────┐   ┌───────────┐
    │Fetch │   │  Render  │   │  Upload   │
    │OHLCV │──▶│  Charts  │──▶│   Image   │
    └──────┘   └──────────┘   └───────────┘
```

### Components

#### BinanceClient
- Fetches OHLCV candlestick data from Binance
- Converts raw API data to pandas DataFrame with proper columns and types
- Handles API errors and logging

#### ChartRenderer
- Renders candlestick charts using mplfinance library
- Applies TradingView dark theme styling
- Resizes images to exact 240×240px dimensions
- Converts to JPEG with configurable quality

#### ImageUploader
- Sends JPEG images via HTTP multipart POST
- Implements automatic retry with exponential backoff (2s, 4s, 8s delays)
- Tracks upload duration and errors
- Handles network timeouts gracefully

#### StructuredLogging
- Logs to both file (`logs/trade_monitor.log`) and stdout
- Includes cycle ID, timing information, and detailed error context
- Useful for monitoring and debugging

## Dependencies

- **python-binance**: Official Binance API client
- **pandas**: Data manipulation and analysis
- **mplfinance**: Professional candlestick chart rendering
- **Pillow**: Image processing and JPEG encoding
- **httpx**: Modern HTTP client with timeout support
- **Pydantic**: Data validation and settings management
- **PyYAML**: Configuration file parsing
- **structlog**: Structured logging framework

All dependencies are listed in `requirements.txt`.

## Logging

Logs are written to `logs/trade_monitor.log` with timestamps, log levels, and structured context. The log level can be configured in `config/settings.yaml`:

```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "logs/trade_monitor.log"
```

View live logs:

```bash
tail -f logs/trade_monitor.log
```

## Configuration Reference

### Coin Configuration

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | string | Binance trading pair (e.g., "ETHUSDT") |
| `display_name` | string | Display name for chart filenames |
| `upload_host` | string | Target device IP or hostname |

### Chart Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `width` | integer | 240 | Chart width in pixels |
| `height` | integer | 240 | Chart height in pixels |
| `style` | string | "tradingview" | Chart styling theme |
| `jpeg_quality` | integer | 85 | JPEG quality (1-100) |

### Upload Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `timeout` | float | 30.0 | Upload timeout in seconds |
| `retries` | integer | 3 | Number of retry attempts |
| `dir` | string | "/image/" | Target directory on device |

### Timeframe Configuration

| Field | Type | Description |
|-------|------|-------------|
| `code` | string | Timeframe code for filename (e.g., "1D", "1M") |
| `interval` | string | Binance kline interval (1m, 5m, 1h, 1d, 1w, 1M) |
| `limit` | integer | Number of candles to fetch (default: 30) |

## Troubleshooting

### Installation Issues

If `uv` is not found:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Upload Failures

Check device connectivity:

```bash
ping 192.168.0.20
```

Verify upload endpoint:

```bash
curl -v http://192.168.0.20/doUpload
```

Review logs for detailed error messages:

```bash
tail -100 logs/trade_monitor.log
grep "error\|failed" logs/trade_monitor.log
```

### Cron Not Running

Verify cron job is installed:

```bash
crontab -l
```

Check cron execution logs:

```bash
tail -f logs/cron.log
```

Ensure venv is activated and scripts have execute permissions:

```bash
chmod +x scripts/*.sh
ls -la scripts/
```

### Binance API Errors

The application uses public Binance endpoints by default (no authentication required). If using authenticated endpoints, ensure your API keys are correctly set in `.env`:

```bash
export BINANCE_API_KEY=your_key
export BINANCE_API_SECRET=your_secret
./scripts/run.sh
```

## Output

Generated chart filenames follow the pattern: `{DISPLAY_NAME}_{TIMEFRAME_CODE}.jpg`

Examples:
- `ETH_1D.jpg` - Ethereum 1-day chart
- `ETH_1M.jpg` - Ethereum 1-month chart
- `XRP_1D.jpg` - Ripple 1-day chart
- `SOL_1M.jpg` - Solana 1-month chart

Each file is exactly 240×240 pixels in JPEG format and uploaded via HTTP multipart to the configured device.

## Performance

Typical cycle execution time: 2-5 seconds

- Fetch OHLCV data: ~0.5-1 second per coin
- Render charts: ~0.5-1 second per chart
- Upload images: ~1-2 seconds total (with network latency)

The 55-second timeout in `scripts/run.sh` ensures completion well within the 1-minute cron interval.

## License

Proprietary. See LICENSE file for details.

## Support

For issues or questions, review:
1. Application logs: `logs/trade_monitor.log`
2. Cron logs: `logs/cron.log`
3. Configuration: `config/settings.yaml`
4. This README for common troubleshooting steps
