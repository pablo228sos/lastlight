import fixture from '../data/frontier.result.json'
import type { SimulationInput } from './contracts'

export interface FrontierCell {
  initial_soc: number
  duration_hours: number
  failed: boolean
  first_failure_hours: number | null
  physics_verified: true
  verification_run_id: string
}

export interface FrontierResult {
  schema_version: '1.0.0'
  physics_version: 'lastlight-dispatch-1.0.0'
  ml_model_version: null
  ml_status: 'not_requested' | 'incompatible_checkpoint'
  run_id: string
  input_hash: string
  seed: number
  provenance: { category: string; references: string[] }
  summary: { physics_calls: number; verified_cells: number; method: string }
  axes: { initial_soc: number[]; duration_hours: number[] }
  trace: FrontierCell[]
  ml_estimates: []
  warnings: string[]
}

const object = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value)

export function validateFrontier(value: unknown): FrontierResult {
  if (!object(value) || value.schema_version !== '1.0.0' || value.physics_version !== 'lastlight-dispatch-1.0.0' || value.ml_model_version !== null ||
    !['not_requested', 'incompatible_checkpoint'].includes(String(value.ml_status)) || !Array.isArray(value.ml_estimates) || value.ml_estimates.length !== 0) {
    throw new Error('Failure Frontier has incompatible physics or ML metadata.')
  }
  if (typeof value.run_id !== 'string' || !/^[0-9a-f]{64}$/.test(String(value.input_hash)) || !object(value.provenance) || value.provenance.category !== 'synthetic' ||
    !object(value.axes) || !Array.isArray(value.axes.initial_soc) || !Array.isArray(value.axes.duration_hours) || !object(value.summary) || !Array.isArray(value.trace)) {
    throw new Error('Failure Frontier is missing its calculation grid.')
  }
  const socs = value.axes.initial_soc as unknown[]
  const hours = value.axes.duration_hours as unknown[]
  if (socs.length < 3 || hours.length < 3 || value.trace.length !== socs.length * hours.length || value.summary.physics_calls !== socs.length || value.summary.verified_cells !== value.trace.length) {
    throw new Error('Failure Frontier grid dimensions do not match official trace calls.')
  }
  if (socs.some((soc, index) => typeof soc !== 'number' || !Number.isFinite(soc) || soc < 0 || soc > 1 || (index > 0 && soc <= (socs[index - 1] as number))) ||
    hours.some((hour, index) => typeof hour !== 'number' || !Number.isFinite(hour) || hour <= 0 || (index > 0 && hour <= (hours[index - 1] as number)))) {
    throw new Error('Failure Frontier axes are invalid.')
  }
  for (let index = 0; index < value.trace.length; index++) {
    const cell = value.trace[index]
    if (!object(cell) || cell.physics_verified !== true || typeof cell.verification_run_id !== 'string' || cell.verification_run_id.length === 0 || typeof cell.failed !== 'boolean' || typeof cell.duration_hours !== 'number' ||
      cell.initial_soc !== socs[Math.floor(index / hours.length)] || cell.duration_hours !== hours[index % hours.length] ||
      (cell.first_failure_hours !== null && (typeof cell.first_failure_hours !== 'number' || !Number.isFinite(cell.first_failure_hours))) ||
      (cell.failed && (cell.first_failure_hours === null || cell.duration_hours <= (cell.first_failure_hours as number))) ||
      (!cell.failed && cell.first_failure_hours !== null)) {
      throw new Error('Failure Frontier contains an unverified or inconsistent cell.')
    }
    if (index % hours.length > 0) {
      const previous = value.trace[index - 1] as Record<string, unknown>
      if (cell.verification_run_id !== previous.verification_run_id || (previous.failed === true && cell.failed !== true) ||
        (cell.first_failure_hours !== null && previous.first_failure_hours !== null && Math.abs((cell.first_failure_hours as number) - (previous.first_failure_hours as number)) > 1e-9)) {
        throw new Error('Failure Frontier cells do not follow one physical trace per charge level.')
      }
    }
  }
  return value as unknown as FrontierResult
}

export function verifiedFrontier() { return validateFrontier(fixture) }

export async function requestFrontier(scenario?: SimulationInput, signal?: AbortSignal): Promise<FrontierResult> {
  const base = (import.meta.env.VITE_PHYSICS_API_URL || '').replace(/\/$/, '')
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), 10_000)
  const cancel = () => controller.abort()
  if (signal?.aborted) controller.abort()
  signal?.addEventListener('abort', cancel, { once: true })
  try {
    const response = await fetch(`${base}/api/v1/frontiers`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, maximum_hours: Math.min(scenario?.duration_hours ?? 12, 48), soc_points: 13, duration_points: 21 }),
      signal: controller.signal,
    })
    if (!response.ok) throw new Error(`Failure Frontier API returned HTTP ${response.status}.`)
    return validateFrontier(await response.json() as unknown)
  } finally {
    window.clearTimeout(timeout)
    signal?.removeEventListener('abort', cancel)
  }
}
