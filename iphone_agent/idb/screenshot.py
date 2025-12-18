"""Screenshot utilities for capturing Android device screen."""
import time
import base64
import os
from dataclasses import dataclass
from io import BytesIO

from PIL import Image
from iphone_agent.idb.connection import client
from iphone_agent.idb.connection import client, ensure_connected

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception:  # Optional dependency
    cv2 = None
    np = None


@dataclass
class Screenshot:
    """Represents a captured screenshot."""

    base64_data: str
    width: int
    height: int
    is_sensitive: bool = False

@ensure_connected
def get_screenshot(timeout: int = 10) -> Screenshot:
    """
    Capture a screenshot from the connected IOS device.
    curl -k -u admin:admin "https://your_host_ip/streamer/snapshot" -o screen.jpg

    Args:
        timeout: Timeout in seconds for screenshot operations.

    Returns:
        Screenshot object containing base64 data and dimensions.

    Note:
        If the screenshot fails (e.g., on sensitive screens like payment pages),
        a black fallback image is returned with is_sensitive=True.
    """

    try:
        resp = client.request("/streamer/snapshot", "GET", timeout=float(timeout))
        image_bytes = resp.body

        # Crop black borders (non-black bounding box)
        try:
            if cv2 is None or np is None:
                raise ImportError("cv2/numpy not installed")
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Failed to decode image")

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            threshold = 15
            ys, xs = np.where(gray > threshold)
            if ys.size == 0 or xs.size == 0:
                # All black (or effectively black) -> treat as sensitive
                return _create_fallback_screenshot(is_sensitive=True)

            x_min, x_max = int(xs.min()), int(xs.max())
            y_min, y_max = int(ys.min()), int(ys.max())
            crop = img[y_min : y_max + 1, x_min : x_max + 1]

            ok, buf = cv2.imencode(".png", crop)
            if not ok:
                raise ValueError("Failed to encode cropped image")

            out_bytes = buf.tobytes()
            height, width = crop.shape[:2]
        except Exception:
            # If cropping fails for any reason, fall back to original image bytes
            img_pil = Image.open(BytesIO(image_bytes))
            width, height = img_pil.size
            out_bytes = image_bytes

        return Screenshot(
            base64_data=base64.b64encode(out_bytes).decode("utf-8"),
            width=width,
            height=height,
            is_sensitive=False,
        )
    except Exception:
        # Treat unknown failure as potentially sensitive.
        return _create_fallback_screenshot(is_sensitive=True)
    
def _create_fallback_screenshot(is_sensitive: bool) -> Screenshot:
    """Create a black fallback image when screenshot fails."""
    default_width, default_height = 1080, 2400

    black_img = Image.new("RGB", (default_width, default_height), color="black")
    buffered = BytesIO()
    black_img.save(buffered, format="PNG")
    base64_data = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return Screenshot(
        base64_data=base64_data,
        width=default_width,
        height=default_height,
        is_sensitive=is_sensitive,
    )
