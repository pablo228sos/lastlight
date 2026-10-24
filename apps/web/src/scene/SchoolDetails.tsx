import { useMemo } from 'react'
import { CanvasTexture, RepeatWrapping, SRGBColorSpace } from 'three'
import type { SceneLayer, VisualRehearsalState } from '../app/useMissionState'

function useMasonry() {
  return useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = 512
    canvas.height = 512
    const ctx = canvas.getContext('2d')!
    ctx.fillStyle = '#b5b7a9'
    ctx.fillRect(0, 0, 512, 512)
    for (let row = 0; row < 32; row++) {
      for (let col = -1; col < 16; col++) {
        const x = col * 36 + (row % 2) * 18
        const y = row * 16
        const variation = Math.sin(row * 21.7 + col * 8.9) * 7
        ctx.fillStyle = `rgb(${174 + variation},${177 + variation},${166 + variation})`
        ctx.fillRect(x + 1, y + 1, 34, 14)
        ctx.fillStyle = 'rgba(34,48,47,.12)'
        ctx.fillRect(x, y + 15, 36, 1)
      }
    }
    const texture = new CanvasTexture(canvas)
    texture.colorSpace = SRGBColorSpace
    texture.wrapS = RepeatWrapping
    texture.wrapT = RepeatWrapping
    texture.repeat.set(2, 1)
    texture.anisotropy = 4
    return texture
  }, [])
}

function WindowBay({ x, y, lit, emergency = false }: { x: number; y: number; lit: boolean; emergency?: boolean }) {
  const glow = emergency ? '#79d6c6' : '#e6ad6c'
  return <group position={[x, y, 13.2]}>
    <mesh position={[0, 0, -.02]}><boxGeometry args={[2.64, 1.88, .16]} /><meshStandardMaterial color="#253b40" roughness={.7} metalness={.45} /></mesh>
    <mesh position={[0, 0, .07]}><boxGeometry args={[2.4, 1.65, .035]} />
      <meshStandardMaterial color={lit ? (emergency ? '#5aaba4' : '#9d7750') : '#203b43'} emissive={glow} emissiveIntensity={lit ? (emergency ? 1.8 : .85) : .02} metalness={.2} roughness={.28} />
    </mesh>
    <mesh position={[0, 0, .1]}><boxGeometry args={[.065, 1.65, .06]} /><meshStandardMaterial color="#aab6a9" metalness={.5} /></mesh>
    <mesh position={[0, -.83, .16]}><boxGeometry args={[2.75, .12, .32]} /><meshStandardMaterial color="#c8c6b6" roughness={.84} /></mesh>
    <mesh position={[0, .85, .1]}><boxGeometry args={[2.75, .11, .22]} /><meshStandardMaterial color="#8b9990" /></mesh>
  </group>
}

function Photovoltaics() {
  return <group>
    {Array.from({ length: 12 }, (_, index) => {
      const x = -12 + (index % 6) * 4.5
      const z = 2.3 + Math.floor(index / 6) * 3.4
      return <group key={index} position={[x, 8.81, z]} rotation={[-.12, 0, 0]}>
        <mesh position={[0, .08, 0]}><boxGeometry args={[3.45, .035, 2.35]} /><meshStandardMaterial color="#17374a" metalness={.66} roughness={.25} /></mesh>
        {[-1.13, 0, 1.13].map(dx => <mesh key={dx} position={[dx, .108, 0]}><boxGeometry args={[.035, .013, 2.33]} /><meshBasicMaterial color="#719bad" /></mesh>)}
        {[-.58, 0, .58].map(dz => <mesh key={dz} position={[0, .108, dz]}><boxGeometry args={[3.4, .013, .035]} /><meshBasicMaterial color="#719bad" /></mesh>)}
        <mesh position={[0, -.16, -.9]}><boxGeometry args={[3.2, .3, .12]} /><meshStandardMaterial color="#596e72" metalness={.7} /></mesh>
      </group>
    })}
  </group>
}

