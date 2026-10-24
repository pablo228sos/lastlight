/** Boundary for the future validated API schema. Phase 00 displays no numerical simulation output. */
export interface SimulationTracePoint {
  t_utc: string; grid_kw: number; solar_kw: number; battery_charge_kw: number
  battery_discharge_kw: number; battery_soc: number; critical_served_kw: number
  critical_demand_kw: number; noncritical_served_kw: number; unserved_critical_kw: number
  status: 'normal' | 'islanded' | 'degraded' | 'critical_failure'
}
export interface SimulationResult {
  run_id: string; model_version: string; input_hash: string; seed: number
  summary: { critical_survival_hours: number | null; served_critical_fraction: number
    unserved_critical_kwh: number; first_failure_utc: string | null; max_balance_residual_kwh: number }
  trace: SimulationTracePoint[]
  provenance: { category: 'measured' | 'research_derived' | 'synthetic'; references: string[] }
}
