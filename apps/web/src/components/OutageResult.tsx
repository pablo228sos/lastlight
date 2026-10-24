import type { PhysicsPanelProps } from './PhysicsPanel'
import { horizon, hours, number, percent } from './analysisFormat'

export function OutageResult({ result, index, onIndex }: PhysicsPanelProps) {
  const duration = horizon(result)
  const failureTime = result.summary.critical_survival_hours
  const failed = !result.summary.survived_full_window
  const point = result.trace[index]
  const failureIndex = result.trace.findIndex(item => item.status === 'critical_failure')
  const loads = result.input.load?.critical_profile_kw
  const demand = loads ? `${number(Math.min(...loads))}–${number(Math.max(...loads))} kW profile` : result.input.load?.critical_kw !== undefined ? `${number(result.input.load.critical_kw)} kW` : 'See returned trace'
  return <section className="outage-result" aria-label="Physical blackout result">
    <div className="verdict-layout">
      <div className={'verdict-main ' + (failed ? 'is-failure' : 'is-survival')}>
        <p className="verdict-question">Can this school survive a {number(duration)}-hour blackout?</p>
        <div className="verdict-answer"><strong>{failed ? 'NO' : 'YES'}</strong><span>{failed ? 'Critical power first fails after' : 'Critical power maintained for'}<b>{hours(failureTime ?? duration)}</b></span></div>
        <p className="verdict-detail" data-testid="outage-verdict">{failureTime !== null ? <><strong>{hours(Math.max(0, duration - failureTime))} remain in the outage at the first loss of critical power.</strong> This is the first failure; supply can recover later if generation or the grid returns.</> : <>No critical failure is observed in this window. Survival beyond {hours(duration)} has not been established.</>}</p>
      </div>
      <dl className="scenario-facts" aria-label="Scenario inputs">
        <div><dt>Initial battery charge</dt><dd>{result.input.battery?.initial_soc !== undefined ? percent(result.input.battery.initial_soc) : 'Not returned'}</dd></div>
        <div><dt>Blackout duration</dt><dd>{hours(duration)}</dd></div>
        <div><dt>Critical demand</dt><dd>{demand}</dd></div>
        <div><dt>Battery capacity</dt><dd>{result.input.battery?.capacity_kwh !== undefined ? `${number(result.input.battery.capacity_kwh)} kWh` : 'Not returned'}</dd></div>
      </dl>
    </div>
    <div className="trace-section">
      <div className="section-heading"><h4>Follow the actual power supply</h4><p>Solid: critical demand served. Hatched: critical demand partly or fully unserved.</p></div>
      <div className="supply-strip" role="img" aria-label="Critical power through the calculated blackout. Hatched intervals indicate unserved critical demand.">
        {result.trace.map((row, i) => <span key={i} className={row.unserved_critical_kw > 1e-9 ? 'supply-fails' : 'supply-survives'} style={{ width: `${row.duration_hours / duration * 100}%` }} />)}
        <i className="trace-cursor" style={{ left: `${point.elapsed_hours / duration * 100}%` }} />
      </div>
      <div className="trace-scale"><span>0 h / grid disconnected</span><span>{hours(duration)} / end of tested window</span></div>
      <label className="trace-control">Inspect the calculated timeline <output>{hours(point.elapsed_hours)}</output><input name="outage-trace" aria-label="Outage trace position" type="range" min={0} max={result.trace.length - 1} value={index} onChange={event => onIndex(Number(event.target.value))} /></label>
      <div className="trace-readout"><span><small>Battery at this interval</small><strong>{percent(point.battery_soc)}</strong></span><span><small>Critical demand served</small><strong>{number(point.critical_served_kw)} / {number(point.critical_demand_kw)} kW</strong></span><span><small>Unserved critical energy / full run</small><strong>{number(result.summary.unserved_critical_kwh)} kWh</strong></span>
        {failureIndex >= 0 && <button className="analysis-button" onClick={() => onIndex(failureIndex)}>SHOW FIRST FAILURE ↗</button>}</div>
    </div>
    <p className="analysis-assumptions">{result.input.grid?.profile_online ? 'Grid availability follows the supplied profile.' : result.input.grid?.online ? 'Grid is connected in this input.' : 'Grid disconnected.'} {result.input.solar?.profile_kw ? 'Solar follows the supplied profile.' : `Solar input: ${number(result.input.solar?.generation_kw ?? 0)} kW.`} {result.input.load?.shed_noncritical_during_outage ? 'Noncritical demand is shed during the outage.' : 'Noncritical demand competes for available power.'}</p>
  </section>
}
