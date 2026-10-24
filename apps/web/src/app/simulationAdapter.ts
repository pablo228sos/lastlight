import type { SimulationResult } from '../lib/contracts'
import type { SceneAdapter } from './useMissionState'

export function simulationAdapter(result: SimulationResult): SceneAdapter {
  return {
    canShowPhysics: true,
    visualStateAt(index) {
      const point = result.trace[Math.min(Math.max(index, 0), result.trace.length - 1)]
      return {
        kind: 'physics_calculated', gridConnected: point.grid_online,
        noncriticalLit: point.noncritical_served_kw > 1e-9,
        criticalLit: point.unserved_critical_kw <= 1e-9,
        event: point.grid_online ? 'GRID_RESTORED' : 'GRID_LOST',
      }
    },
  }
}
