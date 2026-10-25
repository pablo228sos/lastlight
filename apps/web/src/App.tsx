import { useCallback, useEffect, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { CameraDirector } from './scene/CameraDirector'
import { DistrictWorld } from './scene/DistrictWorld'
import { HotspotProjection } from './scene/HotspotProjection'
import { useMissionState } from './app/useMissionState'
import { usePhysicsRun } from './app/usePhysicsRun'
import { EvidenceDrawer } from './components/EvidenceDrawer'
import { SimulationInstrument } from './components/SimulationInstrument'
import { sites } from './features/sites'
import type { SiteId } from './features/sites'
import { publicOfflineOnly } from './lib/deployment'
import './styles/app.css'

type ComponentId = 'pv' | 'battery' | 'inverter'
const components: Record<ComponentId, { title: string; subtitle: string }> = {
  pv: { title: 'ROOFTOP PV', subtitle: 'SOURCE / ON-SITE' },
  battery: { title: 'STORAGE', subtitle: 'RESERVE / CABINET' },
  inverter: { title: 'INVERTER', subtitle: 'CONVERSION / AC BUS' },
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
  const physics = usePhysicsRun()
  const { reset: resetPhysics, status: physicsStatus, playing: physicsPlaying, setPlaying: setPhysicsPlaying } = physics
  const { returnCity: returnMissionCity, reset: resetMission, evidenceOpen, setEvidenceOpen, setPaused, phase, enter } = mission
  const reducedMotion = useReducedMotion()
  const lowPower = reducedMotion || navigator.hardwareConcurrency <= 4
  const [component, setComponent] = useState<ComponentId | null>(null)
  const selected = sites.find(item => item.id === mission.siteId)!
  const isFacility = mission.phase === 'SITE' || mission.phase === 'INSPECT' || mission.phase === 'BLACKOUT'
  const isOpening = mission.phase === 'INTRO'
  const showSchoolHotspots = isFacility && mission.siteId === 'school' && mission.phase !== 'BLACKOUT'
  const { setPhase, setShot } = mission
  const settled = useCallback(() => { setPhase('DISTRICT'); setShot('district') }, [setPhase, setShot])
  const selectSite = (id: SiteId) => { setComponent(null); physics.reset(); mission.selectSite(id) }
  const focusComponent = (id: ComponentId) => { setComponent(id); mission.setPhase('INSPECT'); mission.setShot('equipment'); mission.setLayer('power') }
  const inspectSite = () => { mission.inspect(); if (mission.siteId !== 'school') mission.setLayer('architecture') }
  const returnCity = useCallback(() => { setComponent(null); resetPhysics(); returnMissionCity() }, [resetPhysics, returnMissionCity])
  const resetScene = useCallback(() => { resetPhysics(); resetMission() }, [resetPhysics, resetMission])
  const disconnect = () => {
    if (mission.siteId !== 'school') return
    mission.disconnect()
    if (mission.siteId === 'school') void physics.begin(publicOfflineOnly || new URLSearchParams(window.location.search).get('demo') === 'offline' ? 'offline' : 'live')
  }
  const visual = physics.visual ?? mission.visual
  const equipmentDetail: Record<ComponentId, string> = {
    pv: physics.result ? `Modeled rooftop array. This scenario accepts ${physics.sample?.row.solar_kw.toFixed(2)} kW of PV. No weather or measured irradiance is inferred.` : 'Modeled rooftop array. A validated simulation will report accepted solar power.',
    battery: physics.result ? `${physics.result.input.battery.capacity_kwh} kWh modeled capacity, ${(physics.result.input.battery.minimum_soc * 100).toFixed(0)}% minimum SOC. Displayed charge follows the trace.` : 'Modeled battery enclosure. Capacity and charge appear after a verified simulation loads.',
    inverter: physics.result ? `${physics.result.input.inverter.max_kw} kW modeled AC limit. Islanding ${physics.result.input.inverter.islanding_capable ? 'enabled' : 'disabled'} in the resolved input.` : 'Modeled inverter enclosure. Limits appear after a verified simulation loads.',
  }

  useEffect(() => {
    const keys = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement) return
      if (event.target instanceof HTMLButtonElement && (event.key === 'Enter' || event.key === ' ')) return
      if (event.key === 'Escape') { if (evidenceOpen) setEvidenceOpen(false); else returnCity() }
      if (event.key.toLowerCase() === 'r') { setComponent(null); resetScene() }
      if (event.key === ' ') { event.preventDefault(); if (physicsStatus === 'ready') setPhysicsPlaying(!physicsPlaying); else setPaused(value => !value) }
      if (event.key === 'Enter' && phase === 'INTRO') enter()
    }
    window.addEventListener('keydown', keys)
    return () => window.removeEventListener('keydown', keys)
  }, [evidenceOpen, setEvidenceOpen, setPaused, phase, enter, physicsStatus, physicsPlaying, setPhysicsPlaying, returnCity, resetScene])

  return <main className={'experience phase-' + mission.phase.toLowerCase()} data-phase={mission.phase} data-shot={mission.shot} data-site={mission.siteId} data-visual-step={mission.visualStep} data-quality={lowPower ? 'economy' : 'full'} data-physics-source={physics.source ?? 'none'} data-critical-lit={String(visual.criticalLit)}>
    <div className="stage" aria-label="Interactive three-dimensional synthetic Bishkek-inspired district">
      <Canvas shadows={!lowPower} dpr={lowPower ? 1 : [1, 1.5]} camera={{ position: [8, 175, 260], fov: 37, near: .1, far: 1000 }}
        gl={{ antialias: true, powerPreference: 'high-performance', preserveDrawingBuffer: new URLSearchParams(window.location.search).has('capture') }} fallback={<div className="webgl-fallback">3D rendering is unavailable on this device. The scenario controls remain accessible.</div>}>
        <CameraDirector shot={mission.shot} phase={mission.phase} siteId={mission.siteId} paused={mission.paused}
          reducedMotion={reducedMotion} onDescentComplete={settled} />
        <DistrictWorld visual={visual} layer={mission.layer} phase={mission.phase} selected={mission.siteId} lowPower={lowPower}
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
      <button className="wordmark" onClick={returnCity} aria-label="LASTLIGHT return to city"><span className="mark">▥</span> LASTLIGHT<span className="period">.</span></button>
      <div className="masthead-center"><span className="point" /> CURSED / ENERGY RESILIENCE LAB <span className="slash">/</span> LOGOS 2026</div>
      <button className="text-action" onClick={() => mission.setEvidenceOpen(true)}>DATA &amp; METHODS <span>↗</span></button>
    </header>

    <div className="left-rule" aria-hidden="true"><span>LL / 03</span><i /><span>BISHKEK / SYNTHETIC</span></div>
    <div className="top-telemetry"><span className="warm-dot" /> <span data-testid="rehearsal-label">{physics.source === 'live' ? 'LIVE LOCAL PHYSICS API / SYNTHETIC INPUTS' : physics.source === 'offline' ? 'VERIFIED OFFLINE REPLAY / SYNTHETIC INPUTS' : mission.siteId === 'school' ? publicOfflineOnly ? 'PUBLIC OFFLINE DEMO / VERIFIED REPLAY AVAILABLE' : 'ILLUSTRATIVE SCENE / NO PHYSICS RUN LOADED' : 'VISUAL SITE STUDY / NO VALIDATED ENERGY MODEL'}</span></div>
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
      <div className="eyebrow"><span /> {isFacility ? `FACILITY / 0${sites.findIndex(site => site.id === mission.siteId) + 1}` : mission.phase === 'DESCENT' ? 'DESCENT / IN PROGRESS' : 'DISTRICT / SYNTHETIC'}</div>
      <h1>{isFacility ? selected.name : 'The city at night'}<span className="period">.</span></h1>
      <p>{isFacility ? selected.category : 'A modeled district inspired by Bishkek. Select a facility to enter its energy system.'}</p>
      {isFacility && mission.siteId !== 'school' && <p className="site-summary">{selected.description}</p>}
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
      {mission.siteId === 'school' ? <button className={mission.layer === 'power' ? 'selected' : ''} onClick={() => mission.setLayer('power')} data-testid="layer-power">POWER PATH</button> : <span className="spine-disclaimer">NO PHYSICS MODEL</span>}
      <button onClick={mission.orbit} data-testid="orbit">ORBIT ↗</button>
      <button onClick={inspectSite} data-testid="inspect">INSPECT ↘</button>
    </div>}

    {component && isFacility && <aside className="component-note" aria-label="Equipment inspection">
      <button onClick={() => setComponent(null)} aria-label="Close equipment inspection">×</button>
      <span>{components[component].subtitle}</span>
      <h2>{components[component].title}</h2>
      <p>{equipmentDetail[component]}</p>
    </aside>}

    {mission.phase === 'BLACKOUT' && mission.siteId === 'school' && <SimulationInstrument physics={physics} />}

    {!isOpening && <div className="transport">
      <div className="transport-left">
        <span className="transport-kicker">SCENE / {mission.phase}</span>
        <span className="transport-title">{isFacility && mission.siteId !== 'school' ? 'VISUAL SITE STUDY' : visual.gridConnected ? 'GRID CONNECTED' : visual.criticalLit ? 'GRID DISCONNECTED' : 'CRITICAL POWER LOST'}</span>
      </div>
      <div className="transport-actions">
        {mission.phase === 'DISTRICT' || mission.phase === 'DESCENT' ? <button className="focus-action" onClick={() => selectSite('school')} data-testid="focus-school">FOCUS SCHOOL <span>↗</span></button> : <>
          {mission.phase === 'SITE' && <button onClick={inspectSite} data-testid="enter-simulation">{mission.siteId === 'school' ? 'INSPECT SYSTEM' : 'EXPLORE SITE'} <span>↗</span></button>}
          {mission.phase !== 'BLACKOUT' ? mission.siteId === 'school' ? <button className="disconnect" onClick={disconnect} data-testid="disconnect-grid">DISCONNECT GRID <span>↗</span></button> : <button className="school-demo" onClick={() => selectSite('school')} data-testid="school-demo">SCHOOL PHYSICS DEMO <span>↗</span></button>
            : <button className="reset" onClick={resetScene} data-testid="reset-scene">RESET SCENE <span>↶</span></button>}
        </>}
        <button className="icon-action" onClick={() => mission.setPaused(!mission.paused)} aria-label={mission.paused ? 'Play camera' : 'Pause camera'} data-testid="pause-camera">{mission.paused ? '▶' : 'Ⅱ'}</button>
        <button className="icon-action" onClick={returnCity} aria-label="Return to city" data-testid="return-city">⌂</button>
      </div>
      {mission.siteId !== 'school' && isFacility ? <div className="timeline site-study-strip" aria-label="Site study status">VISUAL PROTOTYPE / NO BLACKOUT CALCULATION FOR THIS SITE</div> : physics.status === 'ready' ? <div className="timeline live-trace-strip" aria-label="Trace status">
        <span>TRACE / {physics.selectedRun.toUpperCase()}</span><div className="timeline-track"><i style={{ width: `${physics.elapsedHours / (physics.result?.input.duration_hours ?? 12) * 100}%` }} /></div><span>PLAYBACK IN PHYSICS INSTRUMENT ↗</span>
      </div> : <div className="timeline" aria-label="Visual rehearsal states">
        <button className={mission.visualStep === 0 ? 'active' : ''} onClick={resetScene}>CONNECTED</button>
        <div className="timeline-track"><i className={mission.visualStep === 1 ? 'offline' : ''} /></div>
        <button className={mission.visualStep === 1 ? 'active' : ''} onClick={disconnect}>DISCONNECTED</button>
        <span>VISUAL STATE REHEARSAL</span>
      </div>}
    </div>}

    <footer className="footnote"><span>NO MEASURED SITE DATA <i /> {physics.source ? 'PHYSICS INPUTS / SYNTHETIC' : 'GEOMETRY + LIGHTING / SYNTHETIC'}</span><span>CURSED · KYRGYZSTAN · 2026</span></footer>
    {mission.evidenceOpen && <EvidenceDrawer source={physics.source} baseline={physics.baseline} comparison={physics.comparison} designSearch={physics.designSearch} selectedRun={physics.selectedRun} onClose={() => mission.setEvidenceOpen(false)} />}
  </main>
}
export default App
