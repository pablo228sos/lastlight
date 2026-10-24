import { useLayoutEffect, useMemo, useRef, type RefObject } from 'react'
import { Line } from '@react-three/drei'
import { SchoolFacadeWall } from './SchoolFacadeWall'
import { useFrame } from '@react-three/fiber'
import { CanvasTexture, Color, MathUtils, MeshBasicMaterial, MeshStandardMaterial, Object3D, type InstancedMesh } from 'three'
import type { SceneLayer, ScenePhase, VisualRehearsalState } from '../app/useMissionState'
import type { SiteId } from '../features/sites'

type Building = { x: number; z: number; w: number; d: number; h: number; tone: number }
type MatrixItem = { x: number; y: number; z: number; sx: number; sy: number; sz: number; ry?: number }
const seeded = (n: number) => { const s = Math.sin(n * 93.731 + 18.61) * 43758.5453; return s - Math.floor(s) }
const buildingSites: Record<SiteId, [number, number]> = {
  school: [13, 7], clinic: [-58, -54], business: [74, -53], residential: [-58, 74],
}
const parcelX = [-116, -98, -60, -45, -12, 16, 75, 88, 115]
const parcelZ = [-115, -97, -59, -44, -10, 20, 73, 88, 114]
const buildings: Building[] = parcelX.flatMap((x, ix) => parcelZ.flatMap((z, iz) => {
  const i = ix * 17 + iz
  if ((x > -30 && x < 50 && z > -30 && z < 50) || seeded(i + 2) < .14) return []
  if (Math.abs(x + 58) < 4 && Math.abs(z + 54) < 6) return []
  if (Math.abs(x - 74) < 4 && Math.abs(z + 53) < 6) return []
  return [{ x: x + (seeded(i + 90) - .5) * 3, z: z + (seeded(i + 91) - .5) * 3,
    w: 7 + seeded(i + 12) * 6, d: 8 + seeded(i + 13) * 6,
    h: 5 + seeded(i + 14) * (seeded(i + 15) > .74 ? 23 : 13), tone: i % 4 }]
}))
const buildingBodies: MatrixItem[] = buildings.map(b => ({ x: b.x, y: b.h / 2, z: b.z, sx: b.w, sy: b.h, sz: b.d }))
const facadeBands: MatrixItem[] = buildings.flatMap(b => Array.from({ length: Math.max(1, Math.floor(b.h / 2.9)) }, (_, floor) => ({
  x: b.x, y: 2.85 + floor * 2.9, z: b.z, sx: b.w + .09, sy: .09, sz: b.d + .09,
})))
const entryCanopies: MatrixItem[] = buildings.filter((_, i) => i % 3 !== 2).map(b => ({
  x: b.x + b.w * .16, y: 2.75, z: b.z + b.d / 2 + .8, sx: 2.4, sy: .17, sz: 1.6,
}))
const roofCaps: MatrixItem[] = buildings.map(b => ({ x: b.x, y: b.h + .28, z: b.z, sx: b.w + .7, sy: .56, sz: b.d + .7 }))
const roofVents: MatrixItem[] = buildings.filter((_, i) => i % 3 !== 0).map(b => ({
  x: b.x - b.w * .24, y: b.h + .86, z: b.z + b.d * .2, sx: 1.8, sy: .8, sz: 1.5,
}))
const roofStacks: MatrixItem[] = buildings.filter((_, i) => i % 7 === 0).map(b => ({
  x: b.x + b.w * .22, y: b.h + 1.25, z: b.z - b.d * .24, sx: .7, sy: 1.8, sz: .7,
}))
const windows: MatrixItem[] = buildings.flatMap((b, index) => {
  const result: MatrixItem[] = []
  const floors = Math.max(1, Math.floor(b.h / 2.9))
  for (let floor = 0; floor < floors; floor++) {
    for (let col = 0; col < Math.floor(b.w / 2.1); col++) {
      if (seeded(index * 100 + floor * 20 + col) > .38)
        result.push({ x: b.x - b.w / 2 + 1.3 + col * 2.1, y: 1.7 + floor * 2.8, z: b.z + b.d / 2 + .035, sx: .58, sy: .62, sz: .05 })
    }
    for (let col = 0; col < Math.floor(b.d / 2.1); col++) {
      if (seeded(index * 191 + floor * 17 + col) > .43)
        result.push({ x: b.x + b.w / 2 + .035, y: 1.7 + floor * 2.8, z: b.z - b.d / 2 + 1.3 + col * 2.1, sx: .05, sy: .62, sz: .58 })
    }
  }
  return result
})
const trees: MatrixItem[] = Array.from({ length: 186 }, (_, i) => {
  const x = -122 + seeded(i * 8 + 1) * 244, z = -122 + seeded(i * 8 + 2) * 244
  return { x, y: 1.8 + seeded(i * 8 + 3) * .8, z, sx: 2.4, sy: 4.2, sz: 2.4 }
}).filter(t => !((t.x > -15 && t.x < 40 && t.z > -10 && t.z < 35) ||
  [-80, -33, 55, 100].some(road => Math.abs(t.x - road) < 6 || Math.abs(t.z - road) < 6)))
