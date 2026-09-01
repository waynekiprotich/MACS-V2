import requests
import logging
from datetime import datetime, timezone

from config.settings import settings

logger = logging.getLogger(__name__)

def send_discord_signal(symbol: str, side: str, price: float, strategy: str, ai_score: float = None, notes: str = ""):
    """Send a trade signal to Discord via webhook."""
    webhook_url = getattr(settings, "DISCORD_WEBHOOK_URL", None)
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL is not set. Skipping Discord notification.")
        return

    side_upper = side.upper()
    color = 0x00FF00 if side_upper == "BUY" else 0xFF0000

    embed = {
        "title": f"🚨 MACS-V2 Trade Signal: {side_upper} {symbol}",
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": [
            {"name": "Symbol", "value": symbol, "inline": True},
            {"name": "Action", "value": side_upper, "inline": True},
            {"name": "Price", "value": f"${price:.2f}" if price else "MKT", "inline": True},
            {"name": "Strategy", "value": strategy, "inline": True},
        ]
    }
    
    if ai_score is not None:
        embed["fields"].append({"name": "AI Score", "value": f"{ai_score:.2f}", "inline": True})
        
    if notes:
        embed["fields"].append({"name": "Notes", "value": notes, "inline": False})

    payload = {
        "username": "MACS-V2 Bot",
        "embeds": [embed]
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=5.0)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord notification: {e}")
