# syntri

Syntri client SDK for TypeScript and Node.js.

A thin wrapper over Syntri's HTTP capture API. No runtime dependencies — it
uses native `fetch` (Node 18+ and all modern browsers). It contains no business
logic: you call three methods, it makes three HTTP requests.

## Install

```bash
npm install syntri
```

## Configure

```typescript
import { Syntri } from 'syntri'

const syntri = new Syntri({
  instanceId: 'my-app',
  apiKey: process.env.SYNTRI_API_KEY!,
  baseUrl: process.env.SYNTRI_BASE_URL!,
})
```

| Option       | Type                            | Required | Default | Notes                                             |
| ------------ | ------------------------------- | -------- | ------- | ------------------------------------------------- |
| `instanceId` | `string`                        | yes      | —       | Sent as `instance_id` in every request body.      |
| `apiKey`     | `string`                        | yes      | —       | Sent as `Authorization: Bearer <apiKey>`.         |
| `baseUrl`    | `string`                        | yes      | —       | Base URL of your Syntri deployment.               |
| `timeout`    | `number`                        | no       | `2000`  | Request timeout in ms. On timeout → `unreachable`.|
| `onError`    | `(error: SyntriError) => void`  | no       | —       | Called on auth/network/unexpected errors.         |

## The three calls

Syntri captures each decision your system makes as a chain of events: what came
**in**, what went **out**, and what the **outcome** was. `input` returns a
`correlation_id` that links the later `output` and `outcome` events to it.

```typescript
// Log what came in
const { correlation_id } = await syntri.capture.input({
  payload: { message: userMessage, userId: user.id },
  sessionId: sessionId,
})

// Run your model / logic
const result = await myModel.process(userMessage)

// Log what went out
await syntri.capture.output({
  correlationId: correlation_id!,
  payload: { response: result.text, confidence: result.score },
})

// Later, when you know the outcome
await syntri.capture.outcome({
  correlationId: correlation_id!,
  payload: { satisfied: userRatedPositive, action_taken: result.action },
})
```

`payload` and `metadata` are arbitrary JSON objects. PII tokenisation happens
server-side — the SDK sends your payload as-is and never inspects or transforms
it.

## Response

Every call resolves to a `CaptureResponse`:

```typescript
interface CaptureResponse {
  event_id: string | null
  status:
    | 'captured'       // server accepted the event
    | 'write_failed'   // server could not persist it
    | 'unprocessable'  // server rejected the event body
    | 'unreachable'    // timeout, network error, or auth rejection
    | 'unknown_error'  // an unexpected non-2xx response
  correlation_id: string | null
  latency_ms: number   // SDK-measured round trip
}
```

## Error handling — why the SDK never throws

Observability must never take down the thing it observes. **No capture call
throws under any circumstance.** If Syntri times out, is unreachable, rejects
your API key, or returns an unexpected error, the call still resolves — with a
`status` describing what happened and `event_id` / `correlation_id` set to
`null`.

For failures you want to log or alert on, pass an `onError` callback. It fires
for auth rejections (`401`/`403` → `type: 'auth'`), network/timeout failures
(`type: 'network'`), and unexpected responses (`type: 'unknown'`). A throwing
`onError` callback is caught and ignored, so it can never crash your app either.

```typescript
const syntri = new Syntri({
  instanceId: 'my-app',
  apiKey: process.env.SYNTRI_API_KEY!,
  baseUrl: process.env.SYNTRI_BASE_URL!,
  timeout: 2000,
  onError: (err) => {
    console.warn(`[syntri] ${err.type}: ${err.message}`)
  },
})

// Safe to ignore the result — your code path continues regardless.
const res = await syntri.capture.input({ payload: { message } })
if (res.status !== 'captured') {
  // optional: degrade gracefully, retry later, etc.
}
```

## Types

The SDK exports the full server contract:

```typescript
import type {
  SyntriConfig,
  CaptureResponse,
  CaptureStatus,
  CaptureEvent,
  CaptureEventType,
  CaptureInputEvent,
  CaptureOutputEvent,
  CaptureOutcomeEvent,
  SyntriError,
} from 'syntri'
```

These mirror the Syntri server contract exactly. If the server contract
changes, the SDK types change to match.

## License

Proprietary.
