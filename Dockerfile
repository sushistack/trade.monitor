# Story 5.6 (home-server-gitops) — golden-path image for trade-monitor: market data → 240×240
# charts → multipart upload to embedded LAN devices + an AWTRIX ticker. Runs as a k8s CronJob
# (the LXC `python-crontab` cron is dropped — k8s owns scheduling). Single-shot: `python -m
# trade_monitor` runs one fetch-render-upload cycle and exits.
FROM python:3.12-slim

# Agg = headless matplotlib (no GUI libs). HOME/MPLCONFIGDIR = a writable dir for the non-root
# user: matplotlib's font cache and yfinance's tz cache both need $HOME writable or they crash.
# CONFIG_PATH points at the mounted ConfigMap (config.py reads $CONFIG_PATH, defaults to
# config/settings.yaml). PYTHONPATH = src layout. PYTHONUNBUFFERED so k8s captures stdout live.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLBACKEND=Agg \
    HOME=/tmp \
    MPLCONFIGDIR=/tmp/mpl \
    PYTHONPATH=/app/src \
    CONFIG_PATH=/config/settings.yaml

# libgomp1 (numpy/scipy openmp) + ca-certs (TLS to Binance/Yahoo/LaMetric) + tzdata (Asia/Seoul).
# 🔴 fonts-dejavu-core is REQUIRED, not optional: chart_renderer.py draws the title/price/change text
# with PIL ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20/24/18). Without
# the system TTF at that exact path, PIL falls back to ImageFont.load_default() (a ~10px bitmap) → the
# on-device text renders tiny. (matplotlib bundles its OWN DejaVu, but PIL does not — it needs this pkg.)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 ca-certificates tzdata fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY config/ ./config/

# Non-root. /tmp is world-writable so HOME/MPLCONFIGDIR/log-file all work.
USER nobody

ENTRYPOINT ["python", "-m", "trade_monitor"]
