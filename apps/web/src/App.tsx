import { useCallback, useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { CameraDirector } from './scene/CameraDirector'
import { DistrictWorld } from './scene/DistrictWorld'
import { HotspotProjection } from './scene/HotspotProjection'
import { useMissionState } from './app/useMissionState'
import { EvidenceDrawer } from './components/EvidenceDrawer'
import { sites } from './features/sites'
import type { SiteId } from './features/sites'
import './styles/app.css'

type ComponentId = 'pv' | 'battery' | 'inverter'
const components: Record<ComponentId, { title: string; subtitle: string; detail: string }> = {
  pv: { title: 'ROOFTOP PV', subtitle: 'SOURCE / ON-SITE', detail: 'Modeled equipment geometry. Generation is not calculated in this visual rehearsal.' },
  battery: { title: 'STORAGE', subtitle: 'RESERVE / CABINET', detail: 'Battery enclosure shown for inspection. State of charge will come from a validated trace.' },
  inverter: { title: 'INVERTER', subtitle: 'CONVERSION / AC BUS', detail: 'Power conversion is represented spatially. No capacity or live status is claimed.' },
}

function useReducedMotion() {
  const [reduced, setReduced] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const change = () => setReduced(media.matches)
    media.addEventListener('change', change)
    return () => media.removeEventListener('change', change)
  }, [])
  return reduced
}

