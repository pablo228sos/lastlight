import { useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Vector3 } from 'three'

// React owns the buttons. The 3D scene only projects their positions, avoiding
// nested React roots while camera shots and layers change in the same frame.
const anchors = [
  ['hotspot-pv', 8, 10.6, 14],
  ['hotspot-battery', 35.5, 5.5, 10.3],
  ['hotspot-inverter', 23.5, 4.9, 10.3],
  ['hotspot-clinic', -58, 12, -54],
  ['hotspot-business', 74, 12, -53],
  ['hotspot-residential', -58, 12, 74],
] as const

export function HotspotProjection() {
  const point = useMemo(() => new Vector3(), [])
  useFrame(({ camera, gl }) => {
    const width = gl.domElement.clientWidth
    const height = gl.domElement.clientHeight
    for (const [id, x, y, z] of anchors) {
      const element = document.getElementById(id)
      if (!element) continue
      point.set(x, y, z).project(camera)
      const left = (point.x + 1) * width / 2
      const top = (1 - point.y) * height / 2
      const districtLabel = id === 'hotspot-clinic' || id === 'hotspot-business' || id === 'hotspot-residential'
      const underEditorial = districtLabel && left < Math.min(530, width * .4) && top < 315
      const underControls = districtLabel && top > height - 230
      element.style.visibility = point.z > -1 && point.z < 1 && !underEditorial && !underControls ? 'visible' : 'hidden'
      element.style.left = `${left}px`
      element.style.top = `${top}px`
    }
  })
  return null
}
