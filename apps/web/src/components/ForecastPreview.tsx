import { useEffect, useRef, useState } from 'react'
import { intelligenceRequest } from '../lib/intelligenceApi'
import type { ForecastPreview as Preview } from '../lib/intelligenceContracts'
import { AnalysisDialog } from './AnalysisDialog'

export function ForecastPreview({ onClose }: { onClose: () => void }) {
  const [example, setExample] = useState('rat-march20')
  const [result, setResult] = useState<Preview | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const current = useRef<AbortController | null>(null)
  useEffect(() => () => current.current?.abort(), [])
  const run = async () => {
    current.current?.abort()
    const controller = new AbortController(); current.current = controller
    setBusy(true); setError(null)
    try {
      const value = await intelligenceRequest<Preview>('/api/v1/ml/energydna/forecast', { example_id: example }, controller.signal)
      if (value.horizon_hours !== 1 || value.connected_to_physics !== false || value.units !== 'whole-building average kW' || value.history_kw.length !== 168 || !Number.isFinite(value.baseline_kw) || (value.neural_kw !== null && !Number.isFinite(value.neural_kw))) throw new Error('Forecast provenance, horizon or units contract is invalid.')
      if (!controller.signal.aborted) setResult(value)
    } catch (cause) { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'Research forecast unavailable.') }
    finally { if (!controller.signal.aborted) setBusy(false) }
  }
  const history = result?.history_kw.slice(-48) ?? []
  const maximum = Math.max(1, ...history, result?.neural_kw ?? 0, result?.baseline_kw ?? 0, result?.recorded_actual_kw ?? 0)
  const position = (value: number) => 155 - value / maximum * 140
  return <AnalysisDialog title="Energy demand forecasting" label="ENERGYDNA / RESEARCH PREVIEW" onClose={onClose}>
    <h2>Learning a building’s<br />demand rhythm<span>.</span></h2>
    <p className="frontier-intro">A historical one-hour forecast on overseas BDG2 whole-building meters. Not a measured Kyrgyz school. Not connected to emergency critical-load physics.</p>
    <label className="forecast-selector">Recorded building example <select value={example} onChange={event => { current.current?.abort(); setBusy(false); setResult(null); setExample(event.target.value) }}>
      <option value="rat-march20">Rat · assembly · Francine</option><option value="silvia-march20">Rat · assembly · Silvia</option><option value="mouse-march20">Mouse · science · Micheal</option>
    </select></label>
    <button className="analysis-button" data-testid="run-forecast" disabled={busy} onClick={() => void run()}>{busy ? 'RUNNING GRU + BASELINE…' : 'RUN HISTORICAL FORECAST'}</button>
    {error && <p role="alert">{error}</p>}
    {result && <>
      <p className="model-identity">{result.building_id} · origin {result.forecast_origin_local} · source-local clock · horizon {result.horizon_hours} hour</p>
      <svg className="forecast-chart" viewBox="0 0 780 190" role="img" aria-label="Last 48 observed hours and the next-hour model forecasts with the recorded actual load">
        <line x1="22" x2="752" y1="155" y2="155" stroke="currentColor" opacity=".4" />
        <polyline fill="none" stroke="#a7d6c4" strokeWidth="2.5" points={history.map((v, i) => `${22 + i * 12.8},${position(v)}`).join(' ')} />
        <line x1="638" x2="638" y1="10" y2="155" stroke="currentColor" strokeDasharray="5 5" opacity=".5" />
        <circle cx="682" cy={position(result.baseline_kw)} r="5" fill="#e6bf80" />
        {result.neural_kw != null && <circle cx="711" cy={position(result.neural_kw)} r="5" fill="#b5c2ec" />}
        <circle cx="740" cy={position(result.recorded_actual_kw)} r="5" fill="#fff" />
        <text x="22" y="183">−48 h · observed history</text><text x="580" y="183">origin</text><text x="677" y="183">+1 h</text><text x="22" y="12">{maximum.toFixed(1)} kW</text>
      </svg>
      <div className="forecast-values">
        <section data-testid="forecast-neural"><p className="analysis-kicker">ENERGYDNA GRU / RESEARCH</p><h3>{result.neural_kw == null ? 'Unavailable' : `${result.neural_kw.toFixed(2)} kW`}</h3><small data-testid="forecast-model">{result.model_version ?? 'No model loaded'}</small></section>
        <section data-testid="forecast-baseline"><p className="analysis-kicker">PREFERRED METHOD</p><h3>{result.baseline_kw.toFixed(2)} kW</h3><p>Persistence · last observed hour</p></section>
        <section data-testid="forecast-actual"><p className="analysis-kicker">RECORDED HISTORICAL ACTUAL</p><h3>{result.recorded_actual_kw.toFixed(2)} kW</h3><p>Retrospective comparison only</p></section>
      </div>
      <p className="score-explanation">The GRU is genuinely trained, but persistence had lower validation MAE and remains preferred. The recorded target is never provided to the model. This is a one-hour forecast, not a 24-hour blackout forecast.</p>
      <details><summary>Source, attribution and limitations</summary><p>{result.attribution}</p><p>Source commit {result.source_commit}; subset SHA {result.source_subset_sha256}; example SHA {result.example_sha256}</p><p>{result.timestamp_basis}</p><ul>{result.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul><a href={result.license_url} target="_blank" rel="noreferrer">BDG2 attribution/share-alike license</a></details>
    </>}
  </AnalysisDialog>
}