const lampSites = [-111, -66, -18, 31, 77, 119].flatMap(x => [-80, -33, 55, 100].map(z => ({ x, z })))
  .concat([-111, -66, -18, 31, 77, 119].flatMap(z => [-80, -33, 55, 100].map(x => ({ x, z }))))
const lamps: MatrixItem[] = lampSites.map(({ x, z }) => ({ x, y: 5.2, z, sx: .45, sy: .45, sz: .45 }))
const campusFencePosts: MatrixItem[] = [
  ...Array.from({ length: 13 }, (_, i) => [-30 + i * 5, -25] as const),
  ...Array.from({ length: 13 }, (_, i) => [-30 + i * 5, 25] as const).filter(([x]) => x < -27 || x > -9),
  ...Array.from({ length: 9 }, (_, i) => [-30, -20 + i * 5] as const),
  ...Array.from({ length: 9 }, (_, i) => [30, -20 + i * 5] as const),
].map(([x, z]) => ({ x, y: .9, z, sx: .12, sy: 1.8, sz: .12 }))
const campusFenceRails: MatrixItem[] = [.5, 1.35].flatMap(y => [
  { x: 0, y, z: -25, sx: 60, sy: .06, sz: .08 },
  { x: -30, y, z: 0, sx: .08, sy: .06, sz: 50 },
  { x: 30, y, z: 0, sx: .08, sy: .06, sz: 50 },
  { x: -28.5, y, z: 25, sx: 3, sy: .06, sz: .08 },
  { x: 10.5, y, z: 25, sx: 39, sy: .06, sz: .08 },
])
const schoolLit = new MeshStandardMaterial({ color: '#7c5a37', emissive: '#ffbc70', emissiveIntensity: 1.6, toneMapped: false })
const schoolEmergency = new MeshStandardMaterial({ color: '#386566', emissive: '#65d4c8', emissiveIntensity: 3.5, toneMapped: false })

function Instances({ items, color, emissive, emissiveIntensity = 0, roughness = 1 }: {
  items: MatrixItem[]; color: string; emissive?: string; emissiveIntensity?: number; roughness?: number
}) {
  const ref = useRef<InstancedMesh>(null)
  useLayoutEffect(() => {
    const object = new Object3D()
    items.forEach((item, index) => {
      object.position.set(item.x, item.y, item.z)
      object.scale.set(item.sx, item.sy, item.sz)
      object.rotation.y = item.ry ?? 0
      object.updateMatrix()
      ref.current?.setMatrixAt(index, object.matrix)
    })
    if (ref.current) { ref.current.instanceMatrix.needsUpdate = true; ref.current.computeBoundingSphere() }
  }, [items])
  return <instancedMesh ref={ref} args={[undefined, undefined, items.length]} castShadow receiveShadow>
    <boxGeometry args={[1, 1, 1]} />
    <meshStandardMaterial color={color} emissive={emissive} emissiveIntensity={emissiveIntensity} roughness={roughness} />
  </instancedMesh>
}

