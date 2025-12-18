"""Input utilities for Android device text input."""
import time
import requests
from iphone_agent.idb.connection import client, ensure_connected

@ensure_connected
def copy_text(text: str, device_id: str | None = None) -> None:
    """
    Type text into the currently focused input field.
    """
    try:
        resp = requests.post(
            "http://127.0.0.1:6666/content",
            json={"content": text,
                  "launch_app":False},
        )
        resp.raise_for_status()
    except requests.RequestException:
        pass
    client.request(
        "/api/hid/events/send_shortcut?keys=AltLeft,KeyC",
        "POST",
    )
    time.sleep(0.5)
    client.request(
        "/api/hid/events/send_shortcut?keys=AltLeft,KeyC",
        "POST",
    )
    time.sleep(0.5)
    client.request(
        "/api/hid/events/send_shortcut?keys=MetaRight,KeyV",
        "POST",
    )
    time.sleep(0.5)