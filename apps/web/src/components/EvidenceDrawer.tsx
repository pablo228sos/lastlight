import { useEffect, useRef } from 'react'
import type { PhysicsSource } from '../app/usePhysicsRun'
import type { ComparisonResult, SimulationResult } from '../lib/contracts'
import { downloadEvidenceReport } from '../lib/report'

export function EvidenceDrawer({ onClose, source, baseline, comparison, selectedRun }: {
  onClose: () => void; source: PhysicsSource | null; baseline: SimulationResult | null
  comparison: ComparisonResult | null; selectedRun: 'baseline' | 'upgraded'
}) {
  const closeRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    const previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null
    closeRef.current?.focus()
    const onKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKeyDown)
    return () => { window.removeEventListener('keydown', onKeyDown); previouslyFocused?.focus() }
  }, [onClose])
  return <div className="drawer-backdrop" onClick={onClose}>
    <aside className="evidence-drawer" role="dialog" aria-modal="true" aria-label="Data and methods" onClick={(event) => event.stopPropagation()}>
      <div className="drawer-header"><span>DATA &amp; METHODS / 00</span><button ref={closeRef} onClick={onClose} aria-label="Close data and methods">×</button></div>
      <p className="drawer-overline">EVIDENCE REGISTER</p><h2>What you are<br /><em>looking at.</em></h2>
      <p>The district and school are illustrative 3D geometry, not surveyed infrastructure. The school scenario uses synthetic assumptions. Its numerical outage trace comes from the deterministic physics engine{source === 'offline' ? ' as a previously computed replay' : source === 'live' ? ' through the local API' : ' when a validated run is loaded'}.</p>
      <div className="drawer-fact"><span>SCENE</span><strong>SYNTHETIC VISUAL MODEL</strong></div>
      <div className="drawer-fact"><span>LOCATION</span><strong>BISHKEK CONTEXT, NOT SURVEYED GEOMETRY</strong></div>
      <div className="drawer-fact"><span>PHYSICS SOURCE</span><strong>{source === 'live' ? 'LIVE LOCAL PHYSICS API' : source === 'offline' ? 'VERIFIED ENGINE-GENERATED REPLAY' : 'NO PHYSICS RUN LOADED'}</strong></div>
      <div className="drawer-fact"><span>MODEL</span><strong>{baseline?.model_version ?? 'NOT LOADED'}</strong></div>
      <div className="drawer-fact"><span>INPUTS</span><strong>SYNTHETIC SCHOOL ARCHETYPE, NO MEASURED METERS</strong></div>
      <div className="drawer-fact"><span>TIME ZERO</span><strong>PRE-OUTAGE VIEW IS PRESENTATION; TRACE STARTS GRID OFFLINE</strong></div>
      <div className="drawer-fact"><span>BOUNDARY</span><strong>NO LIVE TELEMETRY, WEATHER FEED OR MAPPED GRID</strong></div>
      {source && baseline && <button className="drawer-download" data-testid="download-report" onClick={() => downloadEvidenceReport({ source, baseline, comparison, selectedRun })}>DOWNLOAD VERIFIED JSON REPORT ↗</button>}
      {source && baseline && <p className="drawer-report-note">Includes the resolved inputs, complete physics trace, result, run hashes and limitations. {comparison ? 'The baseline and upgrade summaries are both included.' : 'Run the upgrade comparison to include both scenarios.'}</p>}
      <button className="drawer-close" onClick={onClose}>CLOSE REGISTER ↗</button>
    </aside>
  </div>
}
