// Mirrors services/simulation/schemas.py at physics commit 874840d.
// Numerical fields are read from the API or its generated fixtures only.
export interface Battery {
  capacity_kwh: number; initial_soc: number; minimum_soc: number; maximum_soc: number
  charge_efficiency: number; discharge_efficiency: number; max_charge_kw: number; max_discharge_kw: number
}
export interface Inverter { max_kw: number; islanding_capable: boolean }
export interface Load { critical_kw: number; noncritical_kw: number; shed_noncritical_during_outage: boolean }
export interface Solar { generation_kw: number; profile_kw: number[] | null; islanding_capable: boolean }
export interface Grid { online: boolean; profile_online: boolean[] | null; import_limit_kw: number; charge_battery: boolean }
export interface SimulationInput {
  start_utc: string; duration_hours: number; step_minutes: number; seed: number
  battery: Battery; inverter: Inverter; load: Load; solar: Solar; grid: Grid
  provenance: { category: 'measured' | 'research_derived' | 'synthetic'; references: string[] }
}
type DeepPartial<T> = T extends readonly unknown[] ? T : T extends object ? { [K in keyof T]?: DeepPartial<T[K]> } : T
export type SimulationRequest = DeepPartial<SimulationInput>

export interface SimulationTracePoint {
  t_utc: string; t_end_utc: string; elapsed_hours: number; duration_hours: number
  grid_online: boolean; grid_kw: number; grid_charge_kw: number
  solar_kw: number; solar_available_kw: number; solar_curtailed_kw: number
  battery_charge_kw: number; battery_discharge_kw: number
  battery_soc: number; battery_soc_end: number; battery_energy_kwh: number; battery_energy_end_kwh: number
  critical_served_kw: number; critical_demand_kw: number; unserved_critical_kw: number
  noncritical_served_kw: number; noncritical_demand_kw: number; unserved_noncritical_kw: number
  status: 'normal' | 'islanded' | 'degraded' | 'critical_failure'
  conversion_loss_kwh: number; ac_balance_residual_kwh: number
  storage_balance_residual_kwh: number; balance_residual_kwh: number
}
export interface SimulationSummary {
  critical_survival_hours: number | null; served_critical_fraction: number
  unserved_critical_kwh: number; first_failure_utc: string | null; max_balance_residual_kwh: number
  observed_duration_hours: number; survived_full_window: boolean; idealized_autonomy_hours: number | null
  total_critical_demand_kwh: number; served_critical_kwh: number; served_noncritical_kwh: number
  unserved_noncritical_kwh: number; grid_import_kwh: number; solar_available_kwh: number
  solar_used_kwh: number; solar_curtailed_kwh: number; battery_charge_kwh: number
  battery_discharge_kwh: number; conversion_loss_kwh: number; initial_battery_energy_kwh: number
  final_battery_energy_kwh: number; usable_capacity_kwh: number; ending_soc: number
  cumulative_balance_residual_kwh: number
}
export interface SimulationResult {
  run_id: string; model_version: string; schema_version: string; input_hash: string; seed: number
  input: SimulationInput; summary: SimulationSummary; trace: SimulationTracePoint[]
  provenance: SimulationInput['provenance']; warnings: string[]
}
export type ApprovedUpgrade = 'battery_36_kwh' | 'full_precharge'
export interface ComparisonRequest { baseline?: SimulationRequest; upgrade?: ApprovedUpgrade }
export interface ComparisonResult {
  schema_version: string; upgrade: ApprovedUpgrade
  baseline: SimulationResult; upgraded: SimulationResult
  delta: { served_critical_kwh: number; unserved_critical_kwh: number
    critical_survival_hours: number | null; idealized_autonomy_hours: number | null }
}
export interface ErrorResponse { error: { code: string; message: string
  details: { location: (string | number)[]; message: string; type: string }[] } }
