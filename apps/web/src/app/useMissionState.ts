import { useCallback, useState } from 'react'
import type { SiteId } from '../features/sites'

export type ScenePhase = 'INTRO' | 'DESCENT' | 'DISTRICT' | 'SITE' | 'INSPECT' | 'BLACKOUT'
export type SceneLayer = 'architecture' | 'power'
export type CameraShotId = 'orbital' | 'corridor' | 'district' | 'facility' | 'equipment' | 'orbit'
export type CameraShot = { id: CameraShotId; position: [number, number, number]; target: [number, number, number]; duration: number; ease: string }
export type VisualRehearsalState = { kind: 'synthetic_visual_rehearsal'; gridConnected: boolean; noncriticalLit: boolean; criticalLit: boolean; event: 'NONE' | 'GRID_LOST' | 'GRID_RESTORED' }

export const SHOTS: Record<CameraShotId, CameraShot> = {
  orbital: { id: 'orbital', position: [8, 175, 260], target: [0, 0, 0], duration: 0, ease: 'power2.inOut' },
  corridor: { id: 'corridor', position: [112, 86, 118], target: [10, 0, 3], duration: 1.7, ease: 'power2.inOut' },
  district: { id: 'district', position: [81, 63, 83], target: [6, 1, 2], duration: 1.6, ease: 'power2.out' },
  facility: { id: 'facility', position: [65, 39, 58], target: [13, 3, 7], duration: 1.8, ease: 'power3.inOut' },
  equipment: { id: 'equipment', position: [53, 26, 41], target: [16, 5, 7], duration: 1.5, ease: 'power3.inOut' },
  orbit: { id: 'orbit', position: [47, 37, -37], target: [13, 4, 7], duration: 2, ease: 'power2.inOut' },
}

export interface SimulationTraceStep {
  tSeconds: number; gridConnected: boolean; pvKw: number; criticalDemandKw: number
  noncriticalDemandKw: number; servedCriticalKw: number; servedNoncriticalKw: number
  batterySoc: number; batteryEnergyKwh: number; batteryDischargeKw: number
  unservedCriticalKwhCumulative: number
  events: Array<'GRID_LOST' | 'LOAD_SHED' | 'BATTERY_MIN_SOC' | 'CRITICAL_UNSERVED' | 'GRID_RESTORED'>
}
export interface SimulationTrace {
  runId: string; status: 'physics_verified' | 'synthetic_visual_rehearsal'; scenarioId: string
  assumptions: string[]; provenance: Record<string, string>; steps: SimulationTraceStep[]
}
export interface SceneAdapter { visualStateAt(index: number): VisualRehearsalState; canShowPhysics: boolean }
export const rehearsalAdapter: SceneAdapter = {
  canShowPhysics: false,
  visualStateAt(index) { return index === 0
    ? { kind: 'synthetic_visual_rehearsal', gridConnected: true, noncriticalLit: true, criticalLit: true, event: 'NONE' }
    : { kind: 'synthetic_visual_rehearsal', gridConnected: false, noncriticalLit: false, criticalLit: true, event: 'GRID_LOST' }
  },
}

export function useMissionState() {
  const [phase, setPhase] = useState<ScenePhase>('INTRO')
  const [siteId, setSiteId] = useState<SiteId>('school')
  const [layer, setLayer] = useState<SceneLayer>('architecture')
  const [shot, setShot] = useState<CameraShotId>('orbital')
  const [paused, setPaused] = useState(false)
  const [visualStep, setVisualStep] = useState(0)
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  const enter = useCallback(() => { setPaused(false); setPhase('DESCENT'); setShot('corridor') }, [])
  const skip = useCallback(() => { setPaused(false); setPhase('DISTRICT'); setShot('district') }, [])
  const selectSite = useCallback((id: SiteId) => { setSiteId(id); setPhase('SITE'); setShot('facility') }, [])
  const inspect = useCallback(() => { setPhase('INSPECT'); setShot('equipment'); setLayer('power') }, [])
  const orbit = useCallback(() => { setPhase('INSPECT'); setShot('orbit') }, [])
  const disconnect = useCallback(() => { setPhase('BLACKOUT'); setVisualStep(1) }, [])
  const reset = useCallback(() => { setVisualStep(0); setPhase('INSPECT'); setShot('facility') }, [])
  const returnCity = useCallback(() => { setVisualStep(0); setLayer('architecture'); setPhase('DISTRICT'); setShot('district') }, [])
  return { phase, setPhase, siteId, setSiteId, layer, setLayer, shot, setShot, paused, setPaused,
    visualStep, visual: rehearsalAdapter.visualStateAt(visualStep), evidenceOpen, setEvidenceOpen,
    enter, skip, selectSite, inspect, orbit, disconnect, reset, returnCity }
}
