import { useEffect, useRef } from 'react'

export function EvidenceDrawer({ onClose }: { onClose: () => void }) {
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
      <p>The district composition is original, synthetic geometry. Facility labels are research archetypes. No live telemetry, mapped utility lines, weather feed, or energy calculation is displayed in this phase.</p>
      <div className="drawer-fact"><span>SCENE</span><strong>SYNTHETIC VISUAL MOCK</strong></div>
      <div className="drawer-fact"><span>LOCATION</span><strong>BISHKEK CONTEXT, NOT SURVEYED GEOMETRY</strong></div>
      <div className="drawer-fact"><span>SIMULATION</span><strong>TYPE CONTRACT PREPARED; BACKEND PENDING</strong></div>
      <div className="drawer-fact"><span>NEXT VERIFIED GATE</span><strong>ITERATION 01 · PHYSICS VERTICAL SLICE</strong></div>
      <button className="drawer-close" onClick={onClose}>CLOSE REGISTER ↗</button>
    </aside>
  </div>
}
