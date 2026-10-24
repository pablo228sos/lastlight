import { useId, useMemo, useRef, useState } from 'react'
import type { CSSProperties, KeyboardEvent } from 'react'
import type { FrontierCell, FrontierResult, SimulationResult } from '../lib/contracts'
import { conclusion, horizon, hours, number, percent } from './analysisFormat'

const cellKey = (soc: number, duration: number) => `${soc}:${duration}`
// Position actual values at sample centres, with half a cell of padding at each edge.
function position(value: number, values: number[]) {
  const span = values[values.length - 1] - values[0]
  return span === 0 ? 50 : (0.5 / values.length + (value - values[0]) / span * (1 - 1 / values.length)) * 100
}
const ticks = (values: number[], count: number) => values.filter((_, i) => i === values.length - 1 || i % Math.max(1, Math.ceil((values.length - 1) / (count - 1))) === 0)
function hourTicks(values: number[]) {
  const low = values[0], high = values[values.length - 1]
  const step = [.25, .5, 1, 2, 3, 4, 6, 8, 12, 24].find(value => (high - low) / value <= 4) ?? 24
  const result = [low]
  for (let value = Math.ceil(low / step) * step; value < high; value += step) {
    if (value - low >= step * .45 && high - value >= step * .45) result.push(value)
  }
  if (high > low) result.push(high)
  return result
}

