/**
 * LASTLIGHT / Photoreal District — Street Material Pass 01
 *
 * All four original street axes and 10-unit-wide road geometries are fixed:
 * [-80, -33, 55, 100]. This renders asphalt, pedestrian surface, curbs and
 * markings as a single scene. No street or building relocation.
 */
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import { CanvasTexture, Object3D, RepeatWrapping, SRGBColorSpace, type InstancedMesh } from 'three'

export const ORIGINAL_STREET_AXES = [-80, -33, 55, 100] as const
type Strip = { x: number; y: number; z: number; w: number; h: number; d: number }

const grain = (x: number, y: number) => {
  let hash = ((x * 374761393) ^ (y * 668265263)) >>> 0
  hash = Math.imul(hash ^ (hash >>> 13), 1274126177) >>> 0
  return (hash ^ (hash >>> 16)) / 4294967295
}

/** Deterministic asphalt aggregate with fine pores; not a blurry photo. */
function makeAsphaltMap() {
  const c = document.createElement('canvas')
  c.width = c.height = 256
  const g = c.getContext('2d')
  if (!g) throw new Error('canvas2d unavailable')
  const pixels = g.createImageData(256, 256)
  for (let y = 0; y < 256; y++) for (let x = 0; x < 256; x++) {
    const n = grain(x, y)
    const coarse = grain(Math.floor(x / 8), Math.floor(y / 8))
    const v = Math.max(29, Math.min(66, 44 + (n - .5) * 19 + (coarse - .5) * 8))
    const idx = (y * 256 + x) * 4
    pixels.data[idx] = Math.round(v * .95)
    pixels.data[idx+1] = Math.round(v * .97)
    pixels.data[idx+2] = Math.round(v)
    pixels.data[idx+3] = 255
  }
  g.putImageData(pixels,0,0)
  const t = new CanvasTexture(c); t.colorSpace = SRGBColorSpace
  t.wrapS = t.wrapT = RepeatWrapping; t.anisotropy = 4
  return t
}

function makePavingMap() {
  const c = document.createElement('canvas')
  c.width = c.height = 256
  const g = c.getContext('2d')
  if (!g) throw new Error('canvas2d unavailable')
  g.fillStyle = '#636b68'; g.fillRect(0, 0, 256, 256)
  for (let row = 0; row < 8; row++) for (let col = 0; col < 4; col++) {
    const x = col * 64 + (row % 2 ? -32 : 0)
    const y = row * 32
    const shade = Math.floor(grain(col+row*10, row*3) * 11)
    g.fillStyle = 'rgb(' + (91+shade) + ',' + (99+shade) + ',' + (96+shade) + ')'
    g.fillRect(x+1,y+1,62,30)
    if (x < 0) g.fillRect(x+257,y+1,62,30)
  }
  const t = new CanvasTexture(c); t.colorSpace=SRGBColorSpace
  t.wrapS=t.wrapT=RepeatWrapping; t.anisotropy=4
  return t
}

function roadStripMap(original: CanvasTexture, repeatsX: number, repeatsY: number) {
  const t=original.clone()
  t.needsUpdate=true
  t.repeat.set(repeatsX,repeatsY)
  return t
}

function Stripes({ pieces, color }: { pieces: Strip[]; color: string }) {
  const mesh = useRef<InstancedMesh>(null)
  useLayoutEffect(() => {
    const node = mesh.current
    if (!node) return
    const o = new Object3D()
    pieces.forEach((p, i) => {
      o.position.set(p.x,p.y,p.z); o.scale.set(p.w,p.h,p.d)
      o.updateMatrix(); node.setMatrixAt(i,o.matrix)
    })
    node.instanceMatrix.needsUpdate=true
    node.computeBoundingSphere()
  },[pieces])
  return <instancedMesh args={[undefined,undefined,pieces.length]} ref={mesh} castShadow={false} receiveShadow={false}>
    <boxGeometry args={[1,1,1]}/>
    <meshStandardMaterial color={color} transparent opacity={.73} roughness={.96} metalness={0}/>
  </instancedMesh>
}

const markings: Strip[] = ORIGINAL_STREET_AXES.flatMap(at => Array.from({length:26}, (_,j) => [
  {x:at,y:.047,z:-128+j*10,w:.13,h:.015,d:2.5},
  {x:-128+j*10,y:.047,z:at,w:2.5,h:.015,d:.13},
])).flat()
const crosswalks: Strip[] = ORIGINAL_STREET_AXES.flatMap(x =>
  ORIGINAL_STREET_AXES.flatMap(z =>
    Array.from({length:7},(_,j)=>[
      {x:x-3.15+j*1.02,y:.052,z:z+8,w:.58,h:.013,d:2.55},
      {x:x+8,y:.052,z:z-3.15+j*1.02,w:2.55,h:.013,d:.58},
    ]).flat()
  )
)

export function CinematicStreets() {
  const maps=useMemo(() => {
    const base=makeAsphaltMap(),pave=makePavingMap()
    return {
      base,pave,
      asphaltNS:roadStripMap(base,1,28),
      asphaltEW:roadStripMap(base,28,1),
      pavementNS:roadStripMap(pave,1,44),
      pavementEW:roadStripMap(pave,44,1),
    }
  },[])
  useEffect(()=>()=>Object.values(maps).forEach(t=>t.dispose()),[maps])
  return <>
    <mesh rotation={[-Math.PI / 2,0,0]} receiveShadow>
      <planeGeometry args={[310,310]}/>
      <meshStandardMaterial color="#283634" roughness={1}/>
    </mesh>
    {ORIGINAL_STREET_AXES.map((at,i)=><group key={i}>
      {/* Road centerline and width exactly match the old procedural scene. */}
      <mesh position={[at,.015,0]} receiveShadow>
        <boxGeometry args={[10,.03,270]}/>
        <meshStandardMaterial map={maps.asphaltNS} color="#d0d5d0" metalness={0} roughness={.94}/>
      </mesh>
      <mesh position={[0,.018,at]} receiveShadow>
        <boxGeometry args={[270,.03,10]}/>
        <meshStandardMaterial map={maps.asphaltEW} color="#d0d5d0" metalness={0} roughness={.94}/>
      </mesh>
      {/* Sidewalks exist only along old roads, keeping urban topology intact. */}
      {[-1,1].map(side=><group key={side}>
        <mesh position={[at+side*6.47,.064,0]} receiveShadow>
          <boxGeometry args={[2.55,.11,270]}/>
          <meshStandardMaterial color="#a7aaa4" map={maps.pavementNS} roughness={.96}/>
        </mesh>
        <mesh position={[0,.064,at+side*6.47]} receiveShadow>
          <boxGeometry args={[270,.11,2.55]}/>
          <meshStandardMaterial color="#a7aaa4" map={maps.pavementEW} roughness={.96}/>
        </mesh>
        {/* Narrow cast-concrete upstands, no luminous sci-fi line strips. */}
        <mesh position={[at+side*5.14,.078,0]}>
          <boxGeometry args={[.18,.15,270]}/>
          <meshStandardMaterial color="#777e79" roughness={.97}/>
        </mesh>
        <mesh position={[0,.078,at+side*5.14]}>
          <boxGeometry args={[270,.15,.18]}/>
          <meshStandardMaterial color="#777e79" roughness={.97}/>
        </mesh>
      </group>)}
    </group>)}
    <Stripes pieces={markings} color="#b4a482"/>
    <Stripes pieces={crosswalks} color="#c7cac0"/>
  </>
}