function CityFabric({ visual }: { visual: VisualRehearsalState }) {
  const windowMaterial = useRef<MeshStandardMaterial>(null)
  const lampMaterial = useRef<MeshStandardMaterial>(null)
  const windowMesh = useRef<InstancedMesh>(null)
  const lampMesh = useRef<InstancedMesh>(null)
  useLayoutEffect(() => {
    const apply = (ref: RefObject<InstancedMesh | null>, items: MatrixItem[]) => {
      const object = new Object3D()
      items.forEach((item, index) => {
        object.position.set(item.x, item.y, item.z); object.scale.set(item.sx, item.sy, item.sz)
        object.updateMatrix(); ref.current?.setMatrixAt(index, object.matrix)
      })
      if (ref.current) { ref.current.instanceMatrix.needsUpdate = true; ref.current.computeBoundingSphere() }
    }
    apply(windowMesh, windows); apply(lampMesh, lamps)
  }, [])
  useFrame((_, delta) => {
    const target = visual.noncriticalLit ? 1.7 : 0
    if (windowMaterial.current) windowMaterial.current.emissiveIntensity = MathUtils.damp(windowMaterial.current.emissiveIntensity, target, 3.2, delta)
    if (windowMaterial.current) windowMaterial.current.color.lerp(new Color(visual.noncriticalLit ? '#966b40' : '#1b2b2e'), Math.min(1, delta * 3))
    if (lampMaterial.current) lampMaterial.current.emissiveIntensity = MathUtils.damp(lampMaterial.current.emissiveIntensity, visual.gridConnected ? 2.3 : 0, 2.7, delta)
    if (lampMaterial.current) lampMaterial.current.color.lerp(new Color(visual.gridConnected ? '#eeb974' : '#26393c'), Math.min(1, delta * 3))
  })
  return <>
    <Instances items={buildingBodies} color="#29343a" roughness={.88} />
    <Instances items={facadeBands} color="#465356" roughness={.94} />
    <Instances items={entryCanopies} color="#45555a" roughness={.85} />
    <Instances items={roofCaps} color="#3e474b" roughness={.91} />
    <Instances items={roofVents} color="#2b3b40" />
    <Instances items={roofStacks} color="#394b4d" />
    <instancedMesh ref={windowMesh} args={[undefined, undefined, windows.length]} castShadow={false}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial ref={windowMaterial} color="#966b40" emissive="#e49a4e" emissiveIntensity={1.7} toneMapped={false} />
    </instancedMesh>
    <Instances items={trees} color="#192e31" />
    <Instances items={lampSites.map(({ x, z }) => ({ x, y: 2.8, z, sx: .13, sy: 5.6, sz: .13 }))} color="#4a5556" />
    <instancedMesh ref={lampMesh} args={[undefined, undefined, lamps.length]}>
      <sphereGeometry args={[1, 8, 8]} />
      <meshStandardMaterial ref={lampMaterial} color="#eeb974" emissive="#ffac4b" emissiveIntensity={2.3} toneMapped={false} />
    </instancedMesh>
  </>
}

