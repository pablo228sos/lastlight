/**
 * LASTLIGHT / HERO SCHOOL — source-locked, real-time architectural detail.
 * This is decorative geometry only: no new building volume, site relocation,
 * solar modules, equipment/hotspot changes or independent electrical physics.
 * Use the incoming VisualRehearsalState for every illuminated surface.
 */
import { useLayoutEffect, useRef } from 'react'
import { Object3D, type InstancedMesh } from 'three'
import type { VisualRehearsalState } from '../app/useMissionState'

type Part = readonly [number, number, number, number, number, number]
function Batches({ parts, color, roughness = .84, metalness = 0 }: {
  parts: Part[]; color: string; roughness?: number; metalness?: number
}) {
  const mesh = useRef<InstancedMesh>(null)
  useLayoutEffect(() => {
    const o = new Object3D()
    parts.forEach(([x,y,z,w,h,d],i) => {
      o.position.set(x,y,z); o.scale.set(w,h,d); o.updateMatrix()
      mesh.current?.setMatrixAt(i,o.matrix)
    })
    if (mesh.current) { mesh.current.instanceMatrix.needsUpdate = true; mesh.current.computeBoundingSphere() }
  },[parts])
  if (!parts.length) return null
  return <instancedMesh ref={mesh} args={[undefined,undefined,parts.length]} castShadow={false} receiveShadow={false}>
    <boxGeometry args={[1,1,1]}/>
    <meshStandardMaterial color={color} roughness={roughness} metalness={metalness}/>
  </instancedMesh>
}

const FRONT_POSITIONS: Array<[number,number]> = [-11,-7,7,11].flatMap(x=>[2.1,5.6].map(y=>[x,y]))
const EMERGENCY_POSITIONS: Array<[number,number]> = [11.8,15,18.2].map(x=>[x,3.4])

const windowBacking: Part[] = [
  ...FRONT_POSITIONS.map(([x,y]):Part => [x,y,13.143,2.15,1.68,.12]),
  ...EMERGENCY_POSITIONS.map(([x,y]):Part => [x,y,15.633,2.30,2.15,.13]),
]
const windowMullions: Part[] = [
  ...FRONT_POSITIONS.map(([x,y]):Part => [x,y,13.258,.065,1.41,.085]),
  ...EMERGENCY_POSITIONS.map(([x,y]):Part => [x,y,15.763,.067,1.88,.085]),
]
const windowFrameVertical: Part[] = [
  ...FRONT_POSITIONS.flatMap(([x,y]):Part[]=> [-.99,.99].map(dx=>[x+dx,y,13.255,.10,1.64,.13])),
  ...EMERGENCY_POSITIONS.flatMap(([x,y]):Part[]=>[-1.08,1.08].map(dx=>[x+dx,y,15.752,.11,2.1,.13])),
]
const windowFrameHorizontal: Part[] = [
  ...FRONT_POSITIONS.flatMap(([x,y]):Part[]=>[-.77,.77].map(dy=>[x,y+dy,13.254,2.10,.095,.13])),
  ...EMERGENCY_POSITIONS.flatMap(([x,y]):Part[]=>[-1.01,1.01].map(dy=>[x,y+dy,15.751,2.3,.105,.14])),
]
const windowSills: Part[] = [
  ...FRONT_POSITIONS.map(([x,y]):Part=>[x,y-.9,13.37,2.38,.12,.32]),
  ...EMERGENCY_POSITIONS.map(([x,y]):Part=>[x,y-1.16,15.86,2.52,.14,.34]),
]
const windowMidrails: Part[] = [
  ...FRONT_POSITIONS.map(([x,y]):Part=>[x,y-.21,13.249,2.10,.055,.07]),
  ...EMERGENCY_POSITIONS.map(([x,y]):Part=>[x,y-.24,15.745,2.24,.060,.07]),
]

