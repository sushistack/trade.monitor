"""AWTRIX3 client for pushing price updates."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class AwtrixClient:
    """Client for interacting with AWTRIX3 devices."""

    def __init__(self, config: Any):
        """
        Initialize AwtrixClient.

        Args:
            config: Configuration object containing host, app_name, icon, and color.
        """
        self.config = config

    def push_price(self, price: float) -> bool:
        """
        Push price update to AWTRIX3.

        Args:
            price: The price to push.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Format price as "XXX.Xk" (e.g. 105.4k)
            formatted_price = f"{price / 1000:,.1f}k"

            payload = {
                "text": formatted_price,
                "icon": getattr(self.config, "icon", None),
                "color": getattr(self.config, "color", None),
            }

            host = getattr(self.config, "host", "localhost")
            app_name = getattr(self.config, "app_name", "trade_monitor")

            url = f"http://{host}/api/custom?name={app_name}"

            with httpx.Client() as client:
                response = client.post(url, json=payload)
                response.raise_for_status()

            logger.info(
                f"Successfully pushed price {formatted_price} "
                f"to AWTRIX3 at {host} (app: {app_name})"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to push price to AWTRIX3: {e}")
            return False
