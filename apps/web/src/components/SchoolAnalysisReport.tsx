import { useEffect, useRef, useState } from 'react'
import type { PhysicsPanelProps } from './PhysicsPanel'
import { FrontierChart } from './FrontierChart'
import { FragilityAnalysis } from './FragilityAnalysis'
import { OutageResult } from './OutageResult'

const steps = ['Blackout result', 'Failure Frontier', 'AI vs Physics']

export function SchoolAnalysisReport(props: PhysicsPanelProps & { initialStep: number; onClose: () => void }) {
  const { result, frontier, onFrontier, prediction, onAnalyze } = props
  const dialog = useRef<HTMLDialogElement>(null)
  const content = useRef<HTMLDivElement>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const [step, setStep] = useState(props.initialStep)
  const [guided, setGuided] = useState(false)
  useEffect(() => {
    const node = dialog.current!
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    node.showModal()
    return () => { node.close(); opener?.focus({ preventScroll: true }) }
  }, [])
  const select = (next: number, guide = guided) => {
    setStep(next); setGuided(guide)
    content.current?.scrollTo({ top: 0 })
    heading.current?.focus({ preventScroll: true })
    if (next === 1 && !frontier) onFrontier()
    if (next === 2 && guide) {
      if (!prediction) onAnalyze()
      if (!frontier?.model_version) onFrontier(true)
    }
  }
  return <dialog ref={dialog} className="analysis-dialog" aria-labelledby="analysis-title" data-testid="analysis-report"
    onKeyDown={event => {
      if (event.key !== 'Tab') return
      const targets = [...event.currentTarget.querySelectorAll<HTMLElement>('button:not([disabled]):not([tabindex="-1"]), input:not([disabled]), summary, [tabindex="0"]')]
      const first = targets[0], last = targets[targets.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }}
    onCancel={event => { event.preventDefault(); props.onClose() }}>
    <header className="analysis-header">
      <div><p className="analysis-label">LASTLIGHT / SCHOOL RESILIENCE</p><h2 id="analysis-title">One school. One blackout. A tested answer.</h2></div>
      <button className="analysis-close" aria-label="Close school analysis" onClick={props.onClose}>×</button>
    </header>
    <nav className="analysis-chapters" aria-label="School analysis chapters">
      {steps.map((label, i) => <button key={label} aria-current={step === i ? 'step' : undefined} onClick={() => select(i)} data-testid={'analysis-step-' + i}>
        <span aria-hidden="true">0{i + 1}</span>{label}</button>)}
    </nav>
    <div className="analysis-scroll" ref={content}>
      <div className="chapter-intro">
        <p className="analysis-label">{guided ? `GUIDED WALKTHROUGH / STEP ${step + 1} OF 3` : 'PHYSICS-CALCULATED / ' + (result.provenance.category ?? 'synthetic').replace('_', ' ').toUpperCase() + ' INPUTS'}</p>
        <h3 ref={heading} tabIndex={-1} className={step === 1 ? 'analysis-sr-only' : undefined}>{step === 0 ? 'What happens during a blackout?' : step === 1 ? 'Where is the school vulnerable?' : 'What does our AI do?'}</h3>
      </div>
      {step === 0 && <OutageResult {...props} />}
      {step === 1 && <section aria-label="Failure Frontier analysis">
        {props.frontierWarning && <p className="analysis-notice" role="status">{props.frontierWarning}</p>}
        {frontier ? <FrontierChart frontier={frontier} result={result} /> : <div className="analysis-empty" role="status"><p>{props.frontierBusy ? 'Testing battery charge and blackout duration with the physics engine…' : 'Build the map to compare tested energy configurations.'}</p></div>}
        <div className="analysis-inline-actions"><button className="analysis-button" onClick={() => onFrontier()} disabled={props.frontierBusy}>{props.frontierBusy ? 'CALCULATING MAP…' : frontier ? 'RECALCULATE PHYSICS MAP' : 'BUILD PHYSICS MAP'}</button><button className="analysis-link" onClick={() => select(2)}>See what AI adds <span aria-hidden="true">→</span></button></div>
      </section>}
      {step === 2 && <FragilityAnalysis {...props} />}
      <details className="analysis-methodology"><summary>Methodology, provenance &amp; limits</summary>
        <p><strong>PHYSICS-CALCULATED</strong> results use a deterministic single-bus energy balance. <strong>AI-ESTIMATED</strong> scores come from FragilityNet. Inputs are labelled <strong>{(result.provenance.category ?? 'synthetic').replace('_', ' ').toUpperCase()}</strong>; this scenario is not live school or utility telemetry.</p>
        <p>Physics: {result.physics_version ?? result.model_version}. {prediction?.model_version || frontier?.model_version ? `AI: ${prediction?.model_version ?? frontier?.model_version}.` : 'AI has not been loaded for this analysis.'} Step: {result.input.step_minutes} minutes, with within-step events. Seed: {result.seed}.</p>
        <p>Run: {result.run_id}<br />Input hash: {result.input_hash}</p>
        {frontier && <p>Map: {frontier.summary.verified_cells} tested cells / {frontier.summary.physics_calls} physical runs. {frontier.summary.method}. Map run: {frontier.run_id}.</p>}
        <ul>{[...(result.assumptions ?? []), ...result.warnings].map((text, i) => <li key={i}>{text}</li>)}</ul>
        <p>Sources: {result.provenance.references?.join(', ') || 'No references supplied.'}</p>
        <p>The model does not predict when the city grid will fail. Neither result authorizes equipment deployment. No AC transients, voltage or protection analysis is performed. Tested ML sampling has not shown an acceleration advantage over the physical frontier method.</p>
      </details>
    </div>
    <footer className="analysis-footer">
      {guided ? <><span>Step {step + 1} of 3</span><div><button className="analysis-button" onClick={() => select(step - 1)} disabled={step === 0}>BACK</button><button className="analysis-button is-primary" onClick={() => step < 2 ? select(step + 1) : setGuided(false)}>{step < 2 ? 'NEXT STEP →' : 'FINISH WALKTHROUGH'}</button></div></>
        : <><span>Physics determines the outcome.</span><button className="analysis-button" data-testid="start-guide" onClick={() => select(0, true)}>START 3-STEP WALKTHROUGH <span aria-hidden="true">→</span></button></>}
    </footer>
  </dialog>
}
