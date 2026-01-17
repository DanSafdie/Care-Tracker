import os
import httpx
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

logger = logging.getLogger(__name__)

# HASS configuration from environment
HASS_URL = os.getenv("HASS_URL", "http://192.168.1.50:8123")
HASS_TOKEN = os.getenv("HASS_TOKEN")

def call_hass_script(script_name: str) -> bool:
    """
    Calls a Home Assistant script via REST API (Synchronous).
    """
    if not HASS_TOKEN:
        logger.warning(f"HASS_TOKEN not configured. Skipping script call: {script_name}")
        return False

    url = f"{HASS_URL}/api/services/script/turn_on"
    headers = {
        "Authorization": f"Bearer {HASS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"entity_id": f"script.{script_name}"}

    try:
        # Use a timeout to avoid hanging the backend
        with httpx.Client() as client:
            response = client.post(url, headers=headers, json=payload, timeout=5.0)
            if response.status_code in (200, 201):
                logger.info(f"Successfully called HASS script: {script_name}")
                return True
            else:
                logger.error(f"Failed to call HASS script {script_name}: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error calling HASS script {script_name}: {e}")
        return False
