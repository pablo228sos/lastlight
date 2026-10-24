/**
 * LASTLIGHT / Cinematic District PBR v1
 * Existing parcel origins, building dimensions and silhouettes are immutable.
 *
 * This module adds physically plausible procedural wall finishes and decorative
 * facade hardware to those existing boxes. Everything uses instanced geometry
 * rather than loading unrelated external city models.
 */
import { useEffect, useLayoutEffect, useMemo, useRef } from 'react'
import { CanvasTexture, Color, Object3D, SRGBColorSpace, type InstancedMesh } from 'three'

export type ExistingCityBuilding = {
  x: number; z: number; w: number; d: number; h: number; tone: number
}
type Piece = { x: number; y: number; z: number; w: number; h: number; d: number }
type Decoration = {
  glass: Piece[]; jambs: Piece[]; lintels: Piece[]
  plinths: Piece[]; seams: Piece[]; doors: Piece[]
  balconySlabs: Piece[]; balconyGuards: Piece[]
}

const TONES = ['#c0c1b6', '#afb9b8', '#c2b6a8', '#b8bec0']
function createMineralWallMap() {
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = 512
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('Canvas 2D required for architectural wall map')
  ctx.fillStyle = '#c9ccc9'
  ctx.fillRect(0, 0, 512, 512)

  // Fine, low-contrast aggregate; no large cloud-like noise or streaky weathering.
  for (let y = 0; y < 512; y += 2) {
    for (let x = 0; x < 512; x += 2) {
      const r = (x * 1973 + y * 9277 + 89173) >>> 0
      const q = Math.sin(r * 0.00081) * 43758.5453
      const n = q - Math.floor(q)
      const a = n > 0.64 ? (n - 0.64) * 0.11 : 0
      ctx.fillStyle = 'rgba(42,50,50,' + a.toFixed(3) + ')'
      ctx.fillRect(x, y, 2, 2)
    }
  }
  // Clean prefabricated-concrete joints, tonal offset below the window rhythm.
  ctx.lineWidth = 2
  ctx.strokeStyle = 'rgba(42,53,58,0.20)'
  for (const y of [0, 128, 256, 384, 510]) {
    ctx.beginPath(); ctx.moveTo(0, y + 0.5); ctx.lineTo(512, y + 0.5); ctx.stroke()
  }
  ctx.lineWidth = 1
  ctx.strokeStyle = 'rgba(242,245,238,0.26)'
  for (const y of [2, 130, 258, 386]) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(512, y); ctx.stroke()
  }
  for (const x of [0, 170, 342, 510]) {
    ctx.strokeStyle = 'rgba(37,46,48,0.15)'
    ctx.beginPath(); ctx.moveTo(x + 0.5, 0); ctx.lineTo(x + 0.5, 512); ctx.stroke()
  }
  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  texture.anisotropy = 4
  return texture
}

function useMatrixInstances(ref: React.RefObject<InstancedMesh | null>, pieces: Piece[]) {
  useLayoutEffect(() => {
    const refMesh = ref.current
    if (!refMesh || !pieces.length) return
    const object = new Object3D()
    for (let index = 0; index < pieces.length; index++) {
      const item = pieces[index]
      object.position.set(item.x, item.y, item.z)
      object.scale.set(item.w, item.h, item.d)
      object.updateMatrix()
      refMesh.setMatrixAt(index, object.matrix)
    }
    refMesh.instanceMatrix.needsUpdate = true
    refMesh.computeBoundingSphere()
  }, [ref, pieces])
}

/** Real architectural parts, batched by material for interactive laptop FPS. */
function DetailInstances({ pieces, color, metallic = 0, roughness = .82 }: {
  pieces: Piece[]; color: string; metallic?: number; roughness?: number
}) {
  const ref = useRef<InstancedMesh>(null)
  useMatrixInstances(ref, pieces)
  if (!pieces.length) return null
  return <instancedMesh ref={ref} args={[undefined, undefined, pieces.length]} castShadow={false} receiveShadow={false}>
    <boxGeometry args={[1, 1, 1]} />
    <meshStandardMaterial color={color} metalness={metallic} roughness={roughness}/>
  </instancedMesh>
}

export function ArchitecturalBuildingBodies({ buildings }: { buildings: ExistingCityBuilding[] }) {
  const ref = useRef<InstancedMesh>(null)
  const map = useMemo(createMineralWallMap, [])
  useEffect(() => () => map.dispose(), [map])
  useLayoutEffect(() => {
    if (!ref.current) return
    const node = new Object3D()
    buildings.forEach((b, i) => {
      node.position.set(b.x, b.h / 2, b.z)
      node.scale.set(b.w, b.h, b.d)
      node.updateMatrix()
      ref.current?.setMatrixAt(i, node.matrix)
      ref.current?.setColorAt(i, new Color(TONES[b.tone % TONES.length]))
    })
    ref.current.instanceMatrix.needsUpdate = true
    if (ref.current.instanceColor) ref.current.instanceColor.needsUpdate = true
    ref.current.computeBoundingSphere()
  }, [buildings])
  return <instancedMesh ref={ref} args={[undefined, undefined, buildings.length]} castShadow receiveShadow>
    <boxGeometry args={[1, 1, 1]}/>
    <meshStandardMaterial map={map} color="#ffffff" roughness={.92} metalness={.02}/>
  </instancedMesh>
}

