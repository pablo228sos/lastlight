import { useEffect, useRef } from 'react'
import type { SimulationResult } from '../lib/contracts'

export function EvidenceDrawer({ onClose, run }: { onClose: () => void; run: SimulationResult | null }) {
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
      <p>The district geometry and facility inputs are synthetic research examples. No live telemetry, surveyed utility lines or weather feed is connected. {run ? 'The active school figures and lighting use one calculated energy trace under the declared model assumptions.' : 'No calculated run is currently displayed; the scene is a visual rehearsal.'}</p>
      <div className="drawer-fact"><span>SCENE</span><strong>SYNTHETIC VISUAL MOCK</strong></div>
      <div className="drawer-fact"><span>LOCATION</span><strong>BISHKEK CONTEXT, NOT SURVEYED GEOMETRY</strong></div>
      <div className="drawer-fact"><span>SIMULATION</span><strong>{run ? run.physics_version : 'VISUAL REHEARSAL / NO ACTIVE CALCULATION'}</strong></div>
      <div className="drawer-fact"><span>RESEARCH BOUNDARY</span><strong>NO FIELD VALIDATION OR ENGINEERING CERTIFICATION</strong></div>
      <button className="drawer-close" onClick={onClose}>CLOSE REGISTER ↗</button>
    </aside>
  </div>
}
