/**
 * LASTLIGHT Issue #4 | proposed PBR material for two existing school bodies.
 * No changes to facade transforms, cameras, 12 rooftop PV modules or power physics.
 * Works with 1024px tileable *procedural fallback* maps in public/assets/materials/facade02.
 */
import { Suspense, useEffect, useMemo } from 'react'
import { useLoader } from '@react-three/fiber'
import { BoxGeometry, NoColorSpace, RepeatWrapping, SRGBColorSpace, TextureLoader, Vector2 } from 'three'

const ROOT = '/assets/materials/facade02/'
const MAPS = [
  ROOT + 'facade02_mineral_concrete_basecolor_srgb_1024.png',
  ROOT + 'facade02_mineral_concrete_roughness_linear_1024.png',
  ROOT + 'facade02_mineral_concrete_normal_opengl_1024.png',
]

type Variant = 'main' | 'annex'
type WallSpec = {
  position: [number,number,number]
  size: [number,number,number]
  fallback: string
  fallbackRoughness: number
  fallbackMetalness: number
  receiveShadow: boolean
}
const SPECS: Record<Variant, WallSpec> = {
  main: {
    position: [0,4.1,6], size: [30,8,14], fallback: '#a0a69d',
    fallbackRoughness: 0.88, fallbackMetalness: 0.05, receiveShadow: true,
  },
  annex: {
    position: [15.7,3.1,11], size: [10,6,9], fallback: '#9a9f93',
    fallbackRoughness: 0.9, fallbackMetalness: 0, receiveShadow: false,
  },
}
const NORMAL_SCALE = new Vector2(0.16, 0.16)
function uvBox(size: WallSpec['size']) {
  // New UVs ONLY: same BoxGeometry width, height, depth and same vertices.
  const [width,height,depth]=size
  const g=new BoxGeometry(width,height,depth)
  const uv=g.getAttribute('uv'), normals=g.getAttribute('normal')
  for(let i=0;i<uv.count;i++){
    const nx=Math.abs(normals.getX(i))>0.5, ny=Math.abs(normals.getY(i))>0.5
    const w=nx?depth:width, h=ny?depth:height
    // Integer repeat counts: no half-tile discontinuity at facade corners.
    uv.setXY(i, uv.getX(i)*Math.max(1,Math.round(w/4)), uv.getY(i)*Math.max(1,Math.round(h/4)))
  }
  uv.needsUpdate=true
  return g
}
function LoadedFacadeMaterial() {
  const [base,rough,normal]=useLoader(TextureLoader,MAPS)
  useMemo(()=>{
    base.colorSpace=SRGBColorSpace
    rough.colorSpace=NoColorSpace
    normal.colorSpace=NoColorSpace
    for(const tex of [base,rough,normal]){
      tex.wrapS=RepeatWrapping
      tex.wrapT=RepeatWrapping
      tex.anisotropy=4
      tex.needsUpdate=true
    }
  },[base,rough,normal])
  return <meshStandardMaterial map={base} roughnessMap={rough} normalMap={normal}
    roughness={0.96} metalness={0} normalScale={NORMAL_SCALE}/>
}
export function SchoolFacadeWall({variant}:{variant:Variant}) {
  const spec=SPECS[variant]
  const geometry=useMemo(()=>uvBox(spec.size),[spec])
  useEffect(()=>()=>geometry.dispose(),[geometry])
  return <mesh position={spec.position} castShadow receiveShadow={spec.receiveShadow}>
    <primitive object={geometry} attach="geometry"/>
    <Suspense fallback={<meshStandardMaterial color={spec.fallback}
      roughness={spec.fallbackRoughness} metalness={spec.fallbackMetalness}/>}>
      <LoadedFacadeMaterial/>
    </Suspense>
  </mesh>
}