// Precise façade-only parts, no alteration of the original wall boxes.
const pilasters: Part[] = [-14.75,-5,5,14.75].map(x=>[x,4.04,13.235,.36,7.85,.31])
const facadeJoints: Part[] = [
  [0,.60,13.236,30,.095,.18],
  [0,7.88,13.236,30,.16,.23],
  [0,4.03,13.228,29.9,.095,.19],
  [15.7,.48,15.659,9.85,.12,.23],
  [15.7,5.98,15.663,9.85,.16,.24],
]
const annexCornerReturns: Part[] = [
  [10.82,3.05,15.72,.29,5.92,.27],
  [20.58,3.05,15.72,.29,5.92,.27],
]
const roofEdgeDetail: Part[] = [
  [0,8.69,13.55,31.0,.28,.24],
  [0,8.69,-1.55,31,.28,.24],
  [-15.53,8.69,6,.25,.28,15.4],
  [15.53,8.69,6,.25,.28,15.4],
  [15.7,6.82,15.72,10.7,.24,.24],
  [20.97,6.82,11,.24,.24,9.8],
]
const roofDrainAndFittings: Part[] = [
  [-13.8,4.05,13.38,.11,7.58,.15],
  [13.8,4.05,13.38,.11,7.58,.15],
  [20.83,3.18,14.15,.10,5.76,.12],
]

function SchoolEntrance({ lit }: { lit: boolean }) {
  return <group>
    {/* The original entrance, its door, canopy posts and footprint remain unchanged. */}
    <mesh position={[0,2.18,13.24]}>
      <boxGeometry args={[4.55,4.04,.13]}/>
      <meshStandardMaterial color="#15282e" metalness={.42} roughness={.37}/>
    </mesh>
    <mesh position={[0,2.16,13.325]}>
      <boxGeometry args={[4.24,3.72,.075]}/>
      <meshStandardMaterial color="#263b45" metalness={.18} roughness={.25}
        emissive="#cf9857" emissiveIntensity={lit ? .20 : 0}/>
    </mesh>
    {[-1.38,0,1.38].map(x=><mesh key={'door-divider-'+x} position={[x,2.15,13.40]}>
      <boxGeometry args={[.07,3.77,.082]}/>
      <meshStandardMaterial color="#a0b1ad" metalness={.72} roughness={.3}/>
    </mesh>)}
    <mesh position={[0,4.08,13.39]}>
      <boxGeometry args={[4.4,.11,.10]}/>
      <meshStandardMaterial color="#c1c4b8" roughness={.79}/>
    </mesh>
    {[-1.95,1.95].map(x=><mesh key={'doorhandle-'+x} position={[x,1.8,13.48]}>
      <boxGeometry args={[.075,.56,.08]}/>
      <meshStandardMaterial color="#cad0c6" metalness={.8} roughness={.27}/>
    </mesh>)}
    {/* Side trim and a realistic soffit, attached to existing canopy. */}
    <mesh position={[0,4.45,17.0]}>
      <boxGeometry args={[7.25,.14,.20]}/>
      <meshStandardMaterial color="#a0aaa3" metalness={.3} roughness={.58}/>
    </mesh>
    <mesh position={[0,4.47,16.0]}>
      <boxGeometry args={[6.70,.06,2.5]}/>
      <meshStandardMaterial color="#5a6a67" roughness={.74}/>
    </mesh>
    {/* Fixture only emits when school noncritical supply is on. */}
    <mesh position={[0,4.37,16.35]}>
      <boxGeometry args={[3.55,.045,.20]}/>
      <meshStandardMaterial color={lit?'#f1c58a':'#334245'} emissive="#ffc47a"
        emissiveIntensity={lit ? 1.15 : 0} roughness={.43} toneMapped={false}/>
    </mesh>
    <pointLight position={[0,3.8,16.5]} color="#ffd1a0" intensity={lit?9:0} distance={10} decay={2}/>
    {/* Drainage and side-facing canopy frame; no new floating mass. */}
    {[-3.52,3.52].map(x=><mesh key={'canopy-edge-'+x} position={[x,4.48,16]}>
      <boxGeometry args={[.14,.22,2.6]}/>
      <meshStandardMaterial color="#8b9e9a" roughness={.65} metalness={.35}/>
    </mesh>)}
  </group>
}