function App() {
  const mission = useMissionState()
  const reducedMotion = useReducedMotion()
  const lowPower = reducedMotion || navigator.hardwareConcurrency <= 4
  const [component, setComponent] = useState<ComponentId | null>(null)
  const selected = sites.find(item => item.id === mission.siteId)!
  const isFacility = mission.phase === 'SITE' || mission.phase === 'INSPECT' || mission.phase === 'BLACKOUT'
  const isOpening = mission.phase === 'INTRO'
  const showSchoolHotspots = isFacility && mission.siteId === 'school'
  const { setPhase, setShot } = mission
  const settled = useCallback(() => { setPhase('DISTRICT'); setShot('district') }, [setPhase, setShot])
  const selectSite = (id: SiteId) => { setComponent(null); mission.selectSite(id) }
  const focusComponent = (id: ComponentId) => { setComponent(id); mission.setPhase('INSPECT'); mission.setShot('equipment'); mission.setLayer('power') }

  useEffect(() => {
    const keys = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement) return
      if (event.target instanceof HTMLButtonElement && (event.key === 'Enter' || event.key === ' ')) return
      if (event.key === 'Escape') { if (mission.evidenceOpen) mission.setEvidenceOpen(false); else { setComponent(null); mission.returnCity() } }
      if (event.key.toLowerCase() === 'r') { setComponent(null); mission.reset() }
      if (event.key === ' ') { event.preventDefault(); mission.setPaused(value => !value) }
      if (event.key === 'Enter' && mission.phase === 'INTRO') mission.enter()
    }
    window.addEventListener('keydown', keys)
    return () => window.removeEventListener('keydown', keys)
  }, [mission])

  return <main className={'experience phase-' + mission.phase.toLowerCase()} data-phase={mission.phase} data-shot={mission.shot} data-visual-step={mission.visualStep} data-quality={lowPower ? 'economy' : 'full'}>
    <div className="stage" aria-label="Interactive three-dimensional synthetic Bishkek-inspired district">
      <Canvas shadows={!lowPower} dpr={lowPower ? 1 : [1, 1.5]} camera={{ position: [8, 175, 260], fov: 37, near: .1, far: 1000 }}
        gl={{ antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: new URLSearchParams(window.location.search).has('capture') }} fallback={<div className="webgl-fallback">3D rendering is unavailable on this device. The scenario controls remain accessible.</div>}>
        <CameraDirector shot={mission.shot} phase={mission.phase} siteId={mission.siteId} paused={mission.paused}
          reducedMotion={reducedMotion} onDescentComplete={settled} />
        <DistrictWorld visual={mission.visual} layer={mission.layer} phase={mission.phase} selected={mission.siteId} lowPower={lowPower}
          onSelect={selectSite} />
        <HotspotProjection />
      </Canvas>
      <div className="stage-shade" aria-hidden="true" />
      <div className="stage-grain" aria-hidden="true" />
      <div className="world-annotations" aria-label="Spatial facility controls">
        {showSchoolHotspots && <>
          <button id="hotspot-pv" className="world-hotspot" onClick={() => focusComponent('pv')}>01 <span>ROOFTOP PV</span></button>
          <button id="hotspot-inverter" className="world-hotspot" onClick={() => focusComponent('inverter')}>03 <span>INVERTER</span></button>
          <button id="hotspot-battery" className="world-hotspot" onClick={() => focusComponent('battery')}>02 <span>STORAGE</span></button>
        </>}
        {mission.phase === 'DISTRICT' && <>
          <button id="hotspot-clinic" className="world-hotspot" onClick={() => selectSite('clinic')}>CLINIC <span>FOCUS ↗</span></button>
          <button id="hotspot-business" className="world-hotspot" onClick={() => selectSite('business')}>BUSINESS <span>FOCUS ↗</span></button>
          <button id="hotspot-residential" className="world-hotspot" onClick={() => selectSite('residential')}>RESIDENTIAL <span>FOCUS ↗</span></button>
        </>}
      </div>
    </div>

    <header className="masthead">
      <button className="wordmark" onClick={mission.returnCity} aria-label="LASTLIGHT return to city"><span className="mark">▥</span> LASTLIGHT<span className="period">.</span></button>
      <div className="masthead-center"><span className="point" /> CURSED / ENERGY RESILIENCE LAB <span className="slash">/</span> LOGOS 2026</div>
      <button className="text-action" onClick={() => mission.setEvidenceOpen(true)}>DATA &amp; METHODS <span>↗</span></button>
    </header>

    <div className="left-rule" aria-hidden="true"><span>LL / 00.5</span><i /><span>BISHKEK / SYNTHETIC</span></div>
    <div className="top-telemetry"><span className="warm-dot" /> <span data-testid="rehearsal-label">CINEMATIC REHEARSAL / SYNTHETIC, NOT PHYSICS</span></div>
    <div className="shot-index" aria-label="Camera state"><span>CAMERA / {mission.shot.toUpperCase()}</span><span className="shot-mark">{mission.phase === 'DESCENT' ? '● ━ ━' : isFacility ? '━ ━ ●' : '━ ● ━'}</span></div>

    {isOpening ? <section className="opening-copy">
      <div className="eyebrow"><span /> THE RESILIENCE OBSERVATORY <small>N° 001</small></div>
      <h1>The last light<br /><em>should not be</em><br />a surprise<span className="period">.</span></h1>
      <p>A city is a network of human dependencies. Enter one school, inspect its energy system, and rehearse the instant the grid goes dark.</p>
      <div className="opening-actions">
        <button className="primary-action" onClick={mission.enter} data-testid="enter-lab"><b>↗</b><span>ENTER THE LAB</span><small>01 / 04</small></button>
        <button className="quiet-action" onClick={mission.skip} data-testid="skip-intro">SKIP INTRO →</button>
      </div>
    </section> : <section className="scene-title">
      <div className="eyebrow"><span /> {isFacility ? 'FACILITY / 01' : mission.phase === 'DESCENT' ? 'DESCENT / IN PROGRESS' : 'DISTRICT / SYNTHETIC'}</div>
      <h1>{isFacility ? selected.name : 'The city at night'}<span className="period">.</span></h1>
      <p>{isFacility ? selected.category : 'A modeled district inspired by Bishkek. Select a facility to enter its energy system.'}</p>
    </section>}

    <div className="geo-annotation"><span>42°52′ N · 74°36′ E</span><span>ILLUSTRATIVE GEOGRAPHY / NO UTILITY TOPOLOGY</span></div>

    {!isOpening && <nav className="facility-strip" aria-label="Select facility">
      <span className="strip-label">FOCUS /</span>
      {sites.map((site, i) => <button key={site.id} data-testid={'site-' + site.id} aria-pressed={mission.siteId === site.id && isFacility}
        className={mission.siteId === site.id && isFacility ? 'selected' : ''} onClick={() => selectSite(site.id)}>
        <small>0{i + 1}</small>{site.name.toUpperCase()}<span>↗</span>
      </button>)}
    </nav>}

    {isFacility && <div className="equipment-spine">
      <span className="spine-label">SYSTEM / {mission.siteId.toUpperCase()}</span>
      <button className={mission.layer === 'architecture' ? 'selected' : ''} onClick={() => mission.setLayer('architecture')} data-testid="layer-architecture">ARCHITECTURE</button>
      <button className={mission.layer === 'power' ? 'selected' : ''} onClick={() => mission.setLayer('power')} data-testid="layer-power">POWER PATH</button>
      <button onClick={mission.orbit} data-testid="orbit">ORBIT ↗</button>
      <button onClick={mission.inspect} data-testid="inspect">INSPECT ↘</button>
    </div>}

    {component && isFacility && <aside className="component-note" aria-label="Equipment inspection">
      <button onClick={() => setComponent(null)} aria-label="Close equipment inspection">×</button>
      <span>{components[component].subtitle}</span>
      <h2>{components[component].title}</h2>
      <p>{components[component].detail}</p>
    </aside>}

    {!isOpening && <div className="transport">
      <div className="transport-left">
        <span className="transport-kicker">SCENE / {mission.phase}</span>
        <span className="transport-title">{mission.visual.gridConnected ? 'GRID CONNECTED' : 'GRID DISCONNECTED'}</span>
      </div>
      <div className="transport-actions">
        {mission.phase === 'DISTRICT' || mission.phase === 'DESCENT' ? <button className="focus-action" onClick={() => selectSite('school')} data-testid="focus-school">FOCUS SCHOOL <span>↗</span></button> : <>
          {mission.phase === 'SITE' && <button onClick={mission.inspect} data-testid="enter-simulation">INSPECT SYSTEM <span>↗</span></button>}
          {mission.phase !== 'BLACKOUT' ? <button className="disconnect" onClick={mission.disconnect} data-testid="disconnect-grid">DISCONNECT GRID <span>↗</span></button>
            : <button className="reset" onClick={mission.reset} data-testid="reset-scene">RESET SCENE <span>↶</span></button>}
        </>}
        <button className="icon-action" onClick={() => mission.setPaused(!mission.paused)} aria-label={mission.paused ? 'Play camera' : 'Pause camera'} data-testid="pause-camera">{mission.paused ? '▶' : 'Ⅱ'}</button>
        <button className="icon-action" onClick={mission.returnCity} aria-label="Return to city" data-testid="return-city">⌂</button>
      </div>
      <div className="timeline" aria-label="Visual rehearsal states">
        <button className={mission.visualStep === 0 ? 'active' : ''} onClick={mission.reset}>CONNECTED</button>
        <div className="timeline-track"><i className={mission.visualStep === 1 ? 'offline' : ''} /></div>
        <button className={mission.visualStep === 1 ? 'active' : ''} onClick={mission.disconnect}>DISCONNECTED</button>
        <span>VISUAL STATE REHEARSAL</span>
      </div>
    </div>}

    <footer className="footnote"><span>NO LIVE GRID DATA <i /> GEOMETRY + LIGHTING / SYNTHETIC</span><span>CURSED · KYRGYZSTAN · 2026</span></footer>
    {mission.evidenceOpen && <EvidenceDrawer onClose={() => mission.setEvidenceOpen(false)} />}
  </main>
}
export default App
