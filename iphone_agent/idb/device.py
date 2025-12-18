"""PiKVM HID device control utilities.

All operations are executed via the shared HTTPS `client` and PiKVM HID endpoints.
"""

from __future__ import annotations
import os
import time
import requests
from iphone_agent.config.apps import APP_PACKAGES
from iphone_agent.idb.connection import client, ensure_connected
_DEFAULT_TIMEOUT = float(os.getenv("PIKVM_TIMEOUT", "10"))

# @ensure_connected
def tap(x: int, y: int, device_id: str | None = None, delay: float = 1.0) -> None:
    """
    Tap at the specified coordinates.
    Args:
        x: X coordinate.
        y: Y coordinate.
        delay: Delay in seconds after tap.
    """
    client.request(
    f"/api/hid/events/send_mouse_move?to_x={x}&to_y={y}",
    "POST",
    timeout=_DEFAULT_TIMEOUT,
    )
    # time.sleep(0.5)
    client.request(
        "/api/hid/events/send_mouse_button?button=left",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    # time.sleep(delay)


@ensure_connected
def double_tap(
    x: int, y: int, delay: float = 1.0
) -> None:
    """
    Double tap at the specified coordinates.
    Args:
        x: X coordinate.
        y: Y coordinate.
        delay: Delay in seconds after double tap.
    """
    client.request(
    f"/api/hid/events/send_mouse_move?to_x={x}&to_y={y}",
    "POST",
    timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(0.5)
    client.request(
        "/api/hid/events/send_mouse_button?button=left",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(0.2)
    client.request(
        "/api/hid/events/send_mouse_button?button=left",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(delay)


@ensure_connected
def long_press(
    x: int,
    y: int,
    duration_ms: int = 3000,
    delay: float = 1.0,
) -> None:
    """
    Long press at the specified coordinates.

    Args:
        x: X coordinate.
        y: Y coordinate.
        duration_ms: Duration of press in milliseconds.
        device_id: Optional ADB device ID.
        delay: Delay in seconds after long press.
    """
    client.request(
    f"/api/hid/events/send_mouse_move?to_x={x}&to_y={y}",
    "POST",
    timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(0.5)
    client.request(
        "/api/hid/events/send_mouse_button?button=left&state=1",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(max(0.0, duration_ms / 1000.0))
    client.request(
        "/api/hid/events/send_mouse_button?button=left&state=0",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(delay)


@ensure_connected
def swipe(
    start_x: int,
    start_y: int,
    end_x: int,
    end_y: int,
    duration_ms: int | None = 1000,
    delay: float = 1.0,
) -> None:
    """
    Swipe from start to end coordinates.

    Args:
        start_x: Starting X coordinate.
        start_y: Starting Y coordinate.
        end_x: Ending X coordinate.
        end_y: Ending Y coordinate.
        duration_ms: Duration of swipe in milliseconds (auto-calculated if None).
        delay: Delay in seconds after swipe.
    """
    print(start_x, start_y, end_x, end_y, duration_ms)
    client.request(
        f"/api/hid/events/send_mouse_move?to_x={start_x}&to_y={start_y}",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(0.2)
    client.request(
        "/api/hid/events/send_mouse_button?button=left&state=1",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )

    # If a duration is provided, keep the swipe paced (best-effort).
    if duration_ms is not None and duration_ms > 0:
        duration_s = duration_ms / 1000.0

        # Aim for ~60 Hz updates; clamp steps to avoid excessive requests.
        step_dt = 1.0 / 60.0
        steps = int(duration_s / step_dt)
        steps = max(2, min(steps, 120))

        start_t = time.perf_counter()
        for i in range(1, steps):
            t = i / steps
            ix = int(round(start_x + (end_x - start_x) * t))
            iy = int(round(start_y + (end_y - start_y) * t))

            client.request(
                f"/api/hid/events/send_mouse_move?to_x={ix}&to_y={iy}",
                "POST",
                timeout=_DEFAULT_TIMEOUT,
            )

            # Pace to duration (best-effort).
            next_t = start_t + t * duration_s
            time.sleep(max(0.0, next_t - time.perf_counter()))

    client.request(
        f"/api/hid/events/send_mouse_move?to_x={end_x}&to_y={end_y}",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(0.2)
    client.request(
        "/api/hid/events/send_mouse_button?button=left&state=0",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(delay)


@ensure_connected
def back(delay: float = 1.0) -> None:
    """
    Press the back button.
    client.request("/api/hid/events/send_shortcut?keys=Tab,KeyB", "POST", timeout=float(timeout))

    Args:
        delay: Delay in seconds after pressing back.
    """
    client.request(
        "/api/hid/events/send_shortcut?keys=Tab,KeyB",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(delay)


@ensure_connected
def home(delay: float = 1.0) -> None:
    """
    Press the home button.
    Args:
        delay: Delay in seconds after pressing home.
    """
    client.request(
        "/api/hid/events/send_shortcut?keys=AltLeft,KeyH",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )
    time.sleep(delay)


@ensure_connected
def launch_app(app_name: str, delay: float = 1.0) -> bool:
    """
    Launch an app by name.
    Args:
        app_name: The app name (must be in APP_PACKAGES).
        delay: Delay in seconds after launching.

    Returns:
        True if app was launched, False if app not found.
    """
    if app_name not in APP_PACKAGES:
        return False
    
    try:
        resp = requests.post(
            "http://127.0.0.1:6666/content",
            json={"content": APP_PACKAGES[app_name],
                  "launch_app":True},
        )
        resp.raise_for_status()
    except requests.RequestException:
        return False
    
    client.request(
        "/api/hid/events/send_shortcut?keys=AltLeft,KeyC",
        "POST",
    )
    time.sleep(0.5)
    
    client.request(
        "/api/hid/events/send_shortcut?keys=AltLeft,KeyC",
        "POST",
    )
    time.sleep(1)
    client.request(
        "/api/hid/events/send_shortcut?keys=AltLeft,KeyO",
        "POST",
    )
    time.sleep(delay)
    return True
