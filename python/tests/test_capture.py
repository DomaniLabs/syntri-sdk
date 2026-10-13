"""Tests for CaptureClient. The HTTP layer is mocked — no real network calls."""
from __future__ import annotations

import json
import urllib.error
from typing import Any
from unittest.mock import patch

from syntri import Syntri, SyntriConfig, SyntriError

BASE_CONFIG = dict(
    instance_id="my-app",
    api_key="test-key-123",
    base_url="https://api.syntri.test",
)


class FakeResponse:
    """Minimal stand-in for the object urllib.request.urlopen yields."""

    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False


def _json_response(body: dict[str, Any], status: int = 200) -> FakeResponse:
    return FakeResponse(status, json.dumps(body).encode("utf-8"))


def _sent_body(mock_urlopen: Any) -> dict[str, Any]:
    """Decode the JSON body of the Request passed to urlopen."""
    request = mock_urlopen.call_args.args[0]
    return json.loads(request.data.decode("utf-8"))


# ----------------------------------------------------------------------
# input / output / outcome shape
# ----------------------------------------------------------------------


def test_input_returns_correlation_id() -> None:
    body = {"event_id": "evt_1", "status": "captured", "correlation_id": "evt_1"}
    with patch("urllib.request.urlopen", return_value=_json_response(body)) as m:
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        res = syntri.capture.input(payload={"message": "hi"})

    assert res.status == "captured"
    assert res.correlation_id == "evt_1"
    assert res.event_id == "evt_1"

    sent = _sent_body(m)
    assert sent["instance_id"] == "my-app"
    assert sent["event_type"] == "input"
    assert sent["payload"] == {"message": "hi"}
    assert "correlation_id" not in sent


def test_output_sends_correlation_id() -> None:
    body = {"event_id": "evt_2", "status": "captured", "correlation_id": "evt_1"}
    with patch("urllib.request.urlopen", return_value=_json_response(body)) as m:
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        syntri.capture.output(correlation_id="evt_1", payload={"response": "ok"})

    sent = _sent_body(m)
    assert sent["event_type"] == "output"
    assert sent["correlation_id"] == "evt_1"
    assert sent["payload"] == {"response": "ok"}


def test_outcome_sends_correlation_id() -> None:
    body = {"event_id": "evt_3", "status": "captured", "correlation_id": "evt_1"}
    with patch("urllib.request.urlopen", return_value=_json_response(body)) as m:
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        syntri.capture.outcome(correlation_id="evt_1", payload={"satisfied": True})

    sent = _sent_body(m)
    assert sent["event_type"] == "outcome"
    assert sent["correlation_id"] == "evt_1"
    assert sent["payload"] == {"satisfied": True}


# ----------------------------------------------------------------------
# failure paths — the SDK must never raise
# ----------------------------------------------------------------------


def test_timeout_returns_unreachable() -> None:
    with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        syntri = Syntri(SyntriConfig(**BASE_CONFIG, timeout=0.01))
        res = syntri.capture.input(payload={"message": "hi"})

    assert res.status == "unreachable"
    assert res.event_id is None
    assert res.correlation_id is None
    assert isinstance(res.latency_ms, float)


def test_network_error_returns_unreachable() -> None:
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        res = syntri.capture.input(payload={"message": "hi"})

    assert res.status == "unreachable"
    assert res.event_id is None
    assert res.correlation_id is None


def test_auth_error_calls_on_error() -> None:
    errors: list[SyntriError] = []
    http_error = urllib.error.HTTPError(
        url="https://api.syntri.test/v1/capture",
        code=401,
        msg="Unauthorized",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )
    with patch("urllib.request.urlopen", side_effect=http_error):
        syntri = Syntri(SyntriConfig(**BASE_CONFIG, on_error=errors.append))
        res = syntri.capture.input(payload={"message": "hi"})

    assert res.status == "unreachable"
    assert len(errors) == 1
    assert errors[0].type == "auth"
    assert errors[0].status == 401


def test_unexpected_status_returns_unknown_error() -> None:
    errors: list[SyntriError] = []
    http_error = urllib.error.HTTPError(
        url="https://api.syntri.test/v1/capture",
        code=500,
        msg="Server Error",
        hdrs=None,  # type: ignore[arg-type]
        fp=None,
    )
    with patch("urllib.request.urlopen", side_effect=http_error):
        syntri = Syntri(SyntriConfig(**BASE_CONFIG, on_error=errors.append))
        res = syntri.capture.input(payload={})

    assert res.status == "unknown_error"
    assert errors[0].type == "unknown"
    assert errors[0].status == 500


# ----------------------------------------------------------------------
# request details
# ----------------------------------------------------------------------


def test_sends_auth_header() -> None:
    body = {"event_id": "e", "status": "captured", "correlation_id": "e"}
    with patch("urllib.request.urlopen", return_value=_json_response(body)) as m:
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        syntri.capture.input(payload={})

    request = m.call_args.args[0]
    assert request.full_url == "https://api.syntri.test/v1/capture"
    assert request.get_method() == "POST"
    assert request.get_header("Authorization") == "Bearer test-key-123"
    assert request.get_header("Content-type") == "application/json"


def test_latency_ms_populated() -> None:
    body = {"event_id": "e", "status": "captured", "correlation_id": "e"}
    with patch("urllib.request.urlopen", return_value=_json_response(body)):
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        res = syntri.capture.input(payload={})

    assert isinstance(res.latency_ms, float)
    assert res.latency_ms >= 0


def test_passes_session_id_and_metadata() -> None:
    body = {"event_id": "e", "status": "captured", "correlation_id": "e"}
    with patch("urllib.request.urlopen", return_value=_json_response(body)) as m:
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        syntri.capture.input(
            payload={"a": 1},
            session_id="sess-1",
            metadata={"source": "web"},
        )

    sent = _sent_body(m)
    assert sent["session_id"] == "sess-1"
    assert sent["metadata"] == {"source": "web"}


# ----------------------------------------------------------------------
# async
# ----------------------------------------------------------------------


async def test_async_input() -> None:
    body = {"event_id": "evt_1", "status": "captured", "correlation_id": "evt_1"}
    with patch("urllib.request.urlopen", return_value=_json_response(body)) as m:
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        res = await syntri.capture.ainput(payload={"message": "hi"})

    assert res.status == "captured"
    assert res.correlation_id == "evt_1"
    sent = _sent_body(m)
    assert sent["event_type"] == "input"


async def test_async_timeout_does_not_raise() -> None:
    with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
        syntri = Syntri(SyntriConfig(**BASE_CONFIG, timeout=0.01))
        res = await syntri.capture.ainput(payload={"message": "hi"})

    assert res.status == "unreachable"
    assert res.event_id is None


async def test_async_output_and_outcome() -> None:
    body = {"event_id": "evt_2", "status": "captured", "correlation_id": "evt_1"}
    with patch("urllib.request.urlopen", return_value=_json_response(body)) as m:
        syntri = Syntri(SyntriConfig(**BASE_CONFIG))
        await syntri.capture.aoutput(correlation_id="evt_1", payload={"r": 1})
        assert _sent_body(m)["event_type"] == "output"
        await syntri.capture.aoutcome(correlation_id="evt_1", payload={"ok": True})
        assert _sent_body(m)["event_type"] == "outcome"