/** All added details are mounted on original wall planes, never new building masses. */
function decorateBuildings(buildings: ExistingCityBuilding[], lowPower: boolean): Decoration {
  const result: Decoration = {
    glass: [], jambs: [], lintels: [], plinths: [], seams: [], doors: [],
    balconySlabs: [], balconyGuards: [],
  }
  const add = (key: keyof Decoration, x: number, y: number, z: number, w: number, h: number, d: number) => {
    result[key].push({ x, y, z, w, h, d })
  }
  buildings.forEach((b, i) => {
    const front = b.z + b.d / 2, back = b.z - b.d / 2
    const right = b.x + b.w / 2, left = b.x - b.w / 2
    const floors = Math.max(1, Math.floor(b.h / 2.9))
    const maxX = Math.max(1, Math.floor(b.w / 2.1))
    const maxZ = Math.max(1, Math.floor(b.d / 2.1))
    // Dark polished plinth at pedestrian eye level: fixed inside wall footprint.
    add('plinths', b.x, .21, front + .055, b.w, .42, .105)
    add('plinths', b.x, .21, back - .055, b.w, .42, .105)
    add('plinths', right + .055, .21, b.z, .105, .42, b.d)
    add('plinths', left - .055, .21, b.z, .105, .42, b.d)
    // Original entry-canopy placement matches the previous scene.
    if (i % 3 !== 2) {
      add('doors', b.x + b.w * .16, 1.19, front + .095, 1.52, 2.29, .075)
    }
    // Fine vertical expansion joints and corner returns; subtle at distance.
    if (!lowPower) {
      for (const x of [left + .13, right - .13]) {
        add('seams', x, b.h / 2, front + .052, .035, b.h, .06)
        add('seams', x, b.h / 2, back - .052, .035, b.h, .06)
      }
      for (const z of [back + .13, front - .13]) {
        add('seams', right + .052, b.h / 2, z, .06, b.h, .035)
        add('seams', left - .052, b.h / 2, z, .06, b.h, .035)
      }
    }

    const window = (x: number, y: number, z: number, axis: 'x'|'z') => {
      if (axis === 'z') {
        add('glass', x, y, z, 1.10, 1.37, .055)
        if (!lowPower) {
          for (const dx of [-.56, .56]) add('jambs', x + dx, y, z + (z > b.z ? .04 : -.04), .055, 1.45, .062)
          for (const dy of [-.71, .71]) add('lintels', x, y + dy, z + (z > b.z ? .04 : -.04), 1.19, .056, .064)
          add('lintels', x, y - .77, z + (z > b.z ? .10 : -.10), 1.32, .08, .19)
        }
      } else {
        add('glass', x, y, z, .055, 1.37, 1.10)
        if (!lowPower) {
          for (const dz of [-.56, .56]) add('jambs', x + (x > b.x ? .04 : -.04), y, z + dz, .062, 1.45, .055)
          for (const dy of [-.71, .71]) add('lintels', x + (x > b.x ? .04 : -.04), y + dy, z, .064, .056, 1.19)
          add('lintels', x + (x > b.x ? .10 : -.10), y - .77, z, .19, .08, 1.32)
        }
      }
    }
    for (let floor = 0; floor < floors; floor++) {
      const y = 1.7 + floor * 2.8
      if (y + .75 > b.h) continue
      for (let col = 0; col < maxX; col++) {
        const x = b.x - b.w / 2 + 1.3 + col * 2.1
        // Never add windows across the building's physical corners.
        if (x > right - .7) continue
        window(x, y, front + .067, 'z')
        if (!lowPower) window(x, y, back - .067, 'z')

        // Balconies do not enlarge building identity or its volume: small facade fittings.
        if (!lowPower && floor > 0 && i % 4 === 0 && col === 1 && y + .95 < b.h) {
          add('balconySlabs', x, y - .93, front + .42, 1.72, .115, .83)
          add('balconyGuards', x, y - .43, front + .82, 1.7, .79, .06)
        }
      }
      for (let col = 0; col < maxZ; col++) {
        const z = b.z - b.d / 2 + 1.3 + col * 2.1
        if (z > front - .7) continue
        window(right + .067, y, z, 'x')
        if (!lowPower) window(left - .067, y, z, 'x')
      }
    }
  })
  return result
}

export function ArchitecturalDistrictDetails({ buildings, lowPower }: {
  buildings: ExistingCityBuilding[]; lowPower: boolean
}) {
  const groups = useMemo(() => decorateBuildings(buildings, lowPower), [buildings, lowPower])
  return <>
    <DetailInstances pieces={groups.glass} color="#152c38" metallic={.27} roughness={.24}/>
    <DetailInstances pieces={groups.jambs} color="#64787b" metallic={.55} roughness={.44}/>
    <DetailInstances pieces={groups.lintels} color="#8c9691" metallic={.2} roughness={.62}/>
    <DetailInstances pieces={groups.plinths} color="#414b49" roughness={.9}/>
    <DetailInstances pieces={groups.seams} color="#596563" roughness={.87}/>
    <DetailInstances pieces={groups.doors} color="#26363a" metallic={.26} roughness={.47}/>
    <DetailInstances pieces={groups.balconySlabs} color="#838b83" roughness={.84}/>
    <DetailInstances pieces={groups.balconyGuards} color="#3b5055" metallic={.48} roughness={.42}/>
  </>
}
