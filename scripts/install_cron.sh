#!/bin/bash
# Trade Monitor - Cron Installation Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Trade Monitor Cron Setup ==="
echo "Project directory: $PROJECT_DIR"

# Create cron entry
CRON_LINE="* * * * * $PROJECT_DIR/scripts/run.sh >> $PROJECT_DIR/logs/cron.log 2>&1"

echo ""
echo "Installing cron job..."
echo "Cron entry: $CRON_LINE"

# Add to crontab (remove existing trade.monitor entries first)
(crontab -l 2>/dev/null | grep -v "trade.monitor" || true; echo "$CRON_LINE") | crontab -

echo ""
echo "=== Cron Installation Complete ==="
echo ""
echo "Verify with: crontab -l"
echo "Monitor logs: tail -f $PROJECT_DIR/logs/cron.log"
