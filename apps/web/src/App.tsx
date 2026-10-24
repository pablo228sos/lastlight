import { useMissionState } from './app/useMissionState'
import { EvidenceDrawer } from './components/EvidenceDrawer'
import { DistrictScene } from './scene/DistrictScene'
import { sites } from './features/sites'
import './styles/app.css'

function App() {
  const { view, setView, siteId, setSiteId, layer, setLayer, evidenceOpen, setEvidenceOpen } = useMissionState()
  const site = sites.find((item) => item.id === siteId)!
  return <main className={'app app--' + view}>
    <header className="topbar">
      <a className="brand" href="#top" onClick={() => setView('mission')} aria-label="LASTLIGHT home">
        <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span><span>LASTLIGHT<span className="brand-period">.</span></span>
      </a>
      <div className="topbar-center"><span className="tiny-diamond" /> ENERGY RESILIENCE RESEARCH ENVIRONMENT <span className="topbar-version">/ 00.1</span></div>
      <button className="topbar-link" onClick={() => setEvidenceOpen(true)}>DATA &amp; METHODS <span aria-hidden="true">↗</span></button>
    </header>
    <div className="workspace" id="top">
      <aside className="side-rail" aria-label="Navigation">
        <div className="rail-index">LL / 01</div><div className="rail-line" />
        <div className="rail-vertical">BISHKEK · SYNTHETIC DISTRICT</div>
        <div className="rail-bottom">42°52′ N<br />74°36′ E</div>
      </aside>
      <section className="main-stage" aria-label="Synthetic nighttime district visualization">
        <DistrictScene selected={siteId} layer={layer} onSelect={setSiteId} />
        <div className="stage-vignette" aria-hidden="true" />
        <div className="stage-topline"><span><span className="signal-dot" /> SYNTHETIC VISUAL MOCK</span><span>ESTABLISHING VIEW / BISHKEK</span></div>
        {view === 'mission' ? <div className="mission-copy">
          <div className="eyebrow"><span className="eyebrow-line" /> THE RESILIENCE OBSERVATORY <span className="eyebrow-number">N° 001</span></div>
          <h1>The last light<br /><em>should not be</em><br />a surprise<span className="heading-period">.</span></h1>
          <p>Explore how a local energy system could respond when the grid disappears. Inspect the assumptions before trusting the result.</p>
          <button className="primary-action" onClick={() => setView('theater')} data-testid="enter-simulation">
            <span className="action-icon" aria-hidden="true">↗</span><span>ENTER SIMULATION</span><span className="action-key">01 / 04</span>
          </button>
        </div> : <div className="theater-copy">
          <button className="back-link" onClick={() => setView('mission')}>← RETURN TO OVERVIEW</button>
          <div className="eyebrow"><span className="eyebrow-line" /> FACILITY INSPECTION <span className="eyebrow-number">01 / 04</span></div>
          <h1>{site.name}<span className="heading-period">.</span></h1>
          <p>{site.description}</p>
          <div className="preview-label"><span className="signal-dot" /> SCENE PREVIEW ONLY · PHYSICS CONNECTS IN ITERATION 01</div>
        </div>}
        <div className="map-caption"><span>FIG. 01</span><span>MODELED DISTRICT / NOT UTILITY TOPOLOGY</span></div>
        <div className="map-scale"><span>0</span><div /><span>100 M · ILLUSTRATIVE</span></div>
      </section>
      <aside className="inspect-panel" aria-label="Site and view controls">
        <div className="panel-head"><span>MISSION CONTROL</span><span className="panel-cross">✳</span></div>
        <div className="panel-section-title">01 <span>SELECT FACILITY</span></div>
        <div className="site-list" role="group" aria-label="Select facility">
          {sites.map((item, index) => <button key={item.id} className={'site-row ' + (siteId === item.id ? 'is-active' : '')} onClick={() => setSiteId(item.id)} aria-pressed={siteId === item.id} data-testid={'site-' + item.id}>
            <span className="site-number">0{index + 1}</span><span className="site-name">{item.name}</span><span className="site-arrow">↗</span>
          </button>)}
        </div>
        <div className="panel-section-title layer-title">02 <span>VIEW LAYER</span></div>
        <div className="layer-switch" role="group" aria-label="View layer">
          <button className={layer === 'night' ? 'selected' : ''} onClick={() => setLayer('night')} aria-pressed={layer === 'night'} data-testid="layer-night">NIGHT VIEW</button>
          <button className={layer === 'systems' ? 'selected' : ''} onClick={() => setLayer('systems')} aria-pressed={layer === 'systems'} data-testid="layer-systems">SYSTEMS</button>
        </div>
        <div className="site-profile"><span className="profile-kicker">ACTIVE OBJECT / 0{sites.findIndex((item) => item.id === siteId) + 1}</span>
          <h2>{site.name}</h2><p>{site.category}</p><div className="profile-rule" />
          <dl><div><dt>SOURCE</dt><dd>SYNTHETIC</dd></div><div><dt>MODEL</dt><dd>NOT CONNECTED</dd></div><div><dt>VIEW</dt><dd>{layer === 'night' ? 'NIGHT' : 'SYSTEMS'}</dd></div></dl>
        </div>
        <button className="evidence-button" onClick={() => setEvidenceOpen(true)}>INSPECT ASSUMPTIONS <span>↗</span></button>
      </aside>
    </div>
    <footer className="statusbar"><span><span className="status-square" /> OFFLINE VISUAL PREVIEW</span><span>NO REAL GRID OR METER DATA</span><span>CURSED / LOGOS 2026</span></footer>
    {evidenceOpen && <EvidenceDrawer onClose={() => setEvidenceOpen(false)} />}
  </main>
}
export default App
