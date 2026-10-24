import { useCallback, useEffect, useRef, useState } from 'react'
import type { FrontierResult, PredictionResult, SimulationResult } from '../lib/contracts'
import type { SiteId } from '../features/sites'
import { simulationAdapter } from './simulationAdapter'

function validateResult(value: SimulationResult): SimulationResult {
  if (!value.schema_version?.startsWith('1.') || !value.input_hash || !Array.isArray(value.trace) || !value.trace.length ||
    value.trace.some(point => !Number.isFinite(point.battery_soc) || !Number.isFinite(point.critical_served_kw) || !Number.isFinite(point.elapsed_hours))) {
    throw new Error('Unsupported simulation response')
  }
  return value
}

export function useSchoolSimulation(siteId: SiteId) {
  const [result, setResult] = useState<SimulationResult | null>(null)
  const [index, setIndex] = useState(0)
  const [busy, setBusy] = useState(false)
  const [warning, setWarning] = useState('')
  const [frontier, setFrontier] = useState<FrontierResult | null>(null)
  const [frontierBusy, setFrontierBusy] = useState(false)
  const [frontierWarning, setFrontierWarning] = useState('')
  const [prediction, setPrediction] = useState<PredictionResult | null>(null)
  const [predictionBusy, setPredictionBusy] = useState(false)
  const [predictionWarning, setPredictionWarning] = useState('')
  const generation = useRef(0)
  const controller = useRef<AbortController | null>(null)
  const frontierController = useRef<AbortController | null>(null)
  const predictionController = useRef<AbortController | null>(null)
  const clear = useCallback(() => {
    generation.current += 1
    controller.current?.abort()
    frontierController.current?.abort()
    predictionController.current?.abort()
    setResult(null); setIndex(0); setWarning(''); setBusy(false); setFrontier(null); setFrontierBusy(false)
    setFrontierWarning(''); setPrediction(null); setPredictionBusy(false); setPredictionWarning('')
  }, [])
  useEffect(() => () => {
    generation.current += 1
    controller.current?.abort(); frontierController.current?.abort(); predictionController.current?.abort()
  }, [siteId])
  const run = useCallback(async () => {
    clear()
    if (siteId !== 'school') {
      setWarning('This archetype uses a synthetic visual rehearsal; no verified scenario is connected.')
      return
    }
    const id = generation.current
    const abort = new AbortController()
    controller.current = abort
    const timeout = window.setTimeout(() => abort.abort(), 10000)
    setBusy(true)
    try {
      const response = await fetch('/api/v1/simulations', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: abort.signal,
        body: JSON.stringify({ duration_hours: 16, provenance: { category: 'synthetic', references: ['docs/physics/MODEL.md'] } }),
      })
      if (!response.ok) throw new Error('Simulation service unavailable')
      const data = validateResult(await response.json())
      if (generation.current === id) setResult(data)
    } catch {
      if (generation.current === id) setWarning('Backend unavailable or response invalid. Synthetic visual rehearsal only; no calculated numerical result.')
    } finally {
      window.clearTimeout(timeout)
      if (generation.current === id) setBusy(false)
    }
  }, [siteId, clear])
  const loadFrontier = useCallback(async (includeMl = false) => {
    if (!result || frontierBusy) return
    const id = generation.current
    const abort = new AbortController()
    frontierController.current = abort
    const timeout = window.setTimeout(() => abort.abort(), includeMl ? 60000 : 15000)
    setFrontierBusy(true)
    setFrontierWarning('')
    try {
      const input = result.input
      const duration = input.duration_hours ?? result.summary.observed_duration_hours
      const hasProfiles = [input.solar?.profile_kw, input.grid?.profile_online,
        input.load?.critical_profile_kw, input.load?.noncritical_profile_kw].some(Boolean)
      const maximumHours = Math.min(48, hasProfiles ? duration : Math.max(24, duration))
      const response = await fetch('/api/v1/fragility/frontier', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        signal: abort.signal,
        body: JSON.stringify({ scenario: input, soc_points: 13, duration_points: 17, maximum_hours: maximumHours, include_ml: includeMl }),
      })
      if (!response.ok) throw new Error('Frontier unavailable')
      const data: FrontierResult = await response.json()
      if (!Array.isArray(data.trace) || !data.trace.length || data.trace.some(cell => !cell.physics_verified ||
        !Number.isFinite(cell.initial_soc) || !Number.isFinite(cell.duration_hours))) throw new Error('Unverified map')
      if (generation.current === id) setFrontier(data)
    } catch {
      if (generation.current === id) setFrontierWarning('The map could not be loaded. Your school calculation is still available. Retry the map or continue with the result.')
    } finally {
      window.clearTimeout(timeout)
      if (generation.current === id) setFrontierBusy(false)
    }
  }, [result, frontierBusy])
  const analyze = useCallback(async () => {
    if (!result || predictionBusy) return
    const id = generation.current
    const abort = new AbortController()
    predictionController.current = abort
    const timeout = window.setTimeout(() => abort.abort(), 60000)
    setPrediction(null); setPredictionBusy(true); setPredictionWarning('')
    try {
      const response = await fetch('/api/v1/fragility/predict', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: abort.signal,
        body: JSON.stringify(result.input),
      })
      if (!response.ok) throw new Error('AI unavailable')
      const data: PredictionResult = await response.json()
      if (!data.physics_verified || data.input_hash !== result.input_hash || !data.trace?.length ||
        (data.estimate && (!Number.isFinite(data.estimate.synthetic_failure_score) ||
          data.estimate.synthetic_failure_score < 0 || data.estimate.synthetic_failure_score > 1))) {
        throw new Error('Unsupported AI response')
      }
      if (generation.current === id) setPrediction(data)
    } catch {
      if (generation.current === id) setPredictionWarning('AI analysis is unavailable. The physics result and map remain valid. Retry when the model service is available.')
    } finally {
      window.clearTimeout(timeout)
      if (generation.current === id) setPredictionBusy(false)
    }
  }, [result, predictionBusy])
  const point = result?.trace[index]
  return { result, index, setIndex, point, busy, warning, clear, run, frontier, frontierBusy, frontierWarning, loadFrontier,
    prediction, predictionBusy, predictionWarning, analyze,
    visual: result ? simulationAdapter(result).visualStateAt(index) : null }
}
