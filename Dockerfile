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

# ponytail: matplotlib/pandas/numpy/Pillow ship self-contained manylinux wheels, so the only
# system libs needed are libgomp1 (numpy/scipy openmp) + ca-certs (TLS to Binance/Yahoo/LaMetric)
# + tzdata (Asia/Seoul). Add a .so here only if a runtime ImportError ever shows up.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY config/ ./config/

# Non-root. /tmp is world-writable so HOME/MPLCONFIGDIR/log-file all work.
USER nobody

ENTRYPOINT ["python", "-m", "trade_monitor"]
