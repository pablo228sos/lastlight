/**
 * Hero-school mineral plaster / source-locked mesh sizes.
 * Replaces visually blotchy v02 photographic-looking noise with deterministic
 * fine-grain plaster; no baked shadows. The original PNG candidates remain
 * in the repository for comparison, but are intentionally not active here.
 */
import { useEffect, useMemo } from 'react'
import { BoxGeometry, CanvasTexture, RepeatWrapping, SRGBColorSpace } from 'three'

type Variant='main'|'annex'
const SPECS:Record<Variant,{
  position:[number,number,number];size:[number,number,number];tone:string
}>={
  main:{position:[0,4.1,6],size:[30,8,14],tone:'#dce0da'},
  annex:{position:[15.7,3.1,11],size:[10,6,9],tone:'#cad2cc'},
}
function makePlasterTile(){
  const c=document.createElement('canvas')
  c.width=c.height=256
  const g=c.getContext('2d')
  if(!g) throw new Error('2D canvas unavailable')
  const data=g.createImageData(256,256)
  for(let y=0;y<256;y++)for(let x=0;x<256;x++){
    const index=(y*256+x)*4
    // Subtle aggregate: max +/- 7 of 255, no large-scale clouds.
    let hash=((x*374761393)^(y*668265263))>>>0
    hash=Math.imul(hash^(hash>>>13),1274126177)>>>0
    const noise=((hash^(hash>>>16))>>>0)/4294967295
    const shade=Math.round(232+(noise-.5)*13)
    data.data[index]=shade
    data.data[index+1]=shade
    data.data[index+2]=shade-2
    data.data[index+3]=255
  }
  // Pixel-matched boundaries prevent visible seams at repeated UV edges.
  for(let k=0;k<256;k++){
    for(let j=0;j<4;j++){
      data.data[(k*256+255)*4+j]=data.data[(k*256)*4+j]
      data.data[((255*256+k)*4)+j]=data.data[(k*4)+j]
    }
  }
  g.putImageData(data,0,0)
  const t=new CanvasTexture(c)
  t.colorSpace=SRGBColorSpace
  t.wrapS=t.wrapT=RepeatWrapping
  t.anisotropy=4
  return t
}
function sameBoxWithPhysicalUV(size:[number,number,number]){
  const [width,height,depth]=size
  const g=new BoxGeometry(width,height,depth)
  const uv=g.getAttribute('uv'),normal=g.getAttribute('normal')
  for(let i=0;i<uv.count;i++){
    const nx=Math.abs(normal.getX(i))>.5,ny=Math.abs(normal.getY(i))>.5
    const faceW=nx?depth:width,faceH=ny?depth:height
    uv.setXY(i,uv.getX(i)*Math.max(1,Math.round(faceW/4)),
      uv.getY(i)*Math.max(1,Math.round(faceH/4)))
  }
  uv.needsUpdate=true
  return g
}
export function SchoolFacadeWall({variant}:{variant:Variant}){
  const spec=SPECS[variant]
  const map=useMemo(makePlasterTile,[])
  const geometry=useMemo(()=>sameBoxWithPhysicalUV(spec.size),[spec])
  useEffect(()=>()=>{geometry.dispose();map.dispose()},[geometry,map])
  return <mesh position={spec.position} castShadow receiveShadow>
    <primitive object={geometry} attach="geometry"/>
    <meshStandardMaterial map={map} color={spec.tone} roughness={.91} metalness={.015}/>
  </mesh>
}
