import type { SimulationResult } from './contracts'

export interface DesignCandidate {
  capacity_kwh: number
  valid: true
  survived_target: boolean
  first_critical_failure_hours: number | null
  first_critical_failure_utc: string | null
  unserved_critical_kwh: number
  ending_soc: number
  infeasibility_reasons: string[]
  physics_run_id: string
  physics_input_hash: string
  comparable_cost: null
}

export interface DesignSearchResult {
  schema_version: '1.0.0'
  physics_model_version: 'lastlight-dispatch-1.0.0'
  run_id: string
  input_hash: string
  result_hash: string
  seed: number
  outage_target_hours: number
  provenance: SimulationResult['provenance']
  candidate_count: number
  selected_capacity_kwh: number | null
  selection_rule: string
  physics_verified: true
  candidates: DesignCandidate[]
  warnings: string[]
}

export const candidateCapacities = [24, 30, 32, 36] as const
const object = (value: unknown): value is Record<string, unknown> => value !== null && typeof value === 'object' && !Array.isArray(value)
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const digest = (value: unknown) => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value)

export function validateDesignSearch(value: unknown, baseline: SimulationResult): DesignSearchResult {
  if (!object(value) || value.schema_version !== '1.0.0' || value.physics_model_version !== baseline.model_version || value.physics_verified !== true ||
    !digest(value.input_hash) || !digest(value.result_hash) || typeof value.run_id !== 'string' || !object(value.provenance) || value.provenance.category !== 'synthetic' ||
    value.outage_target_hours !== baseline.input.duration_hours || value.seed !== baseline.seed || !Array.isArray(value.candidates) ||
    value.candidate_count !== candidateCapacities.length || value.candidates.length !== candidateCapacities.length ||
    value.selection_rule !== 'smallest passing capacity within the explicit supplied set' || !Array.isArray(value.warnings)) {
    throw new Error('Design search response does not match the official scenario and v1 contract.')
  }
  let selected: number | null = null
  for (const [index, candidate] of value.candidates.entries()) {
    if (!object(candidate) || candidate.capacity_kwh !== candidateCapacities[index] || candidate.valid !== true || typeof candidate.survived_target !== 'boolean' ||
      !finite(candidate.unserved_critical_kwh) || candidate.unserved_critical_kwh < 0 || !finite(candidate.ending_soc) || candidate.ending_soc < 0 || candidate.ending_soc > 1 ||
      typeof candidate.physics_run_id !== 'string' || !digest(candidate.physics_input_hash) || !Array.isArray(candidate.infeasibility_reasons) ||
      candidate.infeasibility_reasons.some(reason => typeof reason !== 'string') || candidate.comparable_cost !== null) {
      throw new Error('Design search has an invalid physical candidate.')
    }
    if (candidate.survived_target) {
      if (candidate.first_critical_failure_hours !== null || candidate.first_critical_failure_utc !== null || candidate.unserved_critical_kwh > 1e-9 || candidate.infeasibility_reasons.length > 0) {
        throw new Error('Design search pass conflicts with an observed deficit.')
      }
      selected ??= candidate.capacity_kwh as number
    } else if (!finite(candidate.first_critical_failure_hours) || candidate.first_critical_failure_hours < 0 || candidate.first_critical_failure_hours >= baseline.input.duration_hours || typeof candidate.first_critical_failure_utc !== 'string' || candidate.unserved_critical_kwh <= 0) {
      throw new Error('Design search failure lacks an observed in-window deficit.')
    }
    if (candidate.capacity_kwh === baseline.input.battery.capacity_kwh && candidate.physics_input_hash !== baseline.input_hash) {
      throw new Error('Design search baseline input differs from the active simulation.')
    }
  }
  if (value.selected_capacity_kwh !== selected) throw new Error('Design search selected a candidate outside the smallest passing tested capacity.')
  return value as unknown as DesignSearchResult
}

export async function requestDesignSearch(baseline: SimulationResult, signal: AbortSignal): Promise<DesignSearchResult> {
  const base = (import.meta.env.VITE_PHYSICS_API_URL || '').replace(/\/$/, '')
  const response = await fetch(`${base}/api/v1/design-search`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, signal,
    body: JSON.stringify({ scenario: baseline.input, outage_target_hours: baseline.input.duration_hours, candidate_capacities_kwh: candidateCapacities }),
  })
  if (!response.ok) throw new Error(`Design search API returned HTTP ${response.status}.`)
  return validateDesignSearch(await response.json() as unknown, baseline)
}