export function FrontierChart({ frontier, result }: { frontier: FrontierResult; result: SimulationResult }) {
  const id = useId()
  const { socs, durations, cells, boundaries } = useMemo(() => {
    const socs = [...new Set(frontier.trace.map(cell => cell.initial_soc))].sort((a, b) => a - b)
    const durations = [...new Set(frontier.trace.map(cell => cell.duration_hours))].sort((a, b) => a - b)
    const lookup = new Map(frontier.trace.map(cell => [cellKey(cell.initial_soc, cell.duration_hours), cell]))
    const cells = durations.toReversed().flatMap(duration => socs.map(soc => lookup.get(cellKey(soc, duration))).filter((cell): cell is FrontierCell => !!cell))
    const boundaries = socs.map(soc => frontier.trace.find(cell => cell.initial_soc === soc && cell.first_failure_hours !== null)).filter((cell): cell is FrontierCell => !!cell)
    return { socs, durations, cells, boundaries }
  }, [frontier.trace])
  const [selected, setSelected] = useState<number | 'current'>('current')
  const [showMl, setShowMl] = useState(true)
  const refs = useRef<(HTMLButtonElement | null)[]>([])
  const charge = result.input.battery?.initial_soc
  const duration = horizon(result)
  const inside = charge !== undefined && charge >= socs[0] && charge <= socs[socs.length - 1] && duration >= durations[0] && duration <= durations[durations.length - 1]
  const onGrid = inside && cells.some(cell => Math.abs(cell.initial_soc - charge!) < 1e-9 && Math.abs(cell.duration_hours - duration) < 1e-9)
  const cell = typeof selected === 'number' ? cells[Math.min(selected, cells.length - 1)] : null
  const coordinate = (soc: number, h: number): CSSProperties => ({ left: `${position(soc, socs)}%`, top: `${100 - position(h, durations)}%` })
  const navigate = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const move: Record<string, number> = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: socs.length, ArrowUp: -socs.length }
    let next = index
    if (event.key in move) next = Math.max(0, Math.min(cells.length - 1, index + move[event.key]))
    else if (event.key === 'Home') next = event.ctrlKey ? 0 : index - index % socs.length
    else if (event.key === 'End') next = event.ctrlKey ? cells.length - 1 : Math.min(cells.length - 1, index - index % socs.length + socs.length - 1)
    else return
    event.preventDefault(); setSelected(next); refs.current[next]?.focus({ preventScroll: true })
  }
  return <figure className="frontier-chart" data-testid="frontier-map" aria-labelledby={id + '-title'}>
    <figcaption><h4 id={id + '-title'}>WHEN DOES THE SCHOOL LOSE POWER?</h4><p>Each square represents a tested combination of battery charge and blackout duration.</p></figcaption>
    <div className="frontier-layout"><div className="frontier-visual">
    <div className="chart-current-caption" data-testid="current-scenario-label"><span className="legend-symbol current" aria-hidden="true" /><strong>YOUR SCENARIO</strong> {charge !== undefined ? percent(charge) + ' CHARGE' : 'CHARGE NOT RETURNED'}, {number(duration)} HOURS</div>
    <div className="chart-shell">
      <p className="chart-y-title">Blackout duration (hours)</p>
      <div className="chart-frame" role="group" aria-label="Physics-verified battery charge and blackout duration map" aria-describedby={id + '-help'}>
        {hourTicks(durations).map(value => <span className="chart-y-tick" key={value} style={{ top: `${100 - position(value, durations)}%` }}>{number(value)}</span>)}
        <div className="chart-plot">
          {cells.map((item, i) => <button key={cellKey(item.initial_soc, item.duration_hours)}
            ref={node => { refs.current[i] = node }} className={'frontier-cell ' + (item.failed ? 'cell-fails' : 'cell-survives')}
            style={{ ...coordinate(item.initial_soc, item.duration_hours), width: `calc(${100 / socs.length}% - 2px)`, height: `calc(${100 / durations.length}% - 2px)` }}
            tabIndex={selected === i || (selected === 'current' && i === 0) ? 0 : -1} aria-pressed={selected === i}
            aria-label={`Battery ${percent(item.initial_soc)}, blackout ${hours(item.duration_hours)}: critical power ${item.failed ? 'fails' : 'survives'}. Physics verified.`}
            onFocus={() => setSelected(i)} onPointerEnter={() => setSelected(i)} onClick={() => setSelected(i)} onKeyDown={event => navigate(event, i)} />)}
          {boundaries.filter(item => item.first_failure_hours! >= durations[0] && item.first_failure_hours! <= durations[durations.length - 1]).map(item => <span className="boundary-sample" key={item.initial_soc} style={coordinate(item.initial_soc, item.first_failure_hours!)} aria-hidden="true" />)}
          {showMl && frontier.verified_candidates.filter(item => item.physics_verified).map((item, i) => <span key={i} data-testid="ai-marker" className="chart-ai-marker" style={coordinate(item.initial_soc, item.duration_hours)} aria-hidden="true" />)}
          {inside && <button className="chart-current-marker" data-testid="current-scenario-marker" style={coordinate(charge!, duration)} aria-label={`Current school scenario: ${percent(charge!)} charge, ${hours(duration)} blackout. ${conclusion(result)}`}
            onClick={() => setSelected('current')} onFocus={() => setSelected('current')}><span aria-hidden="true" /></button>}
        </div>
        {ticks(socs, 5).map(value => <span className="chart-x-tick" key={value} style={{ left: `${position(value, socs)}%` }}>{number(value * 100)}%</span>)}
      </div>
      <p className="chart-x-title">Initial battery charge (%)</p>
    </div>
    <div className="cell-inspector" role="status" aria-live="polite" aria-atomic="true" data-testid="cell-inspector">
      {cell ? <><span className={'legend-symbol ' + (cell.failed ? 'fails' : 'survives')} aria-hidden="true" /><div><strong>TESTED SCENARIO / {cell.failed ? 'CRITICAL POWER FAILS' : 'CRITICAL POWER SURVIVES'}</strong><p>Battery: {percent(cell.initial_soc)} · Blackout: {hours(cell.duration_hours)} · {cell.first_failure_hours !== null ? `First failure: ${hours(cell.first_failure_hours)}.` : 'No critical failure observed in this window.'} Physics verified.</p></div></>
        : <><span className="legend-symbol current" aria-hidden="true" /><div><strong>YOUR EXACT SCHOOL RUN / PHYSICS-CALCULATED</strong><p>Battery: {charge !== undefined && percent(charge)} · Blackout: {hours(duration)} · {conclusion(result)}</p></div></>}
    </div>
    <p className="chart-help" id={id + '-help'}>Hover, tap or focus a square to inspect it. Use arrow keys to move between tests; Home and End move across a row.</p>
    </div><aside className="frontier-context" aria-label="Map interpretation">
    <div className="frontier-legend" role="group" aria-label="Chart legend">
      <span><i className="legend-symbol survives" aria-hidden="true" />CRITICAL POWER SURVIVES</span>
      <span><i className="legend-symbol fails" aria-hidden="true" />CRITICAL POWER FAILS</span>
      <span><i className="legend-symbol ai" aria-hidden="true" />AI-SUGGESTED, PHYSICS-VERIFIED SCENARIO</span>
      <span><i className="legend-symbol current" aria-hidden="true" />CURRENT SCHOOL SCENARIO</span>
    </div>
    <p className="map-current-result"><strong>Your school scenario</strong>{conclusion(result)}</p>
    <div className="boundary-explanation"><span className="boundary-key" aria-hidden="true" /><p><strong>FAILURE BOUNDARY</strong> Above a tick, critical power cannot last the full blackout. Each tick is verified at one charge.</p></div>
    <p className="chart-domain-note">{!inside ? 'Your school scenario is outside this map’s sampled range. Its separate physical calculation is shown above.' : onGrid ? 'Your scenario coincides with a sampled grid point and has its own physical calculation.' : 'Your diamond is between sampled cells. It comes from your separate school calculation, not an extra grid sample.'} No boundary is interpolated between charge samples.</p>
    {frontier.model_version && <label className="marker-toggle"><input type="checkbox" name="show-ai-markers" checked={showMl} onChange={event => setShowMl(event.target.checked)} />Show AI-suggested test cases ({frontier.verified_candidates.filter(item => item.physics_verified).length})</label>}
    {!frontier.model_version && <p className="chart-physics-note">PHYSICS VERIFIED. This colored map is calculated by physics. AI test cases can be requested in the next chapter.</p>}
    </aside></div>
  </figure>
}
