import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { Syntri } from '../src/index'
import type { SyntriError } from '../src/index'

const BASE_CONFIG = {
  instanceId: 'my-app',
  apiKey: 'test-key-123',
  baseUrl: 'https://api.syntri.test',
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

let fetchMock: ReturnType<typeof vi.fn>

beforeEach(() => {
  fetchMock = vi.fn()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe('CaptureClient', () => {
  test('input returns correlation_id', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        event_id: 'evt_1',
        status: 'captured',
        correlation_id: 'evt_1',
        latency_ms: 5,
      }),
    )
    const syntri = new Syntri(BASE_CONFIG)
    const res = await syntri.capture.input({ payload: { message: 'hi' } })

    expect(res.status).toBe('captured')
    expect(res.correlation_id).toBe('evt_1')
    expect(res.event_id).toBe('evt_1')

    // Verify the request body carried the input event shape.
    const [, init] = fetchMock.mock.calls[0]
    const sent = JSON.parse(init.body as string)
    expect(sent.instance_id).toBe('my-app')
    expect(sent.event_type).toBe('input')
    expect(sent.payload).toEqual({ message: 'hi' })
  })

  test('output sends correlation_id', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ event_id: 'evt_2', status: 'captured', correlation_id: 'evt_1', latency_ms: 3 }),
    )
    const syntri = new Syntri(BASE_CONFIG)
    await syntri.capture.output({ correlationId: 'evt_1', payload: { response: 'ok' } })

    const [, init] = fetchMock.mock.calls[0]
    const sent = JSON.parse(init.body as string)
    expect(sent.event_type).toBe('output')
    expect(sent.correlation_id).toBe('evt_1')
    expect(sent.payload).toEqual({ response: 'ok' })
  })

  test('outcome sends correlation_id', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ event_id: 'evt_3', status: 'captured', correlation_id: 'evt_1', latency_ms: 4 }),
    )
    const syntri = new Syntri(BASE_CONFIG)
    await syntri.capture.outcome({ correlationId: 'evt_1', payload: { satisfied: true } })

    const [, init] = fetchMock.mock.calls[0]
    const sent = JSON.parse(init.body as string)
    expect(sent.event_type).toBe('outcome')
    expect(sent.correlation_id).toBe('evt_1')
    expect(sent.payload).toEqual({ satisfied: true })
  })

  test('timeout returns unreachable without throwing', async () => {
    // Simulate the AbortController firing: fetch rejects with an AbortError.
    fetchMock.mockImplementationOnce((_url: string, init: RequestInit) => {
      return new Promise((_resolve, reject) => {
        const signal = init.signal as AbortSignal
        signal.addEventListener('abort', () => {
          const err = new Error('The operation was aborted')
          err.name = 'AbortError'
          reject(err)
        })
      })
    })
    const syntri = new Syntri({ ...BASE_CONFIG, timeout: 20 })
    const res = await syntri.capture.input({ payload: { message: 'hi' } })

    expect(res.status).toBe('unreachable')
    expect(res.event_id).toBeNull()
    expect(res.correlation_id).toBeNull()
    expect(typeof res.latency_ms).toBe('number')
  })

  test('network error returns unreachable without throwing', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('fetch failed'))
    const syntri = new Syntri(BASE_CONFIG)
    const res = await syntri.capture.input({ payload: { message: 'hi' } })

    expect(res.status).toBe('unreachable')
    expect(res.event_id).toBeNull()
    expect(res.correlation_id).toBeNull()
  })

  test('401 calls onError without throwing', async () => {
    fetchMock.mockResolvedValueOnce(new Response('unauthorized', { status: 401 }))
    const errors: SyntriError[] = []
    const syntri = new Syntri({ ...BASE_CONFIG, onError: (e) => errors.push(e) })
    const res = await syntri.capture.input({ payload: { message: 'hi' } })

    expect(res.status).toBe('unreachable')
    expect(errors).toHaveLength(1)
    expect(errors[0].type).toBe('auth')
    expect(errors[0].status).toBe(401)
  })

  test('unexpected non-2xx returns unknown_error and calls onError', async () => {
    fetchMock.mockResolvedValueOnce(new Response('boom', { status: 500 }))
    const errors: SyntriError[] = []
    const syntri = new Syntri({ ...BASE_CONFIG, onError: (e) => errors.push(e) })
    const res = await syntri.capture.input({ payload: {} })

    expect(res.status).toBe('unknown_error')
    expect(errors[0].type).toBe('unknown')
    expect(errors[0].status).toBe(500)
  })

  test('sends correct auth header', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ event_id: 'e', status: 'captured', correlation_id: 'e', latency_ms: 1 }),
    )
    const syntri = new Syntri(BASE_CONFIG)
    await syntri.capture.input({ payload: {} })

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('https://api.syntri.test/v1/capture')
    expect(init.method).toBe('POST')
    const headers = init.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer test-key-123')
    expect(headers['Content-Type']).toBe('application/json')
  })

  test('latency_ms is populated', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ event_id: 'e', status: 'captured', correlation_id: 'e', latency_ms: 42 }),
    )
    const syntri = new Syntri(BASE_CONFIG)
    const res = await syntri.capture.input({ payload: {} })

    expect(typeof res.latency_ms).toBe('number')
    expect(res.latency_ms).toBeGreaterThanOrEqual(0)
  })

  test('passes sessionId and metadata through when provided', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({ event_id: 'e', status: 'captured', correlation_id: 'e', latency_ms: 1 }),
    )
    const syntri = new Syntri(BASE_CONFIG)
    await syntri.capture.input({
      payload: { a: 1 },
      sessionId: 'sess-1',
      metadata: { source: 'web' },
    })

    const [, init] = fetchMock.mock.calls[0]
    const sent = JSON.parse(init.body as string)
    expect(sent.session_id).toBe('sess-1')
    expect(sent.metadata).toEqual({ source: 'web' })
  })
})
