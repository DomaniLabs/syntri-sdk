"""The Syntri client entry point."""
from __future__ import annotations

from syntri.capture import CaptureClient
from syntri.types import SyntriConfig


class Syntri:
    """Syntri client. Construct once with your instance id, API key and base
    URL, then use ``.capture`` to record input, output and outcome events.

    The SDK never raises: capture calls always return a ``CaptureResponse`` so a
    Syntri failure can never crash your app.
    """

    def __init__(self, config: SyntriConfig) -> None:
        self.capture = CaptureClient(config)
