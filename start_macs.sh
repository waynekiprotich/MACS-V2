#!/bin/bash
# MACS-V2 Daemon Wrapper
# Auto-restarts on crash, loops every 15m. Perfect for pm2 or just nohup.

echo "MACS-V2 Background Daemon Started."
while true; do
    echo "Running analysis cycle at $(date)..."
    source venv/bin/activate && python3 run.py analyze
    echo "Cycle complete. Sleeping 900s..."
    sleep 900
done
