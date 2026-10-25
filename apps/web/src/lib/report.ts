import type { ComparisonResult, SimulationResult } from './contracts'
import type { PhysicsSource } from '../app/usePhysicsRun'

export interface ReportSelection {
  source: PhysicsSource
  baseline: SimulationResult
  comparison: ComparisonResult | null
  selectedRun: 'baseline' | 'upgraded'
}

export function createEvidenceReport({ source, baseline, comparison, selectedRun }: ReportSelection) {
  const selected = selectedRun === 'upgraded' && comparison ? comparison.upgraded : baseline
  return {
    document_version: '1.0.0',
    title: 'LASTLIGHT school outage evidence report',
    exported_utc: new Date().toISOString(),
    site: {
      name: 'School',
      geometry: 'Illustrative Bishkek-inspired model, not surveyed infrastructure',
      input_category: selected.provenance.category,
      data_label: 'Synthetic scenario; no measured site meters or live utility data',
    },
    physics_source: source === 'live' ? 'Live local Physics API' : 'Verified engine-generated offline replay',
    selected_run: selectedRun,
    selected_run_id: selected.run_id,
    selected_input_hash: selected.input_hash,
    model_version: selected.model_version,
    schema_version: selected.schema_version,
    provenance: selected.provenance,
    scenario_input: selected.input,
    assumptions: {
      battery: selected.input.battery,
      load: selected.input.load,
      solar: selected.input.solar,
      inverter: selected.input.inverter,
      grid: selected.input.grid,
      outage_duration_hours: selected.input.duration_hours,
    },
    result: {
      first_unmet_critical_demand_utc: selected.summary.first_failure_utc,
      observed_critical_survival_hours: selected.summary.critical_survival_hours,
      survived_full_window: selected.summary.survived_full_window,
      unserved_critical_kwh: selected.summary.unserved_critical_kwh,
      ending_soc: selected.summary.ending_soc,
      summary: selected.summary,
      trace: selected.trace,
    },
    selected_improvement: comparison?.upgrade ?? null,
    comparison: comparison ? {
      upgrade: comparison.upgrade,
      delta: comparison.delta,
      baseline: { run_id: comparison.baseline.run_id, input_hash: comparison.baseline.input_hash, input: comparison.baseline.input, summary: comparison.baseline.summary },
      upgraded: { run_id: comparison.upgraded.run_id, input_hash: comparison.upgraded.input_hash, input: comparison.upgraded.input, summary: comparison.upgraded.summary },
    } : null,
    warnings: selected.warnings,
    limitations: [
      'This report uses a synthetic school archetype and illustrative geometry.',
      'No measured meter, telemetry, weather feed, surveyed utility topology or equipment quotation is connected.',
      'An observed failure must occur before the exclusive end of the simulation horizon; no observed failure does not establish indefinite autonomy.',
      source === 'offline' ? 'The replay is an archived calculation, not a new live API run.' : 'The local API calculation is deterministic for the resolved input and model version.',
    ],
  }
}

export function downloadEvidenceReport(selection: ReportSelection) {
  const report = createEvidenceReport(selection)
  const blob = new Blob([JSON.stringify(report, null, 2) + '\n'], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `lastlight-school-${report.selected_input_hash.slice(0, 12)}.json`
  document.body.append(link)
  link.click()
  link.remove()
  window.setTimeout(() => URL.revokeObjectURL(url), 0)
}
