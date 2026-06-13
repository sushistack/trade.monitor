"""HTTP multipart uploader for embedded devices."""
import logging
import time
from typing import Optional

import requests
from requests.exceptions import RequestException, Timeout

from .config import UploadConfig
from .models import ChartImage, UploadResult

logger = logging.getLogger(__name__)


class ImageUploader:
    """Uploads images to embedded devices via HTTP multipart."""

    def __init__(self, config: UploadConfig):
        """Initialize uploader with configuration."""
        self.config = config

    def upload(
        self,
        host: str,
        image: ChartImage
    ) -> UploadResult:
        """
        Upload single image to target host.

        Args:
            host: Target IP/hostname (e.g., "192.168.0.20")
            image: Chart image to upload

        Returns:
            UploadResult with success status
        """
        url = f"http://{host}/doUpload?dir={self.config.dir}"
        filename = image.full_filename

        start_time = time.time()
        last_error: Optional[str] = None

        for attempt in range(self.config.retries):
            try:
                files = {
                    'file': (filename, image.image_bytes, 'image/jpeg')
                }

                response = requests.post(
                    url,
                    files=files,
                    timeout=self.config.timeout,
                )

                duration_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    logger.info(
                        f"Uploaded {filename} to {host} "
                        f"({duration_ms:.0f}ms)"
                    )
                    return UploadResult(
                        success=True,
                        host=host,
                        filename=filename,
                        duration_ms=duration_ms
                    )
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    logger.warning(
                        f"Upload failed (attempt {attempt + 1}): {last_error}"
                    )

            except Timeout:
                last_error = "Timeout"
                logger.warning(f"Upload timeout (attempt {attempt + 1}): {host}")
            except RequestException as e:
                last_error = f"Request error: {e}"
                logger.warning(f"Upload error (attempt {attempt + 1}): {e}")

            # Exponential backoff
            if attempt < self.config.retries - 1:
                time.sleep(2 ** attempt)

        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Failed to upload {filename} to {host}: {last_error}")

        return UploadResult(
            success=False,
            host=host,
            filename=filename,
            error=last_error,
            duration_ms=duration_ms
        )

    def upload_batch(
        self,
        uploads: list[tuple[str, ChartImage]]
    ) -> list[UploadResult]:
        """
        Upload multiple images.

        Args:
            uploads: List of (host, ChartImage) tuples

        Returns:
            List of UploadResult objects
        """
        results = []
        for host, image in uploads:
            result = self.upload(host, image)
            results.append(result)
        return results
