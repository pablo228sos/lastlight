import type { Assessment as WireAssessment, CandidateResult } from './intelligenceContracts'
import type { SimulationInput, SimulationResult } from './contracts'
import type { FrontierResult } from './failureFrontier'
import { validateSimulation } from './physics'

export type Assessment = Omit<WireAssessment, 'physics'> & { physics: SimulationResult }
export type { CandidateResult }
const base = (import.meta.env.VITE_PHYSICS_API_URL || '').replace(/\/$/, '')

export async function intelligenceRequest<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), 30_000)
  const cancel = () => controller.abort()
  if (signal?.aborted) controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  try {
    const response = await fetch(`${base}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: controller.signal })
    if (!response.ok) throw new Error(`Intelligence API returned HTTP ${response.status}. Physical analysis remains available.`)
    return await response.json() as T
  } catch (error) {
    if (controller.signal.aborted && !signal?.aborted) throw new Error('Analysis timed out after 30 seconds. Physical analysis remains available.')
    throw error
  } finally { window.clearTimeout(timer); signal?.removeEventListener('abort', cancel) }
}

export async function requestAssessment(active: SimulationResult, signal?: AbortSignal) {
  const value = await intelligenceRequest<WireAssessment>('/api/v1/ml/fragility/assess', { scenario: active.input }, signal)
  const physics = validateSimulation(value.physics)
  if (value.physics.input_hash !== active.input_hash || value.physics_authoritative !== true || value.engineering_clearance !== false || value.bridge_schema_version !== 'lastlight-ml-bridge-1') throw new Error('AI assessment does not match the active official scenario.')
  const neural = value.neural
  if (!neural || !['available', 'unavailable', 'incompatible_checkpoint'].includes(neural.status) || !Array.isArray(neural.warnings)) throw new Error('Invalid neural availability contract.')
  if (neural.status === 'available') {
    const estimate = neural.estimate
    if (!neural.model_version || neural.source_physics_version !== active.model_version || !estimate || typeof estimate.predicted_failure !== 'boolean' || !Number.isFinite(estimate.synthetic_failure_score) || estimate.synthetic_failure_score < 0 || estimate.synthetic_failure_score > 1 || estimate.engineering_clearance !== false || estimate.physics_required !== true) throw new Error('Invalid neural estimate identity or score.')
  }
  return { ...value, physics }
}

export async function requestCandidates(scenario: SimulationInput, frontier: FrontierResult, signal?: AbortSignal) {
  const points = frontier.trace.map(({ initial_soc, duration_hours }) => ({ initial_soc, duration_hours }))
  const value = await intelligenceRequest<CandidateResult>('/api/v1/ml/fragility/candidates', { scenario, points, limit: 12 }, signal)
  if (value.physics_version !== 'lastlight-dispatch-1.0.0' || value.schema_version !== '1.0.0' || !Array.isArray(value.candidates) || value.candidates.length > 12 || !Array.isArray(value.warnings)) throw new Error('Incompatible candidate response.')
  const seen = new Set<string>()
  for (const cell of value.candidates) {
    const physical = frontier.trace.find(point => point.initial_soc === cell.initial_soc && point.duration_hours === cell.duration_hours)
    const key = `${cell.initial_soc}:${cell.duration_hours}`
    if (seen.has(key) || !physical || cell.physics_verified !== true || cell.physics_model_version !== value.physics_version || !cell.physics_run_id || !/^[0-9a-f]{64}$/.test(cell.input_hash) || cell.physics_summary.survived_full_window !== !physical.failed || cell.physics_summary.observed_duration_hours !== cell.duration_hours || !Number.isFinite(cell.neural.synthetic_failure_score)) throw new Error('Candidate is not independently consistent with the official map.')
    seen.add(key)
  }
  return value
}
