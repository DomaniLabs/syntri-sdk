import { CaptureClient } from './capture'
import type { SyntriConfig } from './types'

/**
 * Syntri client. Construct once with your instance id, API key and base URL,
 * then use `.capture` to record input, output and outcome events.
 *
 * The SDK never throws: capture calls always resolve to a CaptureResponse so a
 * Syntri failure can never crash your app.
 */
export class Syntri {
  public readonly capture: CaptureClient

  constructor(config: SyntriConfig) {
    this.capture = new CaptureClient(config)
  }
}

export { CaptureClient }

export type {
  SyntriConfig,
  CaptureResponse,
  CaptureStatus,
  CaptureEvent,
  CaptureEventType,
  CaptureInputEvent,
  CaptureOutputEvent,
  CaptureOutcomeEvent,
  SyntriError,
} from './types'
