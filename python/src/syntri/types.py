# These types mirror the Syntri server contract for POST /v1/capture.
# If the server contract changes, these types must change to match.
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

CaptureEventType = Literal["input", "output", "outcome"]

# Statuses returned by the server contract: "captured" | "write_failed" |
# "unprocessable". The SDK additionally synthesizes transport-level outcomes
# the server never had a chance to report:
#   "unreachable"   — timeout, network error, or auth rejection (401/403)
#   "unknown_error" — an unexpected non-2xx response
# The SDK never raises, so every call returns one of these statuses.
CaptureStatus = Literal[
    "captured",
    "write_failed",
    "unprocessable",
    "unreachable",
    "unknown_error",
]


@dataclass
class CaptureResponse:
    event_id: str | None
    status: CaptureStatus
    correlation_id: str | None
    latency_ms: float


@dataclass
class SyntriError:
    type: Literal["network", "auth", "unprocessable", "write_failed", "unknown"]
    message: str
    status: int | None = None


@dataclass
class SyntriConfig:
    instance_id: str
    api_key: str
    base_url: str
    timeout: float = 2.0  # seconds, default 2.0
    on_error: Callable[[SyntriError], None] | None = None