function StreetPools({ visual }: { visual: VisualRehearsalState }) {
  const ref = useRef<InstancedMesh>(null)
  const material = useRef<MeshBasicMaterial>(null)
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 128; canvas.height = 128
    const context = canvas.getContext('2d')!
    const halo = context.createRadialGradient(64, 64, 2, 64, 64, 63)
    halo.addColorStop(0, 'rgba(245,171,83,.32)')
    halo.addColorStop(.25, 'rgba(235,151,68,.19)')
    halo.addColorStop(1, 'rgba(235,151,68,0)')
    context.fillStyle = halo; context.fillRect(0, 0, 128, 128)
    return new CanvasTexture(canvas)
  }, [])
  useLayoutEffect(() => {
    const object = new Object3D()
    lampSites.forEach(({ x, z }, index) => {
      object.position.set(x, .065, z); object.rotation.x = -Math.PI / 2
      object.scale.set(18, 18, 1); object.updateMatrix(); ref.current?.setMatrixAt(index, object.matrix)
    })
    if (ref.current) { ref.current.instanceMatrix.needsUpdate = true; ref.current.computeBoundingSphere() }
  }, [])
  useFrame((_, delta) => { if (material.current) material.current.opacity = MathUtils.damp(material.current.opacity, visual.gridConnected ? .92 : .01, 3, delta) })
  return <instancedMesh ref={ref} args={[undefined, undefined, lampSites.length]} renderOrder={1}>
    <circleGeometry args={[1, 24]} />
    <meshBasicMaterial ref={material} map={texture} transparent opacity={.92} depthWrite={false} />
  </instancedMesh>
}

function Streets() {
  const roads = [-80, -33, 55, 100]
  return <>
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow><planeGeometry args={[310, 310]} /><meshStandardMaterial color="#17252a" roughness={1} /></mesh>
    {roads.map((at, i) => <group key={'x' + i}>
      <mesh position={[at, .015, 0]} receiveShadow><boxGeometry args={[10, .03, 270]} /><meshStandardMaterial color="#222a2c" /></mesh>
      <mesh position={[0, .018, at]} receiveShadow><boxGeometry args={[270, .03, 10]} /><meshStandardMaterial color="#222a2c" /></mesh>
      {Array.from({ length: 26 }, (_, j) => <group key={j}>
        <mesh position={[at, .047, -128 + j * 10]}><boxGeometry args={[.13, .015, 2.5]} /><meshBasicMaterial color="#7b6f58" transparent opacity={.34} /></mesh>
        <mesh position={[-128 + j * 10, .047, at]}><boxGeometry args={[2.5, .015, .13]} /><meshBasicMaterial color="#7b6f58" transparent opacity={.34} /></mesh>
      </group>)}
    </group>)}
  </>
}

