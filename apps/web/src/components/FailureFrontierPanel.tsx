import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { PhysicsSource } from '../app/usePhysicsRun'
import type { SimulationResult } from '../lib/contracts'
import { requestFrontier, verifiedFrontier, type FrontierCell, type FrontierResult } from '../lib/failureFrontier'

export function FailureFrontierPanel({ source, baseline, onClose }: { source: PhysicsSource; baseline: SimulationResult; onClose: () => void }) {
  const [result, setResult] = useState<FrontierResult | null>(() => source === 'offline' ? verifiedFrontier() : null)
  const [shownSource, setShownSource] = useState<PhysicsSource>(source)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] = useState<FrontierCell | null>(null)
  const close = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    close.current?.focus()
    const key = (event: KeyboardEvent) => { if (event.key === 'Escape') { event.stopImmediatePropagation(); onClose() } }
    window.addEventListener('keydown', key, true)
    return () => window.removeEventListener('keydown', key, true)
  }, [onClose])
  useEffect(() => {
    let active = true
    if (source === 'live') void requestFrontier().then(value => { if (active) setResult(value) }).catch(cause => { if (active) setError(cause instanceof Error ? cause.message : 'Frontier could not be loaded.') })
    return () => { active = false }
  }, [source])
  const currentCase = result?.trace.find(point => Math.abs(point.initial_soc - baseline.input.battery.initial_soc) < .001 && Math.abs(point.duration_hours - baseline.input.duration_hours) < .001)
  const cell = selected ?? currentCase
  const ordered = result?.axes.initial_soc.flatMap((_, row) => result.trace.slice((result.axes.initial_soc.length - row - 1) * result.axes.duration_hours.length, (result.axes.initial_soc.length - row) * result.axes.duration_hours.length)) ?? []
  return createPortal(<div className="frontier-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}>
    <section className="frontier-panel" role="dialog" aria-modal="true" aria-label="Physics verified Failure Frontier" data-testid="frontier-panel">
      <header><span>ANALYSIS / 02</span><button ref={close} onClick={onClose} aria-label="Close Failure Frontier">×</button></header>
      <h2>Failure Frontier<span>.</span></h2>
      <p className="frontier-intro">At {baseline.input.battery.capacity_kwh} kWh, compare starting charge with outage duration. Each of the {result?.summary.verified_cells ?? 273} cells is classified from the official physics trace. The diamond marks the active baseline case. Failure exactly at a window's right edge is excluded.</p>
      <div className="frontier-identity">{shownSource === 'live' ? 'LIVE PHYSICS API' : 'VERIFIED OFFLINE REPLAY'} <span>/</span> SYNTHETIC SCHOOL SCENARIO <span>/</span> NO ML PROPOSALS</div>
      {error && <div className="frontier-error" role="alert">{error}<button onClick={() => { setError(null); setResult(verifiedFrontier()); setShownSource('offline') }}>LOAD VERIFIED OFFLINE MAP</button></div>}
      {!result && !error && <p role="status">Calculating the physical boundary…</p>}
      {result && <>
        <div className="frontier-layout">
          <div className="frontier-plot-wrap"><span className="frontier-axis-y">INITIAL BATTERY SOC</span><div className="frontier-y-ticks"><span>100%</span><span>80%</span><span>60%</span><span>40%</span><span>20%</span></div><div className="frontier-plot" style={{ gridTemplateColumns: `repeat(${result.axes.duration_hours.length}, minmax(0, 1fr))`, gridTemplateRows: `repeat(${result.axes.initial_soc.length}, minmax(0, 1fr))` }}>
            {ordered.map((point, index) => {
              const isCurrent = point === currentCase
              return <button key={index} className={`${point.failed ? 'failed' : 'sustained'}${isCurrent ? ' current-case' : ''}`} data-testid={isCurrent ? 'frontier-current-case' : undefined} onMouseEnter={() => setSelected(point)} onFocus={() => setSelected(point)}
                aria-label={`${(point.initial_soc * 100).toFixed(0)}% charge, ${point.duration_hours.toFixed(2)} hours: ${point.failed ? 'critical failure observed' : 'critical load sustained'}${isCurrent ? ', active baseline case' : ''}`} />
            })}
          </div><div className="frontier-axis-x"><span>0.25 H</span><span>3 H</span><span>6 H</span><span>9 H</span><span>{result.axes.duration_hours.at(-1)?.toFixed(0)} H</span></div><div className="frontier-axis-title">OUTAGE DURATION / HOURS</div></div>
          <aside className="frontier-reading"><span>SELECTED PHYSICAL CASE</span><strong>{cell ? `${(cell.initial_soc * 100).toFixed(0)}%` : '—'} <small>INITIAL SOC</small></strong><strong>{cell?.duration_hours.toFixed(2) ?? '—'} <small>HOUR HORIZON</small></strong><div className={cell?.failed ? 'reading-failed' : 'reading-safe'}>{cell?.failed ? 'CRITICAL FAILURE OBSERVED' : 'CRITICAL LOAD SUSTAINED'}</div><p>{cell?.failed ? `First unmet critical demand after ${cell.first_failure_hours?.toFixed(2)} hours.` : 'No critical failure is observed inside this time window.'}</p><small>PHYSICS RUN / {cell?.verification_run_id.slice(0, 8)}</small></aside>
        </div>
        <div className="frontier-legend"><span><i className="sustained" /> SUSTAINED</span><span><i className="failed" /> FAILURE OBSERVED</span><span><i className="current" /> ACTIVE BASELINE</span><span>{result.summary.physics_calls} OFFICIAL RUNS / {result.summary.verified_cells} VERIFIED CELLS</span></div>
        <footer>PHYSICS {result.physics_version} · SCHEMA {result.schema_version} · ML CHECKPOINT 1.1.0 NOT ADAPTED TO OFFICIAL 1.0.0</footer>
      </>}
    </section>
  </div>, document.body)
}
