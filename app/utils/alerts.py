# app/utils/alerts.py
import os
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

def send_slack_alert(
    title: str,
    message: str,
    color: str = "danger",
    fields: Optional[list] = None,
    blocks: Optional[list] = None
):
    """Send alert to Slack channel"""
    if not SLACK_WEBHOOK_URL:
        logger.debug("Slack webhook not configured")
        return
    
    if not blocks:
        blocks = []
    
    # Default blocks
    default_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 {title}",
                "emoji": True
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        }
    ]
    
    if fields:
        for field in fields:
            default_blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*{field.get('title', '')}*\n{field.get('value', '')}"
                    }
                ]
            })
    
    payload = {
        "attachments": [{
            "color": color,
            "blocks": blocks if blocks else default_blocks,
            "ts": int(datetime.now().timestamp())
        }]
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code != 200:
            logger.error(f"Slack alert failed: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {e}")

def alert_on_critical_error(error: Exception, context: Dict[str, Any] = None):
    """Send alert for critical errors"""
    send_slack_alert(
        title="Critical Error",
        message=f"```{str(error)[:500]}```",
        color="danger",
        fields=[
            {"title": "Type", "value": type(error).__name__},
            {"title": "Context", "value": str(context)[:200]} if context else None
        ] if context else None
    )

def alert_on_high_latency(endpoint: str, latency_ms: float, threshold_ms: float = 1000):
    """Alert when API latency is high"""
    send_slack_alert(
        title="High Latency Detected",
        message=f"Endpoint `{endpoint}` took **{latency_ms}ms** (threshold: {threshold_ms}ms)",
        color="warning",
        fields=[
            {"title": "Endpoint", "value": endpoint},
            {"title": "Latency", "value": f"{latency_ms}ms"},
            {"title": "Threshold", "value": f"{threshold_ms}ms"}
        ]
    )

def alert_on_database_pool_full(pool_stats: dict):
    """Alert when database connection pool is nearly full"""
    usage = pool_stats.get("usage_percent", 0)
    send_slack_alert(
        title="Database Pool Warning",
        message=f"Connection pool is at **{usage}%** capacity",
        color="warning",
        fields=[
            {"title": "Active Connections", "value": str(pool_stats.get("checked_out", 0))},
            {"title": "Max Connections", "value": str(pool_stats.get("max_connections", 0))},
            {"title": "Usage", "value": f"{usage}%"}
        ]
    )