#!/bin/bash
# Trade Monitor - Cron Removal Script

echo "Removing trade.monitor cron entries..."

crontab -l 2>/dev/null | grep -v "trade.monitor" | crontab - || true

echo "Done. Verify with: crontab -l"
