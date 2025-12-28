#!/usr/bin/env python3
"""Failure notification utilities for Dell R630 pipelines"""
import os
import requests
from datetime import datetime

def send_alert(message, level="ERROR"):
    """Send alert via multiple channels"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    emoji = {"INFO": "✅", "WARNING": "⚠️", "ERROR": "❌"}.get(level, "ℹ️")
    
    full_message = f"{emoji} [{timestamp}] Dell R630: {message}"
    
    # Log to file always
    with open("/home/george/GB-Power-Market-JJ/logs/alerts.log", "a") as f:
        f.write(f"{full_message}\n")
    
    # Telegram (if configured)
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_chat = os.environ.get("TELEGRAM_CHAT_ID")
    
    if telegram_token and telegram_chat:
        try:
            requests.post(
                f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                json={"chat_id": telegram_chat, "text": full_message},
                timeout=5
            )
        except Exception as e:
            print(f"Telegram failed: {e}")
    
    # Print to console
    print(full_message)

def wrap_with_alerts(func):
    """Decorator to add alerts to any function"""
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        try:
            result = func(*args, **kwargs)
            send_alert(f"{func_name} completed successfully", level="INFO")
            return result
        except Exception as e:
            send_alert(f"{func_name} FAILED: {str(e)}", level="ERROR")
            raise
    return wrapper

if __name__ == "__main__":
    # Test alerts
    send_alert("Alert system initialized", level="INFO")
    print("To enable Telegram: export TELEGRAM_BOT_TOKEN=your_token TELEGRAM_CHAT_ID=your_chat_id")
