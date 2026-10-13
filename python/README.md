# syntri-sdk — Python

The Python client for [Syntri](https://github.com/DomaniLabs/Syntri). A thin,
dependency-light wrapper over Syntri's HTTP API (`POST /v1/capture`) exposing
`input`, `output`, and `outcome` capture methods — sync and async — that
**never raise** on transport failures.

- **Zero runtime dependencies.** Standard library only (`urllib`). No `httpx`,
  no `requests`, no `aiohttp`.
- **Non-blocking failures.** Timeouts, network errors and bad responses come
  back as a status on the response, never as an exception.
- **PII-agnostic.** The SDK forwards your raw payload; tokenisation is handled
  server-side.

> This is `syntri-sdk`, the client SDK for application developers. It is a
> separate package from `syntri-contracts`, which is for capability-pack authors.

## Install

```bash
pip install syntri-sdk
```

Requires Python 3.10+.

## Usage

```python
from syntri import Syntri, SyntriConfig

syntri = Syntri(SyntriConfig(
    instance_id="my-app",
    api_key="syn_...",
    base_url="https://your-syntri-host",
))

# Log input
response = syntri.capture.input(
    payload={"message": user_message},
    session_id=session_id,
)

# Log output
syntri.capture.output(
    correlation_id=response.correlation_id,
    payload={"response": bot_reply},
)

# Log outcome
syntri.capture.outcome(
    correlation_id=response.correlation_id,
    payload={"satisfied": True},
)
```

### Async

Every method has an `a`-prefixed async variant with the same signature. The
async variants run the sync transport in a thread pool, so the SDK stays
stdlib-only.

```python
response = await syntri.capture.ainput(payload={"message": user_message})
await syntri.capture.aoutput(correlation_id=response.correlation_id, payload={"response": bot_reply})
await syntri.capture.aoutcome(correlation_id=response.correlation_id, payload={"satisfied": True})
```

## Configuration

`SyntriConfig` fields:

| Field         | Type                               | Default    | Notes                                              |
| ------------- | ---------------------------------- | ---------- | -------------------------------------------------- |
| `instance_id` | `str`                              | *required* | Sent as `instance_id` in every request body.       |
| `api_key`     | `str`                              | *required* | Sent as `Authorization: Bearer <api_key>`.         |
| `base_url`    | `str`                              | *required* | Your Syntri host; `/v1/capture` is appended.       |
| `timeout`     | `float`                            | `2.0`      | Request timeout in **seconds**.                    |
| `on_error`    | `Callable[[SyntriError], None]`    | `None`     | Optional hook invoked on auth/network/unexpected failures. |

## Error handling

Capture calls always return a `CaptureResponse`; they never raise. Inspect
`response.status`:

| `status`        | Meaning                                                              |
| --------------- | -------------------------------------------------------------------- |
| `captured`      | Server accepted the event.                                           |
| `write_failed`  | Server reached but could not persist the event.                      |
| `unprocessable` | Server rejected the event as invalid.                                |
| `unreachable`   | Timeout, network error, or auth rejection (401/403). *Synthesized.*  |
| `unknown_error` | Unexpected non-2xx response. *Synthesized.*                          |

`captured` / `write_failed` / `unprocessable` come from the server;
`unreachable` and `unknown_error` are synthesized client-side.

```python
from syntri import Syntri, SyntriConfig, SyntriError

def on_error(err: SyntriError) -> None:
    print(f"syntri {err.type}: {err.message} (status={err.status})")

syntri = Syntri(SyntriConfig(
    instance_id="my-app",
    api_key="syn_...",
    base_url="https://your-syntri-host",
    on_error=on_error,
))

response = syntri.capture.input(payload={"message": "hi"})
if response.status != "captured":
    ...  # your app keeps running regardless
```

## Development

```bash
cd python
pip install -e ".[dev]"
pytest --tb=short -q
ruff check src/ tests/
mypy src/
```

## Publishing

See [PUBLISHING.md](./PUBLISHING.md).