function School({ visual, layer, onSelect, showHotspots }: {
  visual: VisualRehearsalState; layer: SceneLayer; onSelect: () => void
  showHotspots: boolean
}) {
  useFrame((_, delta) => {
    schoolLit.emissiveIntensity = MathUtils.damp(schoolLit.emissiveIntensity, visual.noncriticalLit ? 1.6 : 0, 3, delta)
    schoolLit.color.lerp(new Color(visual.noncriticalLit ? '#7c5a37' : '#1c3338'), Math.min(1, delta * 3))
    schoolEmergency.emissiveIntensity = MathUtils.damp(schoolEmergency.emissiveIntensity, visual.criticalLit ? 3.5 : .08, 2, delta)
  })
  return <group position={[13, 0, 7]} onClick={(event) => { event.stopPropagation(); onSelect() }} onPointerOver={() => { document.body.style.cursor = 'pointer' }} onPointerOut={() => { document.body.style.cursor = 'auto' }}>
    {showHotspots && <Line points={[[-30, .19, -25], [30, .19, -25], [30, .19, 25], [-30, .19, 25], [-30, .19, -25]]}
      color="#a8dbd0" lineWidth={1.2} transparent opacity={.64} />}
    <mesh position={[0, .07, 0]} receiveShadow><boxGeometry args={[60, .14, 50]} /><meshStandardMaterial color="#36403b" /></mesh>
    <Instances items={campusFencePosts} color="#637875" roughness={.8} />
    <Instances items={campusFenceRails} color="#58716f" roughness={.82} />
    <mesh position={[-18, .16, 21.5]}><boxGeometry args={[6.5, .04, 7]} /><meshStandardMaterial color="#64736d" roughness={.95} /></mesh>
    <pointLight position={[-18, 5.5, 15]} intensity={visual.gridConnected ? 12 : 0} distance={22} color="#ffbd72" decay={2} />
    <mesh position={[-18, .09, 17]}><boxGeometry args={[19, .025, 14]} /><meshStandardMaterial color="#365454" roughness={1} /></mesh>
    <mesh position={[-18, .115, 17]}><boxGeometry args={[18, .02, .1]} /><meshBasicMaterial color="#a2a087" /></mesh>
    <mesh position={[-18, .115, 10.1]}><boxGeometry args={[18, .02, .1]} /><meshBasicMaterial color="#a2a087" /></mesh>
    <mesh position={[-26.9, .115, 17]}><boxGeometry args={[.1, .02, 14]} /><meshBasicMaterial color="#a2a087" /></mesh>
    <mesh position={[-9.1, .115, 17]}><boxGeometry args={[.1, .02, 14]} /><meshBasicMaterial color="#a2a087" /></mesh>
    <mesh position={[-18, .125, 17]} rotation={[-Math.PI / 2, 0, 0]}><ringGeometry args={[3.1, 3.18, 28]} /><meshBasicMaterial color="#a2a087" side={2} /></mesh>
    <SchoolFacadeWall variant="main" />
    <mesh position={[0, 8.3, 6]} castShadow><boxGeometry args={[31, .65, 15]} /><meshStandardMaterial color="#293e47" roughness={.7} /></mesh>
    {[1.2, 3.95, 6.7].map(y => <group key={'course' + y}>
      <mesh position={[0, y, 13.09]}><boxGeometry args={[30, .075, .12]} /><meshStandardMaterial color="#6e827d" /></mesh>
      <mesh position={[15.06, y, 6]}><boxGeometry args={[.12, .075, 14]} /><meshStandardMaterial color="#6e827d" /></mesh>
    </group>)}
    {[-13.3, -4.5, 4.5, 13.3].map(x => <mesh key={'pier' + x} position={[x, 4.1, 13.16]}>
      <boxGeometry args={[.35, 8, .2]} /><meshStandardMaterial color="#697d79" />
    </mesh>)}
    <SchoolFacadeWall variant="annex" />
    <mesh position={[15.7, 6.45, 11]}><boxGeometry args={[10.6, .5, 9.5]} /><meshStandardMaterial color="#263e46" /></mesh>
    <mesh position={[0, .2, 17.5]}><boxGeometry args={[10, .1, 6]} /><meshStandardMaterial color="#787e72" /></mesh>
    <mesh position={[0, 4.6, 15]} castShadow><boxGeometry args={[7, .2, 4.5]} /><meshStandardMaterial color="#314b51" metalness={.2} /></mesh>
    {[[-3, 2.2, 16.4], [3, 2.2, 16.4]].map(([x,y,z],i)=><mesh key={'canopy' + i} position={[x,y,z]}><boxGeometry args={[.2,4.3,.2]} /><meshStandardMaterial color="#57706b" /></mesh>)}
    <mesh position={[0, 2.2, 13.05]}><boxGeometry args={[4.4, 4.2, .12]} /><meshStandardMaterial color="#1d3037" metalness={.35} roughness={.4} /></mesh>
    <mesh position={[0, 4.8, 13.14]}><boxGeometry args={[7, .22, .15]} /><meshStandardMaterial color="#ebe3c8" emissive="#e4a866" emissiveIntensity={visual.noncriticalLit ? .7 : .02} /></mesh>
    {[-11, -7, 7, 11].flatMap((x) => [2.1, 5.6].map(y => <mesh key={x + '/' + y} position={[x, y, 13.065]}>
      <boxGeometry args={[1.7, 1.25, .12]} /><primitive object={schoolLit} attach="material" />
    </mesh>))}
    {[-10, -6, -2, 2, 6, 10].map(x => <mesh key={'back' + x} position={[x, 4.4, -1.09]}>
      <boxGeometry args={[1.6, 2, .12]} /><meshStandardMaterial color="#7a5835" emissive="#e69852" emissiveIntensity={visual.noncriticalLit ? 1.7 : .04} toneMapped={false} />
    </mesh>)}
    {[11.8, 15, 18.2].map(x => <mesh key={'annex' + x} position={[x, 3.4, 15.55]}>
      <boxGeometry args={[1.8, 1.7, .12]} /><primitive object={schoolEmergency} attach="material" />
    </mesh>)}
    {Array.from({ length: 12 }, (_, i) => {
      const x = -12 + (i % 6) * 4.5, z = 2.3 + Math.floor(i / 6) * 3.4
      return <group key={i} position={[x, 8.75, z]} rotation={[-.12, 0, 0]}>
        <mesh castShadow><boxGeometry args={[3.7, .12, 2.6]} /><meshStandardMaterial color="#102b3c" metalness={.45} roughness={.3} /></mesh>
        <mesh position={[0, .075, 0]}><boxGeometry args={[3.45, .025, 2.35]} /><meshStandardMaterial color="#234e64" metalness={.62} roughness={.24} /></mesh>
        <mesh position={[0, .093, 0]}><boxGeometry args={[.045, .01, 2.35]} /><meshBasicMaterial color="#6e9fa9" /></mesh>
      </group>
    })}
    <mesh position={[19.4, 1.65, 3.2]} castShadow><boxGeometry args={[2.5, 3.1, 1.8]} /><meshStandardMaterial color="#253d45" metalness={.55} roughness={.5} /></mesh>
    <mesh position={[19.4, 1.8, 4.13]}><boxGeometry args={[1.5, .8, .05]} /><meshStandardMaterial color="#254f56" emissive="#69c8bd" emissiveIntensity={layer === 'power' ? 1.4 : .25} /></mesh>
    <mesh position={[15.7, 1.5, 3.2]} castShadow><boxGeometry args={[2.3, 2.8, 1.7]} /><meshStandardMaterial color="#454d4e" metalness={.5} roughness={.45} /></mesh>
    <mesh position={[15.7, 2, 4.08]}><boxGeometry args={[1.5, .16, .04]} /><meshBasicMaterial color="#92d5c4" /></mesh>
    {layer === 'power' && <>
      <Line points={[[-8, 8.95, 5], [11, 8.95, 5], [16, 6.9, 5], [16, 2.5, 4]]} color="#8dd7d1" lineWidth={2} transparent opacity={.88} />
      <Line points={[[19.5, 2.5, 4], [16, 2.5, 4], [16, 1, 10]]} color="#8dd7d1" lineWidth={2} transparent opacity={.88} />
      <Line points={[[24, .25, 12], [19.5, .25, 12], [19.5, 1.5, 4]]} color={visual.gridConnected ? '#efae68' : '#495350'} lineWidth={2.5} />
    </>}
  </group>
}

