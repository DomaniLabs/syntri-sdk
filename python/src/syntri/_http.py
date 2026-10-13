"""Internal HTTP transport. Stdlib only — no httpx, no requests.

A single ``post`` helper wraps ``urllib`` and the contract the rest of the SDK
relies on: it never raises. Every failure — timeout, DNS, connection refused,
an HTTP error status, an unreadable or non-JSON body — comes back as a tuple so
the caller can decide what status to synthesize without a try/except of its own.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


def post(
    url: str,
    payload: dict[str, Any],
    api_key: str,
    timeout: float,
) -> tuple[dict[str, Any] | None, int | None, float]:
    """POST ``payload`` as JSON to ``url`` with a bearer token.

    Returns ``(response_dict, status_code, latency_ms)``:

    - On a readable JSON 2xx response: ``(body, status, latency_ms)``.
    - On an HTTP error status, or a 2xx whose body is not a JSON object:
      ``(None, status, latency_ms)`` — the status is preserved so the caller
      can distinguish auth (401/403) from an otherwise unexpected response.
    - On a timeout or network error (no response at all):
      ``(None, None, latency_ms)``.

    Never raises.
    """
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    start = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = int(response.status)
            raw = response.read()
    except urllib.error.HTTPError as err:
        # Non-2xx. The status is known and worth keeping; the body is irrelevant
        # because the caller synthesizes its own response for error statuses.
        return None, int(err.code), _elapsed_ms(start)
    except (urllib.error.URLError, TimeoutError):
        # Timeout, DNS failure, connection refused — Syntri never answered.
        return None, None, _elapsed_ms(start)
    except Exception:
        # Belt and braces: the transport must never raise into the SDK.
        return None, None, _elapsed_ms(start)

    latency_ms = _elapsed_ms(start)
    try:
        body: Any = json.loads(raw.decode("utf-8")) if raw else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        # A 2xx with an unreadable body: status is known, so the caller can
        # treat it as an unexpected response rather than a lost connection.
        return None, status, latency_ms

    if not isinstance(body, dict):
        return None, status, latency_ms
    return body, status, latency_ms


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000.0
