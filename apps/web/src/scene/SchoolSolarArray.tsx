/**
 * LASTLIGHT / Issue #4 — school rooftop PV material detail.
 *
 * Exactly the original 12 installed module positions. This component adds a
 * deterministic photovoltaic cell pattern, aluminum perimeter and mounting
 * rails; it does not change the school, roof or neighboring geometry.
 *
 * 6x4 visible CELL motifs are drawn inside EACH existing panel.
 * Cells are material graphics, not additional solar panel modules.
 */
import { useEffect, useMemo } from 'react'
import { CanvasTexture, SRGBColorSpace } from 'three'
import type { Texture } from 'three'

export const SCHOOL_PV_MODULE_COUNT = 12 as const
const COLUMN_COUNT = 6
const ROW_COUNT = 2

const positions: Array<[number, number]> = Array.from(
  { length: SCHOOL_PV_MODULE_COUNT },
  (_, i) => [-12 + (i % COLUMN_COUNT) * 4.5, 2.3 + Math.floor(i / COLUMN_COUNT) * 3.4],
)

function makeSolarCellsTexture(): CanvasTexture {
  const canvas = document.createElement('canvas')
  canvas.width = 1024
  canvas.height = 704
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('LASTLIGHT: cannot create PV cell pattern')

  // Near-black glass and subdued, directional midnight-blue cells.
  ctx.fillStyle = '#081622'
  ctx.fillRect(0, 0, canvas.width, canvas.height)
  const columns = 6, rows = 4
  const padX = 26, padY = 20, gap = 7
  const cellW = (canvas.width - padX * 2 - (columns - 1) * gap) / columns
  const cellH = (canvas.height - padY * 2 - (rows - 1) * gap) / rows

  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < columns; col++) {
      const x = padX + col * (cellW + gap)
      const y = padY + row * (cellH + gap)
      const light = (col + row) % 3
      const gradient = ctx.createLinearGradient(x, y, x + cellW, y + cellH)
      gradient.addColorStop(0, light === 0 ? '#163549' : '#112c40')
      gradient.addColorStop(0.52, light === 2 ? '#1b4659' : '#194054')
      gradient.addColorStop(1, '#0a2537')
      ctx.fillStyle = gradient
      ctx.fillRect(x, y, cellW, cellH)

      // Cell borders and two fine vertical conductors, deliberately subdued.
      ctx.strokeStyle = 'rgba(126,178,188,0.28)'
      ctx.lineWidth = 2
      ctx.strokeRect(x + 1, y + 1, cellW - 2, cellH - 2)
      ctx.strokeStyle = 'rgba(180,207,207,0.35)'
      ctx.lineWidth = 2
      for (const frac of [0.34, 0.66]) {
        const bx = x + cellW * frac
        ctx.beginPath()
        ctx.moveTo(bx, y + 5)
        ctx.lineTo(bx, y + cellH - 5)
        ctx.stroke()
      }

      // Deterministic low-contrast polycrystalline marks: no random animation.
      ctx.strokeStyle = 'rgba(121,172,185,0.08)'
      ctx.lineWidth = 1
      for (let k = 0; k < 5; k++) {
        const sx = x + 8 + ((k * 27 + col * 11) % Math.floor(cellW - 16))
        const sy = y + 12 + ((k * 31 + row * 9) % Math.floor(cellH - 24))
        ctx.beginPath()
        ctx.moveTo(sx, sy)
        ctx.lineTo(sx + 16, sy + 9)
        ctx.stroke()
      }
    }
  }

  // Glass glazing glare stays in the texture and never emits its own light.
  const glaze = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
  glaze.addColorStop(0, 'rgba(190,224,228,0.10)')
  glaze.addColorStop(0.38, 'rgba(190,224,228,0.015)')
  glaze.addColorStop(0.7, 'rgba(3,9,14,0.12)')
  glaze.addColorStop(1, 'rgba(3,9,14,0)')
  ctx.fillStyle = glaze
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  const texture = new CanvasTexture(canvas)
  texture.colorSpace = SRGBColorSpace
  texture.anisotropy = 4
  return texture
}

function SolarModule({ x, z, cells }: { x: number; z: number; cells: Texture }) {
  return (
    <group position={[x, 8.75, z]} rotation={[-0.12, 0, 0]}>
      {/* Original outer module footprint: 3.7 x .12 x 2.6. */}
      <mesh castShadow receiveShadow>
        <boxGeometry args={[3.7, 0.12, 2.6]} />
        <meshStandardMaterial color="#182b34" metalness={0.58} roughness={0.34} />
      </mesh>
      {/* Original visible glass size and height; cell pattern is a texture. */}
      <mesh castShadow receiveShadow position={[0, 0.075, 0]}>
        <boxGeometry args={[3.45, 0.025, 2.35]} />
        <meshPhysicalMaterial map={cells} metalness={0.24} roughness={0.18}
          clearcoat={0.75} clearcoatRoughness={0.16} />
      </mesh>

      {/* Light-catching aluminum framing, inside the existing footprint. */}
      {[-1.745, 1.745].map(side => (
        <mesh key={'vertical-' + side} position={[side, 0.098, 0]} castShadow>
          <boxGeometry args={[0.05, 0.042, 2.43]} />
          <meshStandardMaterial color="#718b8f" metalness={0.77} roughness={0.3} />
        </mesh>
      ))}
      {[-1.19, 1.19].map(side => (
        <mesh key={'horizontal-' + side} position={[0, 0.098, side]} castShadow>
          <boxGeometry args={[3.52, 0.042, 0.052]} />
          <meshStandardMaterial color="#718b8f" metalness={0.77} roughness={0.3} />
        </mesh>
      ))}

      {/* Two support rails underneath each existing module; no new PV units. */}
      {[-1.13, 1.13].map(side => (
        <mesh key={'mount-' + side} position={[side, -0.069, 0]} castShadow>
          <boxGeometry args={[0.095, 0.055, 2.42]} />
          <meshStandardMaterial color="#41545b" metalness={0.68} roughness={0.48} />
        </mesh>
      ))}
    </group>
  )
}

export function SchoolSolarArray() {
  const cells = useMemo(makeSolarCellsTexture, [])
  useEffect(() => () => cells.dispose(), [cells])
  return <>
    {positions.map(([x, z], i) => <SolarModule key={i} x={x} z={z} cells={cells} />)}
  </>
}
