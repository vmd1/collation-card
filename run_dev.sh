#!/bin/bash
# Development runner script

export SECRET_KEY="dev-secret-key-change-in-production"
export DATABASE_URL="sqlite:////tmp/virtual_card.db"
export MEDIA_PATH="/tmp/virtual_card_media"
export REDIS_URL="memory://"

# Determine script directory (absolute)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Virtual Card services in development mode..."
echo "=================================================="
echo ""
echo "Dashboard: http://localhost:8000"
echo "Submit:    http://localhost:8001"
echo "Card:      http://localhost:8002"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=================================================="

# Create directories
mkdir -p "$MEDIA_PATH"
# Normalize DATABASE_URL to a filesystem path and create its directory
DB_FILE="${DATABASE_URL#sqlite:}"
DB_FILE="$(echo "$DB_FILE" | sed 's|^/*|/|')"
mkdir -p "$(dirname "$DB_FILE")"

# Start services in background
(
	cd "$SCRIPT_DIR/services/dashboard" && python app.py
) &
PID1=$!

(
	cd "$SCRIPT_DIR/services/submit" && python app.py
) &
PID2=$!

(
	cd "$SCRIPT_DIR/services/card" && python app.py
) &
PID3=$!

# Wait for any service to exit
wait $PID1 $PID2 $PID3

# Cleanup
kill $PID1 $PID2 $PID3 2>/dev/null
