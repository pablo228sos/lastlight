import { useCallback, useEffect, useRef, useState } from 'react'
import type { SimulationResult } from '../lib/contracts'
import { requestAssessment, type Assessment } from '../lib/intelligenceApi'
import { AnalysisDialog } from './AnalysisDialog'

export function ResilienceAnalysis({ active, onClose }: { active: SimulationResult; onClose: () => void }) {
  const [analysis, setAnalysis] = useState<Assessment | null>(null)
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const request = useRef<AbortController | null>(null)
  const perform = useCallback(async (controller: AbortController) => {
    try { const value = await requestAssessment(active, controller.signal); if (!controller.signal.aborted) setAnalysis(value) }
    catch (cause) { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'AI analysis unavailable.') }
    finally { if (!controller.signal.aborted) setBusy(false) }
  }, [active])
  const run = () => {
    request.current?.abort()
    const controller = new AbortController(); request.current = controller
    setBusy(true); setError(null); void perform(controller)
  }
  useEffect(() => {
    const controller = new AbortController(); request.current = controller
    void requestAssessment(active, controller.signal)
      .then(value => { if (!controller.signal.aborted) setAnalysis(value) })
      .catch(cause => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'AI analysis unavailable.') })
      .finally(() => { if (!controller.signal.aborted) setBusy(false) })
    return () => controller.abort()
  }, [active])
  const physical = analysis?.physics ?? active
  const estimate = analysis?.neural.estimate
  const summary = physical.summary
  return <AnalysisDialog title="AI resilience analysis" label="SCHOOL / PHYSICS + FRAGILITYNET" onClose={onClose}>
    <h2>One scenario.<br />Two perspectives<span>.</span></h2>
    <p className="frontier-intro">A neural estimate examines the same resolved inputs. The deterministic simulation decides whether critical demand is served.</p>
    <div className="analysis-columns">
      <section className="analysis-physical"><p className="analysis-kicker">PHYSICS-VERIFIED RESULT</p>
        <h3 data-testid="ai-physical-verdict">{summary.survived_full_window ? `Sustained for ${summary.observed_duration_hours} hours` : `Failure at ${summary.critical_survival_hours?.toFixed(2)} hours`}</h3>
        <dl className="analysis-facts"><div><dt>Outage window</dt><dd>{physical.input.duration_hours} h</dd></div><div><dt>Initial battery charge</dt><dd>{(physical.input.battery.initial_soc * 100).toFixed(0)}%</dd></div><div><dt>Battery capacity</dt><dd>{physical.input.battery.capacity_kwh} kWh</dd></div><div><dt>Unserved critical energy</dt><dd>{summary.unserved_critical_kwh.toFixed(3)} kWh</dd></div></dl>
        <p>{summary.survived_full_window ? 'No critical failure inside the exclusive observation window.' : 'Critical demand is not fully supplied before the observation window ends.'}</p>
        <small>{physical.model_version} · schema {physical.schema_version}</small>
      </section>
      <section className="analysis-neural"><p className="analysis-kicker">AI ESTIMATE</p>
        <h3>{busy ? 'Examining scenario…' : estimate ? estimate.predicted_failure ? 'Failure predicted' : 'Survival predicted' : analysis ? 'Model unavailable' : 'Request not completed'}</h3>
        {estimate && <><p className="analysis-score">Synthetic failure score <strong data-testid="ai-score">{estimate.synthetic_failure_score.toFixed(4)}</strong></p><p data-testid="ai-model" className="model-identity">{analysis?.neural.model_version}</p><p className="analysis-agreement">{estimate.predicted_failure === !summary.survived_full_window ? 'AI and physics agree for this scenario.' : 'AI and physics disagree. Use the physical result.'}</p>
          <p className="analysis-notice" data-testid="ai-ood">{estimate.outside_training_domain ? 'Outside training domain: at least one input exceeds the training range.' : 'No feature-range OOD flag. This does not establish real-world validity.'}</p>
          <p>{estimate.high_uncertainty ? 'High model uncertainty: physical verification is required.' : 'No threshold-margin uncertainty flag. This is a heuristic, not a confidence interval.'}</p></>}
        {analysis && !estimate && <p>Physics remains available. No neural verdict is presented.</p>}
        <button className="analysis-button" disabled={busy} onClick={() => void run()}>{busy ? 'RUNNING REAL MODEL…' : 'RUN ANALYSIS AGAIN'}</button>
        {busy && <button className="analysis-button" onClick={() => { request.current?.abort(); setBusy(false); setError('Analysis cancelled. Physical result retained.') }}>CANCEL ANALYSIS</button>}
        {error && <p role="alert">{error}</p>}
      </section>
    </div>
    <p className="score-explanation">The AI estimate is based on synthetic training scenarios. It is not the real-world probability of a city power outage. Physics remains authoritative; neither result grants engineering clearance.</p>
    {analysis?.neural.warnings.length ? <details><summary>Assumptions, provenance and model warnings</summary><ul>{[...physical.warnings, ...analysis.neural.warnings].map((warning, index) => <li key={index}>{warning}</li>)}</ul><p>Input hash: {physical.input_hash}</p><p>{physical.provenance.category} · {physical.provenance.references.join(' · ')}</p></details> : null}
  </AnalysisDialog>
}
