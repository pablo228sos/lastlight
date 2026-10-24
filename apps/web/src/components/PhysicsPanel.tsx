import { useState } from 'react'
import type { FrontierResult, PredictionResult, SimulationResult } from '../lib/contracts'
import { SchoolAnalysisReport } from './SchoolAnalysisReport'
import { horizon, hours, number, percent } from './analysisFormat'
import './physics.css'

export type PhysicsPanelProps = {
  result: SimulationResult; index: number; onIndex: (index: number) => void
  frontier: FrontierResult | null; frontierBusy: boolean; frontierWarning: string
  onFrontier: (includeMl?: boolean) => void
  prediction: PredictionResult | null; predictionBusy: boolean; predictionWarning: string
  onAnalyze: () => void
}

export function PhysicsPanel(props: PhysicsPanelProps) {
  const { result, index, onIndex, onFrontier } = props
  const [step, setStep] = useState<number | null>(null)
  const point = result.trace[index]
  const failure = result.trace.findIndex(item => item.status === 'critical_failure')
  const open = (next: number) => {
    setStep(next)
    if (next === 1 && !props.frontier) onFrontier()
  }
  return <>
    <aside className="physics-panel" data-testid="physics-panel" aria-label="Calculated school scenario">
      <p className="analysis-label">PHYSICS-CALCULATED <span>School</span></p>
      <h2>Can this school survive a {number(horizon(result))}-hour blackout?</h2>
      <div className={'compact-verdict ' + (result.summary.survived_full_window ? 'is-survival' : 'is-failure')}>
        <strong>{result.summary.survived_full_window ? 'YES' : 'NO'}</strong>
        <div><span>{result.summary.survived_full_window ? 'Critical power maintained for' : 'First critical power failure at'}</span>
          <button className="failure-jump" data-testid="jump-failure" disabled={failure < 0}
            aria-label={failure < 0 ? 'No critical failure observed' : 'Show the first critical failure in the scene'}
            onClick={() => onIndex(failure)}><b data-testid="first-failure">{hours(result.summary.critical_survival_hours ?? horizon(result))}</b>{failure >= 0 && <span aria-hidden="true"> ↗</span>}</button>
        </div>
      </div>
      <p className="compact-context">{result.input.battery?.initial_soc !== undefined && `${percent(result.input.battery.initial_soc)} starting charge · `}{hours(horizon(result))} outage</p>
      <div className="compact-live"><span data-testid="critical-status">{point.unserved_critical_kw > 1e-9 ? 'CRITICAL LOAD UNSERVED' : 'CRITICAL LOAD SERVED'}</span><span data-testid="battery-soc">{(point.battery_soc * 100).toFixed(1)}% SOC</span></div>
      <button className="analysis-button is-primary" data-testid="open-analysis" onClick={() => open(0)}>EXPLORE THE RESULT <span aria-hidden="true">↗</span></button>
      <button className="analysis-link" data-testid="show-frontier" onClick={() => open(1)}>Open Failure Frontier <span aria-hidden="true">→</span></button>
    </aside>
    {step !== null && <SchoolAnalysisReport {...props} initialStep={step} onClose={() => setStep(null)} />}
  </>
}
