import { useState } from 'react'
import type { usePhysicsRun } from '../app/usePhysicsRun'
import { failureHours } from '../lib/physics'
import { FailureFrontierPanel } from './FailureFrontierPanel'
import { DesignSearchPanel } from './DesignSearchPanel'
import { publicOfflineOnly } from '../lib/deployment'

type Physics = ReturnType<typeof usePhysicsRun>
const hours = (value: number) => {
  const seconds = Math.round(value * 3600)
  return [Math.floor(seconds / 3600), Math.floor(seconds % 3600 / 60), seconds % 60].map(part => part.toString().padStart(2, '0')).join(':')
}
const kw = (value: number) => value.toFixed(2)

export function SimulationInstrument({ physics }: { physics: Physics }) {
  const [frontierOpen, setFrontierOpen] = useState(false)
  const [searchOpen, setSearchOpen] = useState(false)
  if (physics.status === 'idle') return null
  if (physics.status === 'loading') return <aside className="simulation-instrument pending" aria-label="Simulation status">
    <div className="instrument-header"><span>PHYSICS / CONNECTING</span><i /></div>
    <p>{publicOfflineOnly ? 'Loading the verified engine-generated school replay.' : 'Requesting the deterministic school scenario from the local physics service.'}</p>
  </aside>
  if (physics.status === 'error') return <aside className="simulation-instrument pending" aria-label="Simulation status">
    <div className="instrument-header"><span>PHYSICS / UNAVAILABLE</span><i /></div>
    <p role="alert">{physics.error}</p>
    <div className="instrument-actions">{!publicOfflineOnly && <button onClick={() => void physics.begin('live')} data-testid="retry-live">RETRY LOCAL API</button>}<button onClick={() => void physics.begin('offline')} data-testid="load-offline">USE VERIFIED REPLAY ↗</button></div>
    <small>Replay is an archived engine result, not a new calculation.</small>
  </aside>
  if (!physics.result || !physics.sample || !physics.source) return null

  const result = physics.result
  const row = physics.sample.row
  const failAt = failureHours(result)
  const failed = row.unserved_critical_kw > 1e-9
  const duration = result.input.duration_hours
  return <aside className={'simulation-instrument' + (failed ? ' failed' : '')} aria-label="Physics simulation instrument" data-testid="physics-instrument">
    <div className="instrument-header"><span>{physics.source === 'live' ? 'LIVE LOCAL PHYSICS API' : 'VERIFIED OFFLINE REPLAY'}</span><i /></div>
    <div className="instrument-context"><span>{physics.selectedRun === 'upgraded' ? '36 KWH / UPGRADE' : '24 KWH / BASELINE'}</span><span title={result.model_version}>{result.model_version.replace('lastlight-dispatch-', 'MODEL ')}</span></div>
    <section className={'engineering-verdict' + (failAt === null ? ' sustained' : ' observed')} data-testid="engineering-verdict" aria-label="Engineering verdict">
      <span>ENGINEERING VERDICT / {physics.selectedRun === 'upgraded' ? 'CAPACITY UPGRADE' : 'BASELINE'}</span>
      <strong data-testid="verdict-time">{failAt === null ? `SUSTAINED ${hours(duration)}` : hours(failAt)}</strong>
      <p>{failAt === null ? `No unmet critical demand observed within this ${duration}-hour test.` : 'First unmet critical demand. Critical service is lost inside the test window.'}</p>
      <div className="verdict-facts">
        <div><span>CRITICAL LOAD</span><b>{kw(result.input.load.critical_kw)} kW</b></div>
        <div><span>BATTERY / START</span><b>{result.input.battery.capacity_kwh} kWh / {(result.input.battery.initial_soc * 100).toFixed(0)}%</b></div>
        <div><span>END STATUS</span><b>{result.summary.survived_full_window ? 'SUSTAINED' : 'UNSERVED'}</b></div>
        <div><span>UNSERVED / END SOC</span><b>{result.summary.unserved_critical_kwh.toFixed(2)} kWh / {(result.summary.ending_soc * 100).toFixed(0)}%</b></div>
      </div>
      <small data-testid="failure-summary">FIRST CRITICAL FAILURE / OBSERVED: {failAt === null ? `NONE IN ${duration}-HOUR TEST` : hours(failAt)}</small>
    </section>
    <div className="instrument-primary"><div><span>SIMULATED TIME</span><strong data-testid="sim-time">{hours(physics.elapsedHours)}</strong><small>OF {hours(duration)} / NOT WALL CLOCK</small></div><div><span>BATTERY SOC</span><strong data-testid="battery-soc">{(physics.sample.soc * 100).toFixed(1)}<small>%</small></strong><small>RESERVE FLOOR {(result.input.battery.minimum_soc * 100).toFixed(0)}%</small></div></div>
    <div className="soc-track" aria-hidden="true"><i style={{ width: `${Math.max(0, Math.min(100, physics.sample.soc * 100))}%` }} /></div>
    <div className="instrument-service"><span>CRITICAL LOAD</span><strong data-testid="critical-coverage">{kw(row.critical_served_kw)} / {kw(row.critical_demand_kw)} kW</strong><em className={failed ? 'loss' : ''}>{failed ? 'SERVICE LOSS' : 'FULLY SERVED'}</em></div>
    <div className="instrument-timeline"><input type="range" min="0" max={duration} step="0.001" value={physics.elapsedHours} onChange={event => physics.seek(Number(event.target.value))} aria-label="Simulation time in hours" data-testid="simulation-scrub" />
      {failAt !== null && <button className="failure-marker" style={{ left: `${failAt / duration * 100}%` }} onClick={() => physics.seek(failAt + .001)} title={`First critical failure at ${hours(failAt)}`} aria-label="Jump to first critical failure" data-testid="failure-marker" />}
      <div><span>00:00</span><span>{hours(duration)}</span></div>
    </div>
    <div className="instrument-actions"><button onClick={() => physics.setPlaying(!physics.playing)} data-testid="simulation-play">{physics.playing ? 'Ⅱ PAUSE' : '▶ PLAY'}</button><button onClick={() => physics.seek(0)} data-testid="simulation-rewind">↶ 00:00</button><button onClick={physics.cycleSpeed} data-testid="simulation-speed">{physics.speed}×</button></div>
    {!physics.comparison ? <button className="instrument-compare" onClick={() => void physics.compare()} disabled={physics.compareLoading} data-testid="compare-upgrade">{physics.compareLoading ? 'CALCULATING COMPARISON…' : 'COMPARE 24 → 36 KWH ↗'}</button> : <div className="instrument-comparison" data-testid="comparison-result">
      <div className="run-selector"><button className={physics.selectedRun === 'baseline' ? 'selected' : ''} onClick={() => physics.chooseRun('baseline')} data-testid="show-baseline">BASELINE / 24</button><button className={physics.selectedRun === 'upgraded' ? 'selected' : ''} onClick={() => physics.chooseRun('upgraded')} data-testid="show-upgraded">UPGRADE / 36</button></div>
      <p>BASELINE {physics.comparison.baseline.summary.critical_survival_hours?.toFixed(2)} H OBSERVED FAILURE<br />UPGRADE {physics.comparison.upgraded.summary.first_failure_utc === null ? 'NO OBSERVED FAILURE IN 12 H' : `${physics.comparison.upgraded.summary.critical_survival_hours?.toFixed(2)} H OBSERVED FAILURE`}</p>
      {physics.comparison.upgraded.summary.idealized_autonomy_hours !== null && <small>ANALYTICAL BATTERY-ONLY REFERENCE / {physics.comparison.upgraded.summary.idealized_autonomy_hours.toFixed(2)} H</small>}
    </div>}
    {physics.compareError && <p role="alert" className="instrument-error">{physics.compareError}</p>}
    <div className="analysis-launches"><button className="frontier-launch" onClick={() => setFrontierOpen(true)} data-testid="open-frontier">FAILURE FRONTIER ↗</button>
      {physics.source === 'live' && <button className="design-launch" onClick={() => { setSearchOpen(true); if (!physics.designSearch && !physics.designSearchLoading) void physics.searchDesign() }} data-testid="open-design-search">FIND VIABLE CAPACITY ↗</button>}</div>
    <div className="instrument-flows"><span>GRID <b>{row.grid_online ? 'ONLINE' : 'OFFLINE'}</b></span><span>PV <b>{kw(row.solar_kw)} kW</b></span><span>BATTERY <b>{kw(row.battery_discharge_kw - row.battery_charge_kw)} kW</b></span></div>
    {frontierOpen && physics.baseline && <FailureFrontierPanel source={physics.source} baseline={physics.baseline} onClose={() => setFrontierOpen(false)} />}
    {searchOpen && physics.baseline && physics.source === 'live' && <DesignSearchPanel baseline={physics.baseline} result={physics.designSearch} loading={physics.designSearchLoading} error={physics.designSearchError} onRetry={() => void physics.searchDesign()} onClose={() => setSearchOpen(false)} />}
  </aside>
}
