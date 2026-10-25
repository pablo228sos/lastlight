import { useCallback, useEffect, useRef, useState } from 'react'
import type { ComparisonResult, SimulationResult } from '../lib/contracts'
import { requestBaseline, requestComparison, verifiedBaseline, verifiedComparison } from '../lib/physicsApi'
import { traceInterval, validateComparison } from '../lib/physics'
import { requestDesignSearch, type DesignSearchResult } from '../lib/designSearch'
import type { VisualRehearsalState } from './useMissionState'

export type PhysicsSource = 'live' | 'offline'
export type RunStatus = 'idle' | 'loading' | 'ready' | 'error'
const speeds = [720, 1440, 2880] as const

export function usePhysicsRun() {
  const [status, setStatus] = useState<RunStatus>('idle')
  const [source, setSource] = useState<PhysicsSource | null>(null)
  const [baseline, setBaseline] = useState<SimulationResult | null>(null)
  const [comparison, setComparison] = useState<ComparisonResult | null>(null)
  const [selectedRun, setSelectedRun] = useState<'baseline' | 'upgraded'>('baseline')
  const [error, setError] = useState<string | null>(null)
  const [compareError, setCompareError] = useState<string | null>(null)
  const [compareLoading, setCompareLoading] = useState(false)
  const [designSearch, setDesignSearch] = useState<DesignSearchResult | null>(null)
  const [designSearchLoading, setDesignSearchLoading] = useState(false)
  const [designSearchError, setDesignSearchError] = useState<string | null>(null)
  const [elapsedHours, setElapsedHours] = useState(0)
  const elapsedRef = useRef(0)
  const [playing, setPlaying] = useState(false)
  const [speedIndex, setSpeedIndex] = useState(2)
  const requestRef = useRef<AbortController | null>(null)
  const designSearchRef = useRef<AbortController | null>(null)
  const designSearchSerial = useRef(0)
  const serial = useRef(0)
  const result = selectedRun === 'upgraded' && comparison ? comparison.upgraded : baseline

  const reset = useCallback(() => {
    serial.current += 1
    requestRef.current?.abort()
    designSearchRef.current?.abort()
    designSearchSerial.current += 1
    requestRef.current = null
    setStatus('idle'); setSource(null); setBaseline(null); setComparison(null)
    setSelectedRun('baseline'); setError(null); setCompareError(null); setCompareLoading(false)
    setDesignSearch(null); setDesignSearchLoading(false); setDesignSearchError(null)
    elapsedRef.current = 0
    setElapsedHours(0); setPlaying(false)
  }, [])

  const begin = useCallback(async (mode: PhysicsSource) => {
    const current = ++serial.current
    requestRef.current?.abort()
    designSearchRef.current?.abort()
    designSearchSerial.current += 1
    const controller = new AbortController()
    requestRef.current = controller
    setStatus('loading'); setSource(null); setBaseline(null); setComparison(null)
    setSelectedRun('baseline'); setError(null); setCompareError(null); elapsedRef.current = 0; setElapsedHours(0); setPlaying(false)
    setDesignSearch(null); setDesignSearchLoading(false); setDesignSearchError(null)
    try {
      const value = mode === 'live' ? await requestBaseline(controller.signal) : verifiedBaseline()
      if (current !== serial.current) return
      setBaseline(value); setSource(mode); setStatus('ready')
      setPlaying(!window.matchMedia('(prefers-reduced-motion: reduce)').matches)
    } catch (cause) {
      if (current !== serial.current) return
      setStatus('error')
      setError(cause instanceof Error ? cause.message : 'Physics result could not be loaded.')
    }
  }, [])

  const compare = useCallback(async () => {
    if (!baseline || !source || compareLoading) return
    const current = ++serial.current
    requestRef.current?.abort()
    const controller = new AbortController()
    requestRef.current = controller
    setCompareLoading(true); setCompareError(null)
    try {
      const value = source === 'live' ? await requestComparison(controller.signal) : verifiedComparison()
      validateComparison(value)
      if (value.baseline.input_hash !== baseline.input_hash) throw new Error('Comparison baseline does not match the active simulation.')
      if (current !== serial.current) return
      setComparison(value); setSelectedRun('upgraded'); elapsedRef.current = 0; setElapsedHours(0); setPlaying(false)
    } catch (cause) {
      if (current !== serial.current) return
      setCompareError(cause instanceof Error ? cause.message : 'Physics comparison could not be loaded.')
    } finally {
      if (current === serial.current) setCompareLoading(false)
    }
  }, [baseline, source, compareLoading])

  const searchDesign = useCallback(async () => {
    if (!baseline || source !== 'live' || designSearchLoading) return
    designSearchRef.current?.abort()
    const controller = new AbortController()
    designSearchRef.current = controller
    const current = ++designSearchSerial.current
    const timeout = window.setTimeout(() => controller.abort(), 20_000)
    setDesignSearchLoading(true); setDesignSearchError(null)
    try {
      const value = await requestDesignSearch(baseline, controller.signal)
      if (current !== designSearchSerial.current) return
      setDesignSearch(value)
    } catch (cause) {
      if (current !== designSearchSerial.current) return
      setDesignSearchError(cause instanceof Error ? cause.message : 'Official design search could not be loaded.')
    } finally {
      window.clearTimeout(timeout)
      if (current === designSearchSerial.current) setDesignSearchLoading(false)
    }
  }, [baseline, source, designSearchLoading])

  useEffect(() => () => { serial.current += 1; designSearchSerial.current += 1; requestRef.current?.abort(); designSearchRef.current?.abort() }, [])
  useEffect(() => {
    if (!playing || !result) return
    let frame = 0
    let previous = performance.now()
    const tick = (now: number) => {
      const delta = Math.min((now - previous) / 1000, .25)
      previous = now
      const next = Math.min(result.input.duration_hours, elapsedRef.current + delta * speeds[speedIndex] / 3600)
      elapsedRef.current = next
      setElapsedHours(next)
      if (next >= result.input.duration_hours) { setPlaying(false); return }
      frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [playing, result, speedIndex])
  const seek = useCallback((hours: number) => {
    if (!result) return
    elapsedRef.current = Math.max(0, Math.min(result.input.duration_hours, hours))
    setElapsedHours(elapsedRef.current)
    setPlaying(false)
  }, [result])
  const chooseRun = useCallback((choice: 'baseline' | 'upgraded') => {
    if (choice === 'upgraded' && !comparison) return
    setSelectedRun(choice); elapsedRef.current = 0; setElapsedHours(0); setPlaying(false)
  }, [comparison])
  const sample = result ? traceInterval(result, elapsedHours) : null
  const visual: VisualRehearsalState | null = sample ? {
    kind: 'physics_trace', gridConnected: sample.row.grid_online,
    noncriticalLit: sample.row.noncritical_served_kw > 1e-9,
    criticalLit: sample.row.unserved_critical_kw <= 1e-9 && sample.row.critical_served_kw + 1e-9 >= sample.row.critical_demand_kw,
    event: sample.row.unserved_critical_kw > 1e-9 ? 'CRITICAL_UNSERVED' : sample.row.grid_online ? 'GRID_RESTORED' : 'GRID_LOST',
  } : null
  return { status, source, baseline, comparison, selectedRun, result, error, compareError, compareLoading,
    designSearch, designSearchLoading, designSearchError, searchDesign,
    elapsedHours, playing, speed: speeds[speedIndex], sample, visual, begin, compare, reset, seek, chooseRun,
    setPlaying, cycleSpeed: () => setSpeedIndex(value => (value + 1) % speeds.length) }
}
