"""AWTRIX3 client for pushing price updates."""

import base64
import io
import logging
from typing import Any, Optional

import httpx
import requests
from PIL import Image

logger = logging.getLogger(__name__)

_LAMETRIC_CDN = "https://developer.lametric.com/content/apps/icon_thumbs/{id}.png"


def _fetch_icon_b64(icon_id: str) -> Optional[str]:
    """Fetch a LaMetric icon by ID, resize to 8x8, return as base64 JPEG string."""
    try:
        resp = requests.get(_LAMETRIC_CDN.format(id=icon_id), timeout=5)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img = img.resize((8, 8), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        logger.warning(f"Could not fetch icon {icon_id} from LaMetric CDN: {e}")
        return None


class AwtrixClient:
    """Client for interacting with AWTRIX3 devices."""

    def __init__(self, config: Any):
        self.config = config
        self._icon_b64: Optional[str] = None

        icon_id = getattr(config, "icon", None)
        if icon_id and str(icon_id).isdigit():
            self._icon_b64 = _fetch_icon_b64(str(icon_id))
            if self._icon_b64:
                logger.info(f"Loaded icon {icon_id} from LaMetric CDN")
            else:
                logger.warning(f"Icon {icon_id} not available, Awtrix will show no icon")

    def push_price(self, price: float) -> bool:
        """Push price update to AWTRIX3."""
        try:
            formatted_price = f"{price / 1000:,.1f}k"

            payload = {
                "text": formatted_price,
                "color": getattr(self.config, "color", None),
            }

            if self._icon_b64:
                payload["icon"] = self._icon_b64
            else:
                icon = getattr(self.config, "icon", None)
                if icon:
                    payload["icon"] = icon

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
