import type {
  CaptureEvent,
  CaptureResponse,
  CaptureStatus,
  SyntriConfig,
  SyntriError,
} from './types'

const DEFAULT_TIMEOUT_MS = 2000

/**
 * CaptureClient wraps POST /v1/capture. Every method resolves — it never
 * throws. If Syntri is slow, unreachable, or misbehaving, the caller's app
 * keeps running; the failure surfaces as a status on the returned
 * CaptureResponse and, where configured, through config.onError.
 */
export class CaptureClient {
  constructor(private config: SyntriConfig) {}

  /** Capture an input event. The returned correlation_id links later output/outcome events. */
  async input(options: {
    payload: Record<string, unknown>
    sessionId?: string
    metadata?: Record<string, unknown>
  }): Promise<CaptureResponse> {
    return this.send({
      instance_id: this.config.instanceId,
      event_type: 'input',
      payload: options.payload,
      ...(options.sessionId !== undefined ? { session_id: options.sessionId } : {}),
      ...(options.metadata !== undefined ? { metadata: options.metadata } : {}),
    })
  }

  /** Capture an output event, correlated to a prior input event. */
  async output(options: {
    correlationId: string
    payload: Record<string, unknown>
    sessionId?: string
    metadata?: Record<string, unknown>
  }): Promise<CaptureResponse> {
    return this.send({
      instance_id: this.config.instanceId,
      event_type: 'output',
      payload: options.payload,
      correlation_id: options.correlationId,
      ...(options.sessionId !== undefined ? { session_id: options.sessionId } : {}),
      ...(options.metadata !== undefined ? { metadata: options.metadata } : {}),
    })
  }

  /** Capture an outcome event, correlated to a prior input event. */
  async outcome(options: {
    correlationId: string
    payload: Record<string, unknown>
    sessionId?: string
    metadata?: Record<string, unknown>
  }): Promise<CaptureResponse> {
    return this.send({
      instance_id: this.config.instanceId,
      event_type: 'outcome',
      payload: options.payload,
      correlation_id: options.correlationId,
      ...(options.sessionId !== undefined ? { session_id: options.sessionId } : {}),
      ...(options.metadata !== undefined ? { metadata: options.metadata } : {}),
    })
  }

  private notifyError(error: SyntriError): void {
    if (this.config.onError) {
      try {
        this.config.onError(error)
      } catch {
        // A throwing onError callback must never break the caller. Swallow it.
      }
    }
  }

  private unreachable(latency_ms: number): CaptureResponse {
    return { event_id: null, status: 'unreachable', correlation_id: null, latency_ms }
  }

  private synthesized(status: CaptureStatus, latency_ms: number): CaptureResponse {
    return { event_id: null, status, correlation_id: null, latency_ms }
  }

  private async send(event: CaptureEvent): Promise<CaptureResponse> {
    const timeout = this.config.timeout ?? DEFAULT_TIMEOUT_MS
    const start = now()
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeout)

    let response: Response
    try {
      response = await fetch(joinUrl(this.config.baseUrl, '/v1/capture'), {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.config.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(event),
        signal: controller.signal,
      })
    } catch (err) {
      // Timeout (AbortError) or a transport-level network failure. Either way,
      // Syntri never answered — report unreachable, never throw.
      const elapsed = now() - start
      const aborted = err instanceof Error && err.name === 'AbortError'
      this.notifyError({
        type: 'network',
        message: aborted
          ? `Request to Syntri timed out after ${timeout}ms`
          : `Network error contacting Syntri: ${errMessage(err)}`,
      })
      return this.unreachable(elapsed)
    } finally {
      clearTimeout(timer)
    }

    const elapsed = now() - start

    if (response.status === 401 || response.status === 403) {
      this.notifyError({
        type: 'auth',
        message: `Syntri rejected the API key (HTTP ${response.status})`,
        status: response.status,
      })
      return this.unreachable(elapsed)
    }

    if (!response.ok) {
      this.notifyError({
        type: 'unknown',
        message: `Unexpected response from Syntri (HTTP ${response.status})`,
        status: response.status,
      })
      return this.synthesized('unknown_error', elapsed)
    }

    // 2xx: trust the server's decision fields, but report SDK-measured
    // round-trip latency for consistency across success and failure paths.
    try {
      const body = (await response.json()) as Partial<CaptureResponse>
      return {
        event_id: body.event_id ?? null,
        status: body.status ?? 'captured',
        correlation_id: body.correlation_id ?? null,
        latency_ms: elapsed,
      }
    } catch (err) {
      this.notifyError({
        type: 'unknown',
        message: `Could not parse Syntri response body: ${errMessage(err)}`,
        status: response.status,
      })
      return this.synthesized('unknown_error', elapsed)
    }
  }
}

function now(): number {
  return typeof performance !== 'undefined' && typeof performance.now === 'function'
    ? performance.now()
    : Date.now()
}

function errMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

function joinUrl(base: string, path: string): string {
  return `${base.replace(/\/+$/, '')}${path}`
}
