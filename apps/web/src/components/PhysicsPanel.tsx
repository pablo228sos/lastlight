import type { FrontierResult, SimulationResult } from '../lib/contracts'
import './physics.css'

type Props = { result: SimulationResult; index: number; onIndex: (index: number) => void;
  frontier: FrontierResult | null; frontierBusy: boolean; onFrontier: (includeMl?: boolean) => void }

export function PhysicsPanel({ result, index, onIndex, frontier, frontierBusy, onFrontier }: Props) {
  const point = result.trace[index]
  const failure = result.trace.findIndex(item => item.status === 'critical_failure')
  return <aside className="physics-panel" data-testid="physics-panel" aria-label="Calculated school scenario">
    <p className="physics-kicker">PHYSICS / SYNTHETIC SCHOOL INPUTS</p>
    <div className="physics-metrics">
      <span>BATTERY SOC<strong data-testid="battery-soc">{(point.battery_soc * 100).toFixed(1)}%</strong></span>
      <span>FIRST FAILURE<strong data-testid="first-failure">{result.summary.critical_survival_hours === null ? 'NOT OBSERVED' : `${result.summary.critical_survival_hours.toFixed(2)} h`}</strong></span>
      <span>CRITICAL SERVED<strong>{point.critical_served_kw.toFixed(2)} / {point.critical_demand_kw.toFixed(2)} kW</strong></span>
      <span>UNSERVED / FULL RUN<strong>{result.summary.unserved_critical_kwh.toFixed(2)} kWh</strong></span>
    </div>
    <p className="physics-status" role="status" data-testid="critical-status">{point.unserved_critical_kw > 1e-9 ? 'CRITICAL LOAD UNSERVED' : 'CRITICAL LOAD SERVED'} · {point.elapsed_hours.toFixed(2)} h</p>
    <label className="physics-timeline">OUTAGE TRACE <input aria-label="Outage trace position" type="range" min={0} max={result.trace.length - 1} value={index} onChange={event => onIndex(Number(event.target.value))} /></label>
    <div className="physics-actions">
      {failure >= 0 && <button data-testid="jump-failure" onClick={() => onIndex(failure)}>FIRST FAILURE ↗</button>}
      <button data-testid="show-frontier" onClick={() => onFrontier()} disabled={frontierBusy}>{frontierBusy ? 'CALCULATING…' : 'FAILURE FRONTIER ↗'}</button>
    </div>
    {frontier && <figure className="frontier" data-testid="frontier-map">
      <figcaption>PHYSICS VERIFIED · SOC × OUTAGE HOURS</figcaption>
      <svg viewBox="0 0 280 140" role="img" aria-label="Failure frontier: orange cells fail; pale cells survive the inspected horizon">
        {frontier.trace.map((cell, i) => <rect key={i} x={20 + cell.initial_soc * 230} y={120 - cell.duration_hours / 24 * 110} width={15} height={6}
          fill={cell.failed ? '#e6a45e' : '#9ddbd0'}><title>{(cell.initial_soc * 100).toFixed(0)}% SOC, {cell.duration_hours.toFixed(1)} hours: {cell.failed ? 'critical failure' : 'survives this horizon'}</title></rect>)}
        {frontier.verified_candidates.map((cell, i) => <circle key={'ml-' + i} cx={27 + cell.initial_soc * 230} cy={123 - cell.duration_hours / 24 * 110} r={4} fill="none" stroke="#f2f0e9"><title>ML proposal, physics checked: {cell.failed ? 'failure' : 'horizon survived'}{cell.outside_training_domain ? '; outside training bounds' : ''}</title></circle>)}
        <text x="20" y="136">0% SOC</text><text x="220" y="136">100%</text><text x="0" y="12">24h</text>
      </svg>
      <p>Orange: failure · Pale: horizon survived. ML proposals are separate; every displayed cell is physics verified.</p>
      {frontier.model_version ? <p data-testid="verified-ml">{frontier.verified_candidates.length} ML proposals checked by physics. Circles mark verified proposals; the model grants no engineering clearance.</p> : <button data-testid="verify-ml" onClick={() => onFrontier(true)} disabled={frontierBusy}>{frontierBusy ? 'LOADING MODEL…' : 'VERIFY ML PROPOSALS ↗'}</button>}
      {frontier.warnings.map((message, i) => <p key={i}>{message}</p>)}
    </figure>}
    <details><summary>MODEL &amp; PROVENANCE</summary><p>{result.physics_version} · {result.provenance.category}</p><p>Run {result.run_id}</p><p>Balance residual: {result.summary.max_balance_residual_kwh.toExponential(2)} kWh</p><p>Single-bus energy model; no AC transients or field certification.</p></details>
  </aside>
}
