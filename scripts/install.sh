#!/bin/bash
# Trade Monitor - Installation Script
# Uses uv for fast Python environment setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Trade Monitor Installation ==="
echo "Project directory: $PROJECT_DIR"

cd "$PROJECT_DIR"

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "Error: uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "Using: $(uv --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
uv venv venv

# Install dependencies
echo ""
echo "Installing dependencies..."
VIRTUAL_ENV=venv uv pip install -r requirements.txt

# Create directories
echo ""
echo "Creating directories..."
mkdir -p logs

# Copy example env if not exists
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "Created .env from template"
    fi
fi

# Make scripts executable
chmod +x scripts/*.sh

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env if needed (optional for Binance public API)"
echo "2. Test run: ./scripts/run.sh"
echo "3. Install cron: ./scripts/install_cron.sh"
