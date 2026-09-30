# Contributing to syntri-sdk

This repo holds one client SDK per language, each in its own top-level
directory. TypeScript is the reference implementation — read
[`typescript/`](./typescript) before starting a new language, and mirror its
shape.

## What every SDK must be

- **Thin.** It wraps Syntri's HTTP API (`POST /v1/capture`) and nothing more.
  No business logic. No data transformation.
- **Dependency-light.** Prefer the language's native HTTP client. The
  TypeScript SDK has zero runtime dependencies (native `fetch`). Match that
  spirit.
- **Non-throwing.** A capture call must never crash the caller's app. Transport
  failures (timeout, network, auth, unexpected status) resolve to a response
  with a failure `status`, never an exception/panic.
- **PII-agnostic.** The SDK sends the raw payload. Tokenisation is server-side.
  The SDK never inspects or scrubs payload contents.
- **Contract-faithful.** Types/structs mirror the server contract exactly. When
  the server contract changes, the SDK types change to match. SDKs do **not**
  import from `syntri-contracts` — that is a separate package for a separate
  audience (capability-pack authors).

## Directory layout

```
<language>/
├── src/            # or the language's conventional source dir
├── tests/
├── README.md       # install, configure, three-call example, error handling
├── PUBLISHING.md   # how releases are cut for this language
└── <manifest>      # package.json / pyproject.toml / go.mod / etc.
```

## Required methods

Every SDK exposes a client with three capture methods:

| Method    | Sends `event_type` | Requires `correlation_id`? | Returns |
| --------- | ------------------ | -------------------------- | ------- |
| `input`   | `input`            | no                         | a capture response whose `correlation_id` links later events |
| `output`  | `output`           | yes                        | a capture response |
| `outcome` | `outcome`          | yes                        | a capture response |

Each method accepts a `payload` (arbitrary JSON object) plus optional
`sessionId`/`session_id` and `metadata`. The client is configured with
`instanceId`, `apiKey`, `baseUrl`, and optional `timeout` and error hook.

The client must:

- send `instance_id` in every request body (never infer it),
- set `Authorization: Bearer <apiKey>` and `Content-Type: application/json`,
- time out after the configured timeout (default 2000 ms) → `unreachable`,
- measure and report round-trip latency,
- surface auth/network/unexpected failures through the language's idiomatic
  error hook without throwing.

## Response contract

```
event_id       string | null
status         captured | write_failed | unprocessable | unreachable | unknown_error
correlation_id string | null
latency_ms     number
```

`captured` / `write_failed` / `unprocessable` come from the server;
`unreachable` (timeout, network, auth) and `unknown_error` (unexpected non-2xx)
are synthesized client-side.

## Test requirements

Mock the HTTP layer — **no real network calls in tests.** Cover at minimum:

- `input` returns a `correlation_id`
- `output` / `outcome` send the correct `correlation_id`
- timeout → `unreachable`, does not throw
- network error → `unreachable`, does not throw
- `401` → invokes the error hook, does not throw
- correct auth header is sent
- `latency_ms` is populated

## CI requirements

Add a job to [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) scoped to
your language directory (via `defaults.run.working-directory`). It must, at
minimum, install, typecheck/lint, test, and build on every push and PR to
`main`.

## Publish workflow

Add a `.github/workflows/publish-<registry>.yml` triggered by a
**language-prefixed tag** so other languages' releases don't trigger it:

- TypeScript → `typescript/v*` → npm
- Python → `python/v*` → PyPI
- Go → `go/v*` → module proxy (tag is the release)

Document the one-time registry setup and the tag command in the language's
`PUBLISHING.md`.
