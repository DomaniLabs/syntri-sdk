// These types mirror the Syntri server contract for POST /v1/capture.
// If the server contract changes, these types must change to match.

export type CaptureEventType = 'input' | 'output' | 'outcome'

export interface CaptureInputEvent {
  instance_id: string
  event_type: 'input'
  payload: Record<string, unknown>
  session_id?: string
  metadata?: Record<string, unknown>
  timestamp?: string // ISO 8601, server fills if absent
}

export interface CaptureOutputEvent {
  instance_id: string
  event_type: 'output'
  payload: Record<string, unknown>
  correlation_id: string // required — links to input event_id
  session_id?: string
  metadata?: Record<string, unknown>
  timestamp?: string
}

export interface CaptureOutcomeEvent {
  instance_id: string
  event_type: 'outcome'
  payload: Record<string, unknown>
  correlation_id: string // required — links to input event_id
  session_id?: string
  metadata?: Record<string, unknown>
  timestamp?: string
}

export type CaptureEvent =
  | CaptureInputEvent
  | CaptureOutputEvent
  | CaptureOutcomeEvent

// Statuses returned by the server contract: 'captured' | 'write_failed' |
// 'unprocessable'. The SDK additionally synthesizes transport-level outcomes
// the server never had a chance to report:
//   'unreachable'   — timeout, network error, or auth rejection (401/403)
//   'unknown_error' — an unexpected non-2xx response
// The SDK never throws, so every call resolves to one of these statuses.
export type CaptureStatus =
  | 'captured'
  | 'write_failed'
  | 'unprocessable'
  | 'unreachable'
  | 'unknown_error'

export interface CaptureResponse {
  event_id: string | null
  status: CaptureStatus
  correlation_id: string | null
  latency_ms: number
}

export interface SyntriConfig {
  instanceId: string
  apiKey: string
  baseUrl: string
  timeout?: number // ms, default 2000
  onError?: (error: SyntriError) => void
}

export interface SyntriError {
  type: 'network' | 'auth' | 'unprocessable' | 'write_failed' | 'unknown'
  message: string
  status?: number
}