function SpecialFacility({ id, visual, onSelect, selected }: { id: Exclude<SiteId, 'school'>; visual: VisualRehearsalState; onSelect: () => void; selected: boolean }) {
  const [x, z] = buildingSites[id]
  const isClinic = id === 'clinic'
  return <group position={[x, 0, z]} onClick={(e) => { e.stopPropagation(); onSelect() }}>
    {selected && <Line points={[[-12, .15, -10], [12, .15, -10], [12, .15, 10], [-12, .15, 10], [-12, .15, -10]]}
      color="#a8dbd0" lineWidth={1.2} transparent opacity={.64} />}
    <mesh position={[0, 3.8, 0]} castShadow><boxGeometry args={[isClinic ? 20 : 15, isClinic ? 7.4 : 8.5, isClinic ? 14 : 13]} /><meshStandardMaterial color={isClinic ? '#8b9892' : '#686e68'} /></mesh>
    <mesh position={[0, isClinic ? 7.8 : 8.9, 0]}><boxGeometry args={[isClinic ? 20.8 : 15.8, .5, isClinic ? 14.8 : 13.8]} /><meshStandardMaterial color="#2e4249" /></mesh>
    {[-6, -2, 2, 6].map(v => <mesh key={v} position={[v, 4.4, isClinic ? 7.05 : 6.55]}><boxGeometry args={[1.4, 1.8, .1]} /><meshStandardMaterial color={visual.noncriticalLit ? '#d79952' : '#263d3e'} emissive={visual.noncriticalLit ? '#e7aa68' : '#253c3e'} emissiveIntensity={visual.noncriticalLit ? 1.5 : .02} toneMapped={false} /></mesh>)}
    {isClinic && <mesh position={[0, 8.11, 0]}><boxGeometry args={[.9, .06, 4]} /><meshBasicMaterial color="#93d8cc" /></mesh>}
    {isClinic && <mesh position={[0, 8.12, 0]}><boxGeometry args={[4, .06, .9]} /><meshBasicMaterial color="#93d8cc" /></mesh>}
  </group>
}