function SchoolEquipmentDetails({ powerVisible, criticalLit }: { powerVisible: boolean; criticalLit: boolean }) {
  return <group>
    {/* Cabinets at their ORIGINAL positions: x=19.4 and x=15.7, z=3.2. */}
    {[19.4,15.7].map((x,i)=><group key={'cabinet-'+x}>
      <mesh position={[x,2.40,4.20]}>
        <boxGeometry args={[2.18,.10,.12]}/>
        <meshStandardMaterial color="#96a9a5" roughness={.6} metalness={.54}/>
      </mesh>
      {[-.83,.83].map(dx=><mesh key={dx} position={[x+dx,1.6,4.19]}>
        <boxGeometry args={[.052,2.65,.10]}/>
        <meshStandardMaterial color="#8fa9a7" roughness={.53} metalness={.67}/>
      </mesh>)}
      <mesh position={[x,1.23,4.205]}>
        <boxGeometry args={[1.2,.08,.095]}/>
        <meshStandardMaterial color="#758d89" roughness={.68} metalness={.53}/>
      </mesh>
      {[0,1,2].map(n=><mesh key={n} position={[x-.66+n*.66,.73,4.215]}>
        <boxGeometry args={[.055,.31,.095]}/>
        <meshStandardMaterial color="#718481" roughness={.68} metalness={.62}/>
      </mesh>)}
      <mesh position={[x+.73,2.63,4.24]}>
        <boxGeometry args={[.065,.065,.07]}/>
        <meshStandardMaterial emissive={powerVisible&&criticalLit?'#73d1b7':'#1f383a'}
          emissiveIntensity={powerVisible&&criticalLit?1.0:0} color="#4b7972"/>
      </mesh>
      {i===0 && <mesh position={[x,1.85,4.24]}>
        <boxGeometry args={[.95,.38,.09]}/>
        <meshStandardMaterial color="#30464a" emissive="#4eaea5"
          emissiveIntensity={powerVisible&&criticalLit?.34:0}/>
      </mesh>}
    </group>)}
  </group>
}

export function SchoolHeroDetails({visual, powerVisible}:{
  visual:VisualRehearsalState;powerVisible:boolean
}) {
  return <group>
    {/* A cleaned, low-contrast plastered facade with fixed original silhouette. */}
    <Batches parts={pilasters} color="#d8d6ca" roughness={.90}/>
    <Batches parts={facadeJoints} color="#b2b6ad" roughness={.91}/>
    <Batches parts={annexCornerReturns} color="#c4c9bf" roughness={.88}/>
    <Batches parts={roofEdgeDetail} color="#a5aea7" roughness={.68} metalness={.12}/>
    <Batches parts={roofDrainAndFittings} color="#647978" roughness={.66} metalness={.40}/>
    {/* Real window depth and framing, same eight original regular front
        windows and three emergency annex window centers. */}
    <Batches parts={windowBacking} color="#1b2f34" metalness={.37} roughness={.55}/>
    {FRONT_POSITIONS.map(([x,y])=><mesh key={'front-glass-'+x+'-'+y} position={[x,y,13.218]}>
      <boxGeometry args={[1.84,1.36,.055]}/>
      <meshStandardMaterial color={visual.noncriticalLit?'#725a49':'#1d3038'}
        emissive="#f5ae66" emissiveIntensity={visual.noncriticalLit?.78:0}
        metalness={.22} roughness={.24}/>
    </mesh>)}
    {EMERGENCY_POSITIONS.map(([x,y])=><mesh key={'critical-glass-'+x} position={[x,y,15.71]}>
      <boxGeometry args={[2.05,1.86,.055]}/>
      <meshStandardMaterial color={visual.criticalLit?'#487a78':'#233c41'}
        emissive="#79d9ca" emissiveIntensity={visual.criticalLit?1.25:0}
        metalness={.21} roughness={.25}/>
    </mesh>)}
    <Batches parts={windowFrameVertical} color="#b3bfba" roughness={.43} metalness={.54}/>
    <Batches parts={windowFrameHorizontal} color="#b3bfba" roughness={.43} metalness={.54}/>
    <Batches parts={windowMullions} color="#8ea6a4" roughness={.46} metalness={.50}/>
    <Batches parts={windowMidrails} color="#8b9e9b" roughness={.50} metalness={.49}/>
    <Batches parts={windowSills} color="#c3c6b9" roughness={.87}/>
    <SchoolEntrance lit={visual.noncriticalLit}/>
    <SchoolEquipmentDetails powerVisible={powerVisible} criticalLit={visual.criticalLit}/>
  </group>
}
