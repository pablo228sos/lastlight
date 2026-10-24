import baselineFixture from '../data/baseline.result.json'
import comparisonFixture from '../data/comparison.result.json'
import type { ComparisonRequest, SimulationRequest } from './contracts'
import { validateComparison, validateSimulation } from './physics'

const baseUrl = (import.meta.env.VITE_PHYSICS_API_URL || '').replace(/\/$/, '')
const endpoint = (path: string) => `${baseUrl}${path}`

async function post(path: string, body: SimulationRequest | ComparisonRequest, signal?: AbortSignal): Promise<unknown> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 10_000)
  const cancel = () => controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  try {
    const response = await fetch(endpoint(path), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: controller.signal })
    if (!response.ok) throw new Error(`Physics API returned HTTP ${response.status}.`)
    return await response.json() as unknown
  } catch (error) {
    if (controller.signal.aborted && !signal?.aborted) throw new Error('Physics API did not respond within 10 seconds.')
    throw error
  } finally {
    window.clearTimeout(timeout)
    signal?.removeEventListener('abort', cancel)
  }
}

export async function requestBaseline(signal?: AbortSignal) {
  return validateSimulation(await post('/api/v1/simulations', {}, signal))
}
export async function requestComparison(signal?: AbortSignal) {
  return validateComparison(await post('/api/v1/comparisons', { upgrade: 'battery_36_kwh' }, signal))
}
export function verifiedBaseline() { return validateSimulation(baselineFixture) }
export function verifiedComparison() { return validateComparison(comparisonFixture) }
