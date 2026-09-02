#!/bin/bash
# MACS-V2 Daemon Wrapper
# Auto-restarts on crash, loops every 15m. Perfect for pm2 or just nohup.

echo "MACS-V2 Background Daemon Started."

# Activate local venv if it exists (for local dev)
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "/app/.venv/bin/activate" ]; then
    # Railway explicit activation fallback
    source /app/.venv/bin/activate
fi

while true; do
    echo "Running analysis cycle at $(date)..."
    python3 run.py analyze
    echo "Cycle complete. Sleeping 900s..."
    sleep 900
done
