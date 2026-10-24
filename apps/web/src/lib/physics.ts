import type { ComparisonResult, SimulationResult, SimulationTracePoint } from './contracts'

const object = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value)
const number = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const utc = (value: unknown): value is string => typeof value === 'string' && Number.isFinite(Date.parse(value))

export function validateSimulation(value: unknown): SimulationResult {
  if (!object(value) || !Array.isArray(value.trace) || !object(value.summary) || !object(value.input) || !object(value.provenance)) throw new Error('Physics response has no complete simulation trace.')
  if (typeof value.run_id !== 'string' || typeof value.model_version !== 'string' || typeof value.input_hash !== 'string' || typeof value.schema_version !== 'string') throw new Error('Physics response is missing its model identity.')
  const input = value.input
  const summary = value.summary
  if (!utc(input.start_utc) || !number(input.duration_hours) || input.duration_hours <= 0 || !object(input.battery) || !object(input.load)) throw new Error('Physics response has invalid resolved inputs.')
  if (!number(input.battery.capacity_kwh) || !number(input.load.critical_kw)) throw new Error('Physics response has invalid equipment inputs.')
  if (!number(summary.observed_duration_hours) || !number(summary.max_balance_residual_kwh) || summary.max_balance_residual_kwh > 1e-8 || !('first_failure_utc' in summary)) throw new Error('Physics response failed its energy or summary checks.')
  if (value.trace.length === 0) throw new Error('Physics response has an empty trace.')
  const start = Date.parse(input.start_utc)
  let previousEnd = start
  let firstFailure: string | null = null
  for (const row of value.trace) {
    if (!object(row) || !utc(row.t_utc) || !utc(row.t_end_utc) || !number(row.duration_hours) || !number(row.elapsed_hours)) throw new Error('Physics trace has invalid interval boundaries.')
    const rowStart = Date.parse(row.t_utc)
    const rowEnd = Date.parse(row.t_end_utc)
    if (Math.abs(rowStart - previousEnd) > 1 || rowEnd <= rowStart || Math.abs((rowEnd - rowStart) / 3_600_000 - row.duration_hours) > 1e-6) throw new Error('Physics trace intervals are not continuous.')
    for (const key of ['battery_soc', 'battery_soc_end', 'grid_kw', 'solar_kw', 'battery_charge_kw', 'battery_discharge_kw', 'critical_served_kw', 'critical_demand_kw', 'noncritical_served_kw', 'unserved_critical_kw', 'balance_residual_kwh']) {
      if (!number(row[key])) throw new Error(`Physics trace is missing ${key}.`)
    }
    if ((row.battery_soc as number) < -1e-8 || (row.battery_soc as number) > 1 + 1e-8 || (row.battery_soc_end as number) < -1e-8 || (row.battery_soc_end as number) > 1 + 1e-8 || Math.abs(row.balance_residual_kwh as number) > 1e-8) throw new Error('Physics trace failed its bounds or energy checks.')
    if (typeof row.grid_online !== 'boolean' || typeof row.status !== 'string') throw new Error('Physics trace has invalid grid or status fields.')
    if ((row.unserved_critical_kw as number) > 1e-9 && firstFailure === null) firstFailure = row.t_utc
    previousEnd = rowEnd
  }
  if (Math.abs((previousEnd - start) / 3_600_000 - input.duration_hours) > 1e-6) throw new Error('Physics trace does not cover the requested horizon.')
  if (summary.first_failure_utc !== firstFailure) throw new Error('Physics failure summary disagrees with the trace.')
  if (firstFailure === null && summary.critical_survival_hours !== null) throw new Error('Physics survival summary disagrees with the trace.')
  if (firstFailure !== null && (!number(summary.critical_survival_hours) || Math.abs(summary.critical_survival_hours - (Date.parse(firstFailure) - start) / 3_600_000) > 1e-6)) throw new Error('Physics failure time disagrees with the trace.')
  return value as unknown as SimulationResult
}

export function validateComparison(value: unknown): ComparisonResult {
  if (!object(value) || value.upgrade !== 'battery_36_kwh' || !object(value.delta)) throw new Error('Physics comparison has an unsupported upgrade.')
  const baseline = validateSimulation(value.baseline)
  const upgraded = validateSimulation(value.upgraded)
  if (upgraded.input.battery.capacity_kwh !== 36 || baseline.input.battery.capacity_kwh !== 24) throw new Error('Physics comparison has unexpected battery capacities.')
  return value as unknown as ComparisonResult
}

export function traceInterval(result: SimulationResult, elapsedHours: number): { row: SimulationTracePoint; soc: number; index: number } {
  const start = Date.parse(result.input.start_utc)
  const time = start + Math.max(0, Math.min(elapsedHours, result.input.duration_hours)) * 3_600_000
  const trace = result.trace
  let lo = 0, hi = trace.length - 1
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2)
    if (time < Date.parse(trace[mid].t_end_utc)) hi = mid
    else lo = mid + 1
  }
  const row = trace[lo]
  const begin = Date.parse(row.t_utc), end = Date.parse(row.t_end_utc)
  const fraction = Math.max(0, Math.min(1, (time - begin) / (end - begin)))
  return { row, soc: row.battery_soc + (row.battery_soc_end - row.battery_soc) * fraction, index: lo }
}

export function failureHours(result: SimulationResult): number | null {
  return result.summary.first_failure_utc === null ? null : (Date.parse(result.summary.first_failure_utc) - Date.parse(result.input.start_utc)) / 3_600_000
}
