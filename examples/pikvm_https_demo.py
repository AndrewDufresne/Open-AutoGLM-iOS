"""Demo for PiKVM HTTPS wrapper.

Equivalent to:
  curl -k -X POST -u admin:admin "https://<ip>/api/hid/events/send_mouse_move?to_x=0&to_y=32500"
  curl -k -X POST -u admin:admin "https://<ip>/api/hid/set_connected?connected=1"
  curl -k -u admin:admin "https://<ip>/streamer/snapshot" -o screen.jpg

Usage (Windows cmd):
  set PIKVM_BASE_URL=https://YourPiKVMIP
  set PIKVM_USERNAME=admin
  set PIKVM_PASSWORD=admin
  python examples\pikvm_https_demo.py
"""

from __future__ import annotations

import os

from iphone_agent.idb.connection import PiKvmHttpsClient


def main() -> None:
    base_url = os.getenv("PIKVM_BASE_URL", "https://YourPiKVMIP")
    username = os.getenv("PIKVM_USERNAME", "admin")
    password = os.getenv("PIKVM_PASSWORD", "admin")
    verify_ssl = os.getenv("PIKVM_VERIFY_SSL", "0").strip() in {"1", "true", "True"}

    client = PiKvmHttpsClient(
        base_url,
        username=username,
        password=password,
        verify_ssl=verify_ssl,
        timeout=10.0,
    )

    # connect idb
    client.request("/api/hid/set_connected?connected=1", "POST")

    # screen extremes (same as your curl examples)
    client.request("/api/hid/events/send_mouse_move?to_x=0&to_y=32500", "POST")
    client.request("/api/hid/events/send_mouse_move?to_x=0&to_y=-32500", "POST")
    client.request("/api/hid/events/send_mouse_move?to_x=-32500&to_y=0", "POST")
    client.request("/api/hid/events/send_mouse_move?to_x=32500&to_y=0", "POST")

    # snapshot
    resp = client.request("/streamer/snapshot", "GET")
    with open("screen.jpg", "wb") as f:
        f.write(resp.body)

    print("OK: wrote screen.jpg")


if __name__ == "__main__":
    main()
