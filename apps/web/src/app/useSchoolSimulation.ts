import { useCallback, useEffect, useRef, useState } from 'react'
import type { FrontierResult, SimulationResult } from '../lib/contracts'
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
  const generation = useRef(0)
  const controller = useRef<AbortController | null>(null)
  const clear = useCallback(() => {
    generation.current += 1
    controller.current?.abort()
    setResult(null); setIndex(0); setWarning(''); setBusy(false); setFrontier(null); setFrontierBusy(false)
  }, [])
  useEffect(() => () => { generation.current += 1; controller.current?.abort() }, [siteId])
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
    setFrontierBusy(true)
    try {
      const response = await fetch('/api/v1/fragility/frontier', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(includeMl ? 60000 : 15000),
        body: JSON.stringify({ scenario: { ...result.input, duration_hours: 24 }, soc_points: 13, duration_points: 17, maximum_hours: 24, include_ml: includeMl }),
      })
      if (!response.ok) throw new Error('Frontier unavailable')
      const data: FrontierResult = await response.json()
      if (!Array.isArray(data.trace) || data.trace.some(cell => !cell.physics_verified)) throw new Error('Unverified map')
      if (generation.current === id) setFrontier(data)
    } catch {
      if (generation.current === id) setWarning('Frontier unavailable. The displayed simulation trace remains calculated by physics.')
    } finally {
      if (generation.current === id) setFrontierBusy(false)
    }
  }, [result, frontierBusy])
  const point = result?.trace[index]
  return { result, index, setIndex, point, busy, warning, clear, run, frontier, frontierBusy, loadFrontier,
    visual: result ? simulationAdapter(result).visualStateAt(index) : null }
}
