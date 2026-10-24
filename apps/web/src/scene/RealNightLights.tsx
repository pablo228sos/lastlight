/**
 * LASTLIGHT — physically anchored lamp contribution for real WebGL night shots.
 * These coordinates are a subset of the EXISTING CityFabric lampSites.
 * Point-light budget is capped at 4, with shadows disabled for laptop demo.
 * No extra or independent lights are active when the visual grid is out.
 */
import type { VisualRehearsalState } from '../app/useMissionState'

const EXISTING_NEAR_SCHOOL_LAMPS: Array<[number,number]> = [
  [-18,55], [31,55], [-18,-33], [31,-33],
]
export function RealNightLights({visual,lowPower}:{
  visual:VisualRehearsalState;lowPower:boolean
}){
  if(lowPower) return null
  return <>
    {EXISTING_NEAR_SCHOOL_LAMPS.map(([x,z])=>
      <pointLight key={x+'/'+z} position={[x,5.1,z]} color="#ffbd7b"
        intensity={visual.gridConnected?12:0} distance={22} decay={2}/>
    )}
  </>
}
