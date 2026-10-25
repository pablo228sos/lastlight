import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import type { SimulationResult } from '../lib/contracts'
import type { DesignSearchResult } from '../lib/designSearch'

export function DesignSearchPanel({ baseline, result, loading, error, onRetry, onClose }: {
  baseline: SimulationResult; result: DesignSearchResult | null; loading: boolean; error: string | null
  onRetry: () => void; onClose: () => void
}) {
  const close = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    close.current?.focus()
    const key = (event: KeyboardEvent) => { if (event.key === 'Escape') { event.stopImmediatePropagation(); onClose() } }
    window.addEventListener('keydown', key, true)
    return () => window.removeEventListener('keydown', key, true)
  }, [onClose])
  return createPortal(<div className="design-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}>
    <section className="design-panel" role="dialog" aria-modal="true" aria-label="Physics verified capacity search" data-testid="design-search-panel">
      <header><span>ANALYSIS / 03 · LIVE LOCAL PHYSICS API</span><button ref={close} onClick={onClose} aria-label="Close capacity search">×</button></header>
      <h2>Find a viable<br /><em>capacity.</em></h2>
      <p className="design-intro">One unchanged official simulation per candidate. The objective is the smallest passing capacity in this explicit set for a {baseline.input.duration_hours}-hour outage, with {(baseline.input.battery.initial_soc * 100).toFixed(0)}% initial charge and {baseline.input.load.critical_kw.toFixed(2)} kW critical load.</p>
      {loading && <p role="status" className="design-status">Testing 24, 30, 32 and 36 kWh with official physical dispatch…</p>}
      {error && <div className="design-error" role="alert">{error}<button onClick={onRetry}>RETRY OFFICIAL SEARCH ↗</button></div>}
      {result && <>
        <div className={'design-answer' + (result.selected_capacity_kwh === null ? ' infeasible' : '')}>
          <span>SMALLEST PASSING TESTED CAPACITY</span>
          <strong data-testid="design-selected">{result.selected_capacity_kwh === null ? 'NONE IN THIS SET' : `${result.selected_capacity_kwh} kWh`}</strong>
          <p>{result.selected_capacity_kwh === null ? 'None of the submitted capacities served all critical demand through the test window.' : `This candidate has no observed critical deficit inside the exclusive ${baseline.input.duration_hours}-hour horizon.`}</p>
        </div>
        <div className="design-table-wrap"><table className="design-table"><thead><tr><th>CAPACITY</th><th>12 H TEST</th><th>FIRST DEFICIT</th><th>UNSERVED</th><th>END SOC</th></tr></thead><tbody>
          {result.candidates.map(candidate => <tr key={candidate.capacity_kwh} className={candidate.capacity_kwh === result.selected_capacity_kwh ? 'selected' : ''}>
            <th>{candidate.capacity_kwh} kWh</th><td className={candidate.survived_target ? 'pass' : 'fail'}>{candidate.survived_target ? 'SUSTAINED' : 'FAILED'}</td>
            <td>{candidate.first_critical_failure_hours === null ? 'NOT OBSERVED' : `${candidate.first_critical_failure_hours.toFixed(2)} h`}</td>
            <td>{candidate.unserved_critical_kwh.toFixed(2)} kWh</td><td>{(candidate.ending_soc * 100).toFixed(1)}%</td>
          </tr>)}</tbody></table></div>
        <div className="design-method"><span>{result.candidate_count} PHYSICAL RUNS / SCHEMA {result.schema_version}</span><span>SEARCH HASH {result.input_hash.slice(0, 12)}</span></div>
        <p className="design-limit">The selection is restricted to these tested capacities. It is not a global minimum or a minimum-cost design. No equipment prices or measured school data were supplied. A pass is observed only within this test window.</p>
      </>}
    </section>
  </div>, document.body)
}
