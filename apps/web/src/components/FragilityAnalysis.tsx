import type { PhysicsPanelProps } from './PhysicsPanel'
import { conclusion, hours, percent } from './analysisFormat'

export function FragilityAnalysis({ result, frontier, frontierBusy, frontierWarning, onFrontier, prediction, predictionBusy, predictionWarning, onAnalyze }: PhysicsPanelProps) {
  const estimate = prediction?.estimate
  const candidates = frontier?.verified_candidates.filter(item => item.physics_verified) ?? []
  const warnings = [...new Set([...(prediction?.warnings ?? []), ...(estimate?.warnings ?? [])])]
  return <section className="fragility-analysis" aria-label="FragilityNet AI contribution">
    <p className="chapter-lede">FragilityNet examines energy-system configurations and identifies scenarios worth testing. The physics engine checks whether critical power actually survives.</p>
    <div className="ai-comparison" data-testid="ai-comparison">
      <div className="ai-estimate"><p className="analysis-label">AI-ESTIMATED / FRAGILITYNET</p>
        <h4>{predictionBusy ? 'Analyzing your scenario…' : estimate ? estimate.predicted_failure ? 'FAILURE' : 'SURVIVAL' : prediction ? 'MODEL UNAVAILABLE' : 'Ready to test your scenario'}</h4>
        {estimate ? <><p className="ai-score">Synthetic failure score <strong data-testid="ai-score">{estimate.synthetic_failure_score.toFixed(4)}</strong></p><p className="model-version">Model: {estimate.model_version}</p></> : <p>{prediction ? 'No AI estimate was returned. The physical calculation remains available.' : 'Run the trained model on the exact inputs used for this school calculation.'}</p>}
        <button className="analysis-button is-primary" data-testid="run-ai" onClick={onAnalyze} disabled={predictionBusy}>{predictionBusy ? 'RUNNING AI ANALYSIS…' : estimate ? 'RUN AI ANALYSIS AGAIN' : 'RUN AI ANALYSIS'} <span aria-hidden="true">↗</span></button>
      </div>
      <div className="ai-physics"><p className="analysis-label">PHYSICS-CALCULATED / AUTHORITATIVE</p>
        <h4>{(prediction ?? result).summary.survived_full_window ? `SURVIVES ${hours((prediction ?? result).summary.observed_duration_hours)}` : (prediction ?? result).summary.critical_survival_hours !== null ? `FAILURE AT ${hours((prediction ?? result).summary.critical_survival_hours!)}` : 'CRITICAL POWER FAILS'}</h4>
        <p>{conclusion(prediction ?? result)}</p>
        <p>{prediction ? 'The endpoint independently ran physics for this exact input.' : 'Your school’s existing physical result. AI analysis will also independently run the simulator.'}</p>
        <p className="model-version">Physics: {result.physics_version ?? result.model_version}</p>
      </div>
    </div>
    {predictionWarning && <p className="analysis-notice" role="status">{predictionWarning}</p>}
    {estimate && <div className="ai-result-note" role="status">
      <p>{estimate.predicted_failure === !prediction!.summary.survived_full_window ? 'AI and physics agree for this scenario.' : 'AI and physics disagree for this scenario. Use the physics result.'}</p>
      {estimate.outside_training_domain && <p data-testid="ai-ood"><strong>OUTSIDE TRAINING DOMAIN.</strong> At least one input feature is outside the model’s training range. Use the physical result.</p>}
      {estimate.high_uncertainty && <p data-testid="ai-uncertainty"><strong>HIGH MODEL UNCERTAINTY.</strong> The estimate requires physical verification.</p>}
    </div>}
    {!!warnings.length && <ul className="analysis-warnings" aria-label="Model warnings">{warnings.map(text => <li key={text}>{text}</li>)}</ul>}
    <p className="score-explanation">This score describes the model’s assessment on synthetic simulation scenarios. It is not the probability of a real-world grid outage. Model predictions cannot authorize equipment for deployment.</p>
    <section className="ai-test-cases" aria-label="AI-suggested scenarios">
      <h4>Let AI choose additional test cases</h4>
      <p>The map’s colors come from physics. FragilityNet selects configurations near its estimated failure boundary, then the simulator checks each one. White outlined circles identify those checked tests.</p>
      <button className="analysis-button" data-testid="verify-ml" onClick={() => onFrontier(true)} disabled={frontierBusy}>{frontierBusy ? 'CHECKING SUGGESTED SCENARIOS…' : 'SHOW AI-SUGGESTED TEST CASES'} <span aria-hidden="true">↗</span></button>
      {frontierWarning && <p className="analysis-notice" role="status">{frontierWarning}</p>}
      {frontier?.model_version ? <div data-testid="verified-ml" role="status"><p>FragilityNet suggested <strong>{candidates.length} scenarios</strong> for additional checking. All <strong>{candidates.length}</strong> were independently evaluated by the physics engine.</p><p>Return to Failure Frontier to inspect the white circles or hide them with the overlay control.</p>
        <details><summary>Inspect the verified test cases</summary><ul className="candidate-list">{candidates.map((cell, i) => <li key={i}>{percent(cell.initial_soc)} charge · {hours(cell.duration_hours)} blackout · Physics: {cell.failed ? 'failure' : 'survival'}.{cell.outside_training_domain && ' AI input outside training domain.'}</li>)}</ul></details></div>
        : frontier?.warnings.some(text => text.includes('unavailable')) && <p className="analysis-notice" data-testid="proposals-unavailable" role="status">AI suggestions are unavailable. The physical map continues to work.</p>}
      <p className="score-explanation">These are synthetic test cases, not measured historical blackouts. Their count does not measure model accuracy. The AI sampler is not claimed to be faster than the physical map.</p>
    </section>
  </section>
}
