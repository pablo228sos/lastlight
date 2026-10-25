import { useEffect, useRef, useState } from 'react'
import type { PhysicsSource } from '../app/usePhysicsRun'
import type { SimulationInput } from '../lib/contracts'
import { requestFrontier, verifiedFrontier, type FrontierCell, type FrontierResult } from '../lib/failureFrontier'
import { verifiedBaseline } from '../lib/physicsApi'
import { requestCandidates, type CandidateResult } from '../lib/intelligenceApi'
import { AnalysisDialog } from './AnalysisDialog'

export function FailureFrontierPanel({ source, scenario, onClose }: { source: PhysicsSource; scenario: SimulationInput; onClose: () => void }) {
  const archiveMatches = JSON.stringify(scenario) === JSON.stringify(verifiedBaseline().input)
  const [result, setResult] = useState<FrontierResult | null>(() => source === 'offline' && archiveMatches ? verifiedFrontier() : null)
  const [shownSource, setShownSource] = useState<PhysicsSource>(source)
  const [error, setError] = useState<string | null>(source === 'offline' && !archiveMatches ? 'No archived map matches this active scenario. Run live physics for its map.' : null)
  const [selected, setSelected] = useState<FrontierCell | null>(null)
  const [candidates, setCandidates] = useState<CandidateResult | null>(null)
  const [candidateError, setCandidateError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const proposal = useRef<AbortController | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    if (source === 'live') void requestFrontier(scenario, controller.signal).then(value => { if (!controller.signal.aborted) setResult(value) }).catch(cause => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'Frontier could not be loaded.') })
    return () => { controller.abort(); proposal.current?.abort() }
  }, [source, scenario])
  const suggest = async () => {
    if (!result) return
    proposal.current?.abort()
    const controller = new AbortController(); proposal.current = controller
    setBusy(true); setCandidateError(null)
    try { const value = await requestCandidates(scenario, result, controller.signal); if (!controller.signal.aborted) setCandidates(value) }
    catch (cause) { if (!controller.signal.aborted) setCandidateError(cause instanceof Error ? cause.message : 'AI suggestions unavailable.') }
    finally { if (!controller.signal.aborted) setBusy(false) }
  }
  const cell = selected ?? result?.trace.find(point => Math.abs(point.initial_soc - scenario.battery.initial_soc) < .001 && point.duration_hours > (scenario.duration_hours / 2))
  const ordered = result?.axes.initial_soc.flatMap((_, row) => result.trace.slice((result.axes.initial_soc.length - row - 1) * result.axes.duration_hours.length, (result.axes.initial_soc.length - row) * result.axes.duration_hours.length)) ?? []
  const checked = candidates?.candidates ?? []
  return <AnalysisDialog title="Physics verified Failure Frontier" closeLabel="Close Failure Frontier" testId="frontier-panel" label="SCHOOL / PHYSICS + CHECKED AI CASES" onClose={onClose}>
    <div>
      <h2>Failure Frontier<span>.</span></h2>
      <p className="frontier-intro">How long can critical power last at each starting charge? Every cell comes from an official physical trace. A failure exactly at the right endpoint is outside the observation window.</p>
      <div className="frontier-identity">{shownSource === 'live' ? 'LIVE PHYSICS API' : 'VERIFIED OFFLINE REPLAY'} · {scenario.battery.capacity_kwh} kWh · {scenario.load.critical_kw} kW CRITICAL · {(scenario.battery.initial_soc * 100).toFixed(0)}% ACTIVE CHARGE</div>
      {error && <div className="frontier-error" role="alert">{error}{archiveMatches && <button onClick={() => { setError(null); setResult(verifiedFrontier()); setShownSource('offline') }}>LOAD MATCHING VERIFIED OFFLINE MAP</button>}</div>}
      {!result && !error && <p role="status">Calculating the physical boundary…</p>}
      {result && <>
        <div className="candidate-toolbar">
          <button className="analysis-button" data-testid="show-ai-candidates" onClick={() => void suggest()} disabled={busy}>{busy ? 'CHECKING AI-SUGGESTED CASES…' : 'SHOW AI-SUGGESTED CASES'}</button>
          {busy && <button className="analysis-button" onClick={() => { proposal.current?.abort(); setBusy(false) }}>CANCEL</button>}
          {candidates && <div role="status"><p data-testid="candidate-count">{candidates.neural_status === 'available' ? `${checked.length} independently checked synthetic cases.` : 'AI suggestions unavailable. The physical map remains available.'}</p><span className="model-identity" data-testid="candidate-model">{candidates.neural_model_version}</span></div>}
        </div>
        <div className="frontier-layout">
          <div className="frontier-plot-wrap"><span className="frontier-axis-y">INITIAL BATTERY CHARGE</span>
            <div className="frontier-y-ticks"><span>{(result.axes.initial_soc.at(-1)! * 100).toFixed(0)}%</span><span>{(result.axes.initial_soc[0] * 100).toFixed(0)}%</span></div>
            <div className="frontier-plot" style={{ gridTemplateColumns: `repeat(${result.axes.duration_hours.length}, minmax(0, 1fr))`, gridTemplateRows: `repeat(${result.axes.initial_soc.length}, minmax(0, 1fr))` }}>
              {ordered.map((point, index) => { const ai = checked.find(item => item.initial_soc === point.initial_soc && item.duration_hours === point.duration_hours); return <button key={index} className={(point.failed ? 'failed' : 'sustained') + (ai ? ' ai-checked' : '')} onMouseEnter={() => setSelected(point)} onFocus={() => setSelected(point)} onClick={() => setSelected(point)}
                aria-label={`${(point.initial_soc * 100).toFixed(0)}% charge, ${point.duration_hours.toFixed(2)} hours: ${point.failed ? 'critical failure observed' : 'critical load sustained'}${ai ? ', AI suggested and independently physics checked' : ''}`} /> })}
            </div><div className="frontier-axis-x"><span>0.25 H</span><span>OUTAGE DURATION</span><span>{result.axes.duration_hours.at(-1)?.toFixed(0)} H</span></div>
          </div>
          <aside className="frontier-reading"><span>SELECTED PHYSICAL CASE</span><strong>{cell ? `${(cell.initial_soc * 100).toFixed(0)}%` : '—'} <small>INITIAL CHARGE</small></strong><strong>{cell?.duration_hours.toFixed(2) ?? '—'} <small>HOUR WINDOW</small></strong><div className={cell?.failed ? 'reading-failed' : 'reading-safe'}>{cell ? cell.failed ? 'CRITICAL FAILURE OBSERVED' : 'CRITICAL LOAD SUSTAINED' : 'SELECT A CASE'}</div><p>{cell?.failed ? `First unmet critical demand at ${cell.first_failure_hours?.toFixed(2)} hours.` : 'No critical failure is observed inside this time window.'}</p><small>PHYSICS RUN / {cell?.verification_run_id.slice(0, 8)}</small></aside>
        </div>
        <div className="frontier-legend"><span><i className="sustained" /> SUSTAINED</span><span><i className="failed" /> FAILURE OBSERVED</span><span>○ AI-SUGGESTED, PHYSICS CHECKED</span><span>{result.summary.physics_calls} RUNS / {result.summary.verified_cells} CELLS</span></div>
        <section className="candidate-section"><h3>Additional cases worth checking</h3><p>The model selects cases near its estimated boundary. Official physics independently simulates each selected case; map colors remain physical.</p>
          {candidateError && <p role="alert">{candidateError}</p>}
          {candidates && <div>
            {!!checked.length && <details><summary>Inspect each independent physical check</summary><ul className="candidate-list">{checked.map(item => <li key={item.input_hash}>{(item.initial_soc * 100).toFixed(0)}% charge · {item.duration_hours.toFixed(2)} h · Physics: {item.physics_summary.survived_full_window ? 'sustained' : `failure at ${item.physics_summary.critical_survival_hours?.toFixed(2)} h`} · AI score {item.neural.synthetic_failure_score.toFixed(4)}{item.neural.outside_training_domain && ' · outside training domain'}<small>Run {item.physics_run_id}</small></li>)}</ul></details>}
          </div>}
          <p className="score-explanation">Candidate count is not model accuracy or measured blackout history. No ML acceleration advantage is claimed.</p>
        </section>
        <footer>PHYSICS {result.physics_version} · SCHEMA {result.schema_version} · ACTIVE SCENARIO INPUTS · SYNTHETIC, NOT SITE MEASUREMENTS</footer>
      </>}
    </div>
  </AnalysisDialog>
}