export function SchoolDetails({ visual, layer }: { visual: VisualRehearsalState; layer: SceneLayer }) {
  const masonry = useMasonry()
  const frontBays = [-12, -8.8, -5.6, 5.6, 8.8, 12]
  const sideBays = [-.4, 2.9, 6.2, 9.5]
  return <group>
    <mesh position={[0, 4.05, 13.14]}><planeGeometry args={[29.65, 7.8]} /><meshStandardMaterial map={masonry} color="#d4d2c2" roughness={1} /></mesh>
    <mesh position={[15.04, 4.05, 6]} rotation={[0, Math.PI / 2, 0]}><planeGeometry args={[13.85, 7.8]} /><meshStandardMaterial map={masonry} color="#c8c9b9" roughness={1} /></mesh>
    <mesh position={[20.74, 3.1, 11]} rotation={[0, Math.PI / 2, 0]}><planeGeometry args={[8.9, 5.85]} /><meshStandardMaterial map={masonry} color="#b9c2b7" roughness={1} /></mesh>

    <mesh position={[0, .38, 13.29]}><boxGeometry args={[30.6, .65, .5]} /><meshStandardMaterial color="#45585a" roughness={.92} /></mesh>
    <mesh position={[0, 7.9, 13.24]}><boxGeometry args={[30.7, .34, .34]} /><meshStandardMaterial color="#d2cfbd" roughness={.86} /></mesh>
    <mesh position={[0, 4.15, 13.26]}><boxGeometry args={[30.7, .24, .27]} /><meshStandardMaterial color="#c4c6b6" /></mesh>
    {[-14.6, -4.05, 4.05, 14.6].map(x => <mesh key={x} position={[x, 4.03, 13.28]}><boxGeometry args={[.42, 7.75, .42]} /><meshStandardMaterial color="#e2d9c1" roughness={.92} /></mesh>)}

    {frontBays.flatMap(x => [2.35, 5.72].map(y => <WindowBay key={`${x}:${y}`} x={x} y={y} lit={visual.noncriticalLit} />))}
    {sideBays.flatMap(z => [2.4, 5.65].map(y => <group key={`${z}:${y}`} position={[15.19, y, z]} rotation={[0, Math.PI / 2, 0]}>
      <mesh><boxGeometry args={[2.45, 1.6, .08]} /><meshStandardMaterial color={visual.noncriticalLit ? '#a47e55' : '#213a41'} emissive="#daa261" emissiveIntensity={visual.noncriticalLit ? .9 : .02} metalness={.25} roughness={.34} /></mesh>
      <mesh position={[0, 0, .07]}><boxGeometry args={[.06, 1.65, .07]} /><meshStandardMaterial color="#b9c3b7" /></mesh>
      <mesh position={[0, -.86, .14]}><boxGeometry args={[2.7, .12, .36]} /><meshStandardMaterial color="#d4d2c0" /></mesh>
    </group>))}

    <mesh position={[0, 2.42, 13.34]}><boxGeometry args={[5.2, 4.3, .22]} /><meshStandardMaterial color="#25383d" metalness={.48} roughness={.38} /></mesh>
    {[-1.25, 0, 1.25].map(x => <mesh key={x} position={[x, 2.35, 13.48]}><boxGeometry args={[.065, 3.7, .08]} /><meshStandardMaterial color="#c5cfbd" metalness={.65} /></mesh>)}
    <mesh position={[0, 4.88, 13.5]}><boxGeometry args={[7.6, .58, .24]} /><meshStandardMaterial color="#e4d5b1" emissive="#f2b56c" emissiveIntensity={visual.noncriticalLit ? .7 : .02} /></mesh>
    <mesh position={[0, 4.9, 13.64]}><planeGeometry args={[6.8, .42]} /><meshBasicMaterial color="#263338" /></mesh>
    {[-3.6, 3.6].map(x => <mesh key={x} position={[x, 2.8, 15.13]}><boxGeometry args={[.18, 5.5, .2]} /><meshStandardMaterial color="#9fb1ac" metalness={.55} /></mesh>)}
    <mesh position={[0, 5.55, 15.2]}><boxGeometry args={[8.5, .22, 4.55]} /><meshStandardMaterial color="#28454c" metalness={.32} roughness={.48} /></mesh>
    <mesh position={[0, 5.4, 17.4]}><boxGeometry args={[8.5, .18, .25]} /><meshStandardMaterial color="#a6b5a9" /></mesh>
    {[-3, -1, 1, 3].map(x => <mesh key={x} position={[x, .2, 18.6]}><boxGeometry args={[1.8, .12, 5.5]} /><meshStandardMaterial color="#a2a99a" roughness={1} /></mesh>)}

    <Photovoltaics />
    <mesh position={[11.4, 9.25, 10.5]}><boxGeometry args={[5.2, 1.15, 2.8]} /><meshStandardMaterial color="#344850" metalness={.35} roughness={.6} /></mesh>
    {[9.8, 11, 12.2].map(x => <mesh key={x} position={[x, 9.27, 11.95]}><boxGeometry args={[.12, .58, .08]} /><meshStandardMaterial color="#91a5a4" metalness={.55} /></mesh>)}
    <mesh position={[11.4, 9.36, 10.5]}><boxGeometry args={[5.45, .1, 3.05]} /><meshStandardMaterial color="#788b8a" metalness={.25} /></mesh>

    <mesh position={[15.7, 3.12, 15.67]}><boxGeometry args={[9.7, 5.55, .16]} /><meshStandardMaterial color="#53696b" roughness={.65} /></mesh>
    {[12.25, 15.7, 19.15].map(x => <group key={x}>
      <mesh position={[x, 3.25, 15.78]}><boxGeometry args={[2.6, 1.9, .09]} /><meshStandardMaterial color={visual.criticalLit ? '#5aada7' : '#1a3b40'} emissive="#75d8cb" emissiveIntensity={visual.criticalLit ? 1.45 : .02} metalness={.15} /></mesh>
      <mesh position={[x, 3.25, 15.85]}><boxGeometry args={[.08, 1.95, .08]} /><meshStandardMaterial color="#d1ddd2" /></mesh>
    </group>)}
    <mesh position={[15.7, 5.95, 15.8]}><boxGeometry args={[10.3, .29, .42]} /><meshStandardMaterial color="#d4d9c9" roughness={.88} /></mesh>

    <mesh position={[18.05, .2, 5.65]}><boxGeometry args={[11.8, .18, 7.6]} /><meshStandardMaterial color="#69746e" roughness={.95} /></mesh>
    {[15.7, 19.4].map(x => <group key={x} position={[x, 0, 3.2]}>
      <mesh position={[0, .08, 0]}><boxGeometry args={[3.4, .17, 2.55]} /><meshStandardMaterial color="#364a4d" /></mesh>
      <mesh position={[0, 3.13, 0]}><boxGeometry args={[2.7, .17, 2.1]} /><meshStandardMaterial color="#859893" metalness={.45} /></mesh>
      {[-.85, .85].map(dx => <mesh key={dx} position={[dx, 1.7, .99]}><boxGeometry args={[.035, 2.45, .06]} /><meshStandardMaterial color="#9fb8b5" metalness={.64} /></mesh>)}
      <mesh position={[0, .5, 1.07]}><boxGeometry args={[1.4, .13, .05]} /><meshStandardMaterial color="#80a69f" emissive="#6cc8ba" emissiveIntensity={layer === 'power' && visual.criticalLit ? .55 : .05} /></mesh>
    </group>)}

    <mesh position={[-18, .13, 17]}><boxGeometry args={[20, .035, 15]} /><meshStandardMaterial color="#3e5554" roughness={1} /></mesh>
    {[[-24, 12], [-12, 12], [-24, 22], [-12, 22]].map(([x, z], i) => <group key={i} position={[x, 0, z]}>
      <mesh position={[0, .19, 0]}><cylinderGeometry args={[1.1, 1.35, .24, 12]} /><meshStandardMaterial color="#71837a" /></mesh>
      <mesh position={[0, 1.8, 0]}><cylinderGeometry args={[.15, .22, 3.3, 8]} /><meshStandardMaterial color="#3d4139" /></mesh>
      <mesh position={[0, 3.6, 0]}><coneGeometry args={[1.45, 3.8, 9]} /><meshStandardMaterial color="#263e35" roughness={1} flatShading /></mesh>
    </group>)}
    {[-21, -15].map(x => <mesh key={x} position={[x, .24, 17]}><boxGeometry args={[.24, .08, 13.6]} /><meshStandardMaterial color="#aab0a0" /></mesh>)}
  </group>
}
