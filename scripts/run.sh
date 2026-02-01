#!/bin/bash
# Trade Monitor - Run Script
# Wrapper for cron execution with timeout protection

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Activate virtual environment
source venv/bin/activate

export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run with 55-second timeout (stay under 1-minute cron interval)
timeout 55 python -m trade_monitor

exit $?
