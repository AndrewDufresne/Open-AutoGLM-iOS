"""PiKVM HTTPS connection helpers.

This module provides a small HTTPS request wrapper so callers only need to pass:
- endpoint: the path/query part after the host (e.g. /api/hid/set_connected?connected=1)
- method: GET/POST/...

It intentionally uses only the Python standard library (no requests dependency).
"""

from __future__ import annotations
import os
import base64
import json
import logging
import ssl
import sys
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from functools import wraps

logger = logging.getLogger(__name__)
base_url = os.getenv("PIKVM_BASE_URL", "https://your_host_ip")
username = os.getenv("PIKVM_USERNAME", "admin")
password = os.getenv("PIKVM_PASSWORD", "admin")
verify_ssl = os.getenv("PIKVM_VERIFY_SSL", "0").strip() in {"1", "true", "True"}
_DEFAULT_TIMEOUT = float(os.getenv("PIKVM_TIMEOUT", "10"))

@dataclass(frozen=True)
class HttpsResponse:
	url: str
	status: int
	headers: Mapping[str, str]
	body: bytes

	def text(self, encoding: str = "utf-8", errors: str = "replace") -> str:
		return self.body.decode(encoding, errors)

	def json(self) -> Any:
		return json.loads(self.body)


class PiKvmHttpsClient:
	"""Simple HTTPS client for PiKVM-style endpoints.

	Example:
		client = PiKvmHttpsClient("https://your_host_ip", "admin", "admin", verify_ssl=False)
		client.request("/api/hid/set_connected?connected=1", "POST")
	"""

	def __init__(
		self,
		base_url: str,
		username: str = "admin",
		password: str = "admin",
		*,
		verify_ssl: bool = False,
		timeout: float = 10.0,
	) -> None:
		self._base_url = base_url.rstrip("/")
		self._timeout = timeout
		self._auth_header = _basic_auth_header(username, password)
		self._ssl_context = _build_ssl_context(verify_ssl=verify_ssl)

	@property
	def base_url(self) -> str:
		return self._base_url

	def request(
		self,
		endpoint: str,
		method: str,
		*,
		headers: Mapping[str, str] | None = None,
		data: bytes | None = None,
		json_body: Any | None = None,
		timeout: float | None = None,
	) -> HttpsResponse:
		"""Send an HTTPS request.

		Args:
			endpoint: Path (and optional query) after the host. Leading '/' optional.
			method: HTTP method, e.g. "GET", "POST".
			headers: Optional extra headers.
			data: Optional raw request body.
			json_body: Optional JSON-serializable body (sets Content-Type).
			timeout: Optional per-call timeout.

		Returns:
			HttpsResponse.

		Raises:
			HTTPError/URLError/TimeoutError and other exceptions from urllib.
			Exceptions are printed (stderr) and logged before being re-raised.
		"""

		url = _join_url(self._base_url, endpoint)
		normalized_method = (method or "GET").upper()

		request_headers: dict[str, str] = {"Authorization": self._auth_header}
		if headers:
			request_headers.update(dict(headers))

		body: bytes | None
		if json_body is not None:
			body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
			request_headers.setdefault("Content-Type", "application/json; charset=utf-8")
		else:
			body = data

		# For POST/PUT/PATCH without explicit body, send an empty payload
		# to ensure urllib issues the correct method.
		if body is None and normalized_method in {"POST", "PUT", "PATCH"}:
			body = b""

		req = Request(url=url, data=body, method=normalized_method)
		for key, value in request_headers.items():
			req.add_header(key, value)

		actual_timeout = self._timeout if timeout is None else timeout

		try:
			with urlopen(req, timeout=actual_timeout, context=self._ssl_context) as resp:
				raw = resp.read()
				resp_headers = {k: v for k, v in resp.headers.items()}
				return HttpsResponse(
					url=url,
					status=getattr(resp, "status", 200),
					headers=resp_headers,
					body=raw,
				)
		except HTTPError as e:
			_emit_exception(normalized_method, url, e)
			raise
		except URLError as e:
			_emit_exception(normalized_method, url, e)
			raise
		except TimeoutError as e:
			_emit_exception(normalized_method, url, e)
			raise
		except Exception as e:
			_emit_exception(normalized_method, url, e)
			raise


def _join_url(base_url: str, endpoint: str) -> str:
	if not endpoint:
		return base_url
	if endpoint.startswith("/"):
		return f"{base_url}{endpoint}"
	return f"{base_url}/{endpoint}"


def _basic_auth_header(username: str, password: str) -> str:
	token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
	return f"Basic {token}"


def _build_ssl_context(*, verify_ssl: bool) -> ssl.SSLContext | None:
	"""Create SSL context.

	When verify_ssl=False, this matches `curl -k` behavior.
	"""

	if verify_ssl:
		return None

	ctx = ssl.create_default_context()
	ctx.check_hostname = False
	ctx.verify_mode = ssl.CERT_NONE
	return ctx


def _emit_exception(method: str, url: str, exc: BaseException) -> None:
	msg = f"HTTPS request failed: {method} {url}: {exc}"
	print(msg, file=sys.stderr)
	logger.exception(msg)

def _ensure_connected() -> None:
    client.request(
        "/api/hid/set_connected?connected=1",
        "POST",
        timeout=_DEFAULT_TIMEOUT,
    )


def ensure_connected(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _ensure_connected()
        return fn(*args, **kwargs)

    return wrapper

client = PiKvmHttpsClient(
    base_url,
    username=username,
    password=password,
    verify_ssl=verify_ssl,
)