export function DistrictWorld({ visual, layer, phase, selected, lowPower, onSelect }: {
  visual: VisualRehearsalState; layer: SceneLayer; phase: ScenePhase; selected: SiteId; lowPower: boolean
  onSelect: (id: SiteId) => void
}) {
  const showHotspots = selected === 'school' && (phase === 'SITE' || phase === 'INSPECT' || phase === 'BLACKOUT')
  const mountainPieces = useMemo(() => Array.from({ length: 15 }, (_, i) => ({
    x: -230 + i * 33, z: -220 - seeded(i + 200) * 40, h: 37 + seeded(i + 290) * 45,
  })), [])
  return <>
    <color attach="background" args={['#09141b']} />
    <fog attach="fog" args={['#09141b', 145, 460]} />
    <ambientLight intensity={1.15} color="#9fb8b9" />
    <hemisphereLight intensity={.8} color="#779aa8" groundColor="#382b25" />
    <directionalLight position={[-60, 150, 80]} intensity={1.9} color="#bbd2d8" castShadow={!lowPower} shadow-mapSize={lowPower ? [512, 512] : [2048, 2048]} shadow-camera-left={-145} shadow-camera-right={145} shadow-camera-top={145} shadow-camera-bottom={-145} />
    <pointLight position={[13, 26, 7]} intensity={visual.gridConnected ? 85 : 22} distance={105} color="#f5a45b" decay={2} />
    <Streets />
    {!lowPower && <StreetPools visual={visual} />}
    <CityFabric visual={visual} />
    <School visual={visual} layer={layer} onSelect={() => onSelect('school')} showHotspots={showHotspots} />
    <SpecialFacility id="clinic" visual={visual} onSelect={() => onSelect('clinic')} selected={selected === 'clinic' && showHotspots === false && (phase === 'SITE' || phase === 'INSPECT' || phase === 'BLACKOUT')} />
    <SpecialFacility id="business" visual={visual} onSelect={() => onSelect('business')} selected={selected === 'business' && showHotspots === false && (phase === 'SITE' || phase === 'INSPECT' || phase === 'BLACKOUT')} />
    <SpecialFacility id="residential" visual={visual} onSelect={() => onSelect('residential')} selected={selected === 'residential' && showHotspots === false && (phase === 'SITE' || phase === 'INSPECT' || phase === 'BLACKOUT')} />
    {mountainPieces.map((m, i) => <mesh key={i} position={[m.x, m.h / 2 - 8, m.z]} rotation={[0, seeded(i + 12), 0]}>
      <coneGeometry args={[28 + seeded(i + 40) * 15, m.h, 4]} /><meshStandardMaterial color={i % 3 ? '#172932' : '#1e333b'} flatShading roughness={1} />
    </mesh>)}
  </>
}
