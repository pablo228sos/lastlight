import { useEffect, useRef } from 'react'
import { useThree } from '@react-three/fiber'
import gsap from 'gsap'
import { Vector3 } from 'three'
import type { CameraShotId, ScenePhase } from '../app/useMissionState'
import { SHOTS } from '../app/useMissionState'
import type { SiteId } from '../features/sites'

// Shot timing follows elapsed time even when a software renderer drops frames.
gsap.ticker.lagSmoothing(0)

const siteCenters: Record<Exclude<SiteId, 'school'>, [number, number]> = {
  clinic: [-58, -54], business: [74, -53], residential: [-58, 74],
}

type Props = {
  shot: CameraShotId; phase: ScenePhase; siteId: SiteId; paused: boolean
  reducedMotion: boolean; onDescentComplete: () => void
}

export function CameraDirector({ shot, phase, siteId, paused, reducedMotion, onDescentComplete }: Props) {
  const { camera, gl } = useThree()
  const target = useRef(new Vector3(...SHOTS.orbital.target))
  const timeline = useRef<gsap.core.Timeline | null>(null)
  const phaseRef = useRef(phase)
  useEffect(() => { phaseRef.current = phase }, [phase])

  useEffect(() => {
    camera.position.set(...SHOTS.orbital.position)
    camera.lookAt(target.current)
  }, [camera])

  useEffect(() => {
    timeline.current?.kill()
    document.documentElement.dataset.cameraIdle = 'false'
    document.documentElement.dataset.cameraShot = shot
    const state = { x: camera.position.x, y: camera.position.y, z: camera.position.z,
      tx: target.current.x, ty: target.current.y, tz: target.current.z }
    const move = (id: CameraShotId, at?: number) => {
      const pose = SHOTS[id]
      const center = siteId === 'school' ? null : siteCenters[siteId]
      const local = center && (id === 'facility' || id === 'equipment' || id === 'orbit')
      const residential = siteId === 'residential'
      const relative = id === 'orbit' ? residential ? [45, 43, -40] : [38, 34, -38] :
        id === 'equipment' ? residential ? [39, 34, 37] : [32, 25, 35] :
          residential ? [52, 45, 47] : [42, 32, 47]
      const destination = local && center ? {
        x: center[0] + relative[0], y: relative[1], z: center[1] + relative[2],
        tx: center[0], ty: residential ? 5 : 2, tz: center[1],
      } : { x: pose.position[0], y: pose.position[1], z: pose.position[2],
        tx: pose.target[0], ty: pose.target[1], tz: pose.target[2] }
      if (reducedMotion || pose.duration === 0) {
        Object.assign(state, destination)
        camera.position.set(state.x, state.y, state.z)
        target.current.set(state.tx, state.ty, state.tz)
        camera.lookAt(target.current)
        return
      }
      if (!timeline.current) timeline.current = gsap.timeline()
      timeline.current.to(state, { ...destination, duration: pose.duration, ease: pose.ease,
        onUpdate: () => { camera.position.set(state.x, state.y, state.z); target.current.set(state.tx, state.ty, state.tz); camera.lookAt(target.current) },
      }, at)
    }
    if (shot === 'corridor') {
      move('corridor')
      move('district')
      if (reducedMotion) { document.documentElement.dataset.cameraIdle = 'true'; onDescentComplete() }
      else timeline.current?.eventCallback('onComplete', () => {
        document.documentElement.dataset.cameraIdle = 'true'
        onDescentComplete()
      })
    } else move(shot)
    if (shot !== 'corridor') {
      if (!timeline.current) document.documentElement.dataset.cameraIdle = 'true'
      else timeline.current.eventCallback('onComplete', () => { document.documentElement.dataset.cameraIdle = 'true' })
    }
    return () => { timeline.current?.kill(); timeline.current = null }
  }, [camera, shot, siteId, reducedMotion, onDescentComplete])

  useEffect(() => { if (paused) timeline.current?.pause(); else timeline.current?.resume() }, [paused])

  useEffect(() => {
    const canvas = gl.domElement
    let lastX = 0, lastY = 0, dragging = false
    const down = (event: PointerEvent) => {
      if (phaseRef.current === 'INTRO' || phaseRef.current === 'DESCENT') return
      dragging = true; lastX = event.clientX; lastY = event.clientY; canvas.setPointerCapture(event.pointerId)
    }
    const move = (event: PointerEvent) => {
      if (!dragging || timeline.current?.isActive()) return
      const dx = event.clientX - lastX, dy = event.clientY - lastY
      lastX = event.clientX; lastY = event.clientY
      const direction = new Vector3().subVectors(camera.position, target.current)
      const theta = Math.atan2(direction.x, direction.z) - dx * .004
      const radius = Math.sqrt(direction.x ** 2 + direction.z ** 2)
      const y = Math.max(8, Math.min(150, direction.y + dy * .13))
      camera.position.set(target.current.x + Math.sin(theta) * radius, target.current.y + y, target.current.z + Math.cos(theta) * radius)
      camera.lookAt(target.current)
    }
    const up = () => { dragging = false }
    const wheel = (event: WheelEvent) => {
      if (phaseRef.current === 'INTRO' || phaseRef.current === 'DESCENT' || timeline.current?.isActive()) return
      event.preventDefault()
      const vector = new Vector3().subVectors(camera.position, target.current)
      const distance = Math.max(17, Math.min(260, vector.length() * (event.deltaY > 0 ? 1.11 : .89)))
      camera.position.copy(target.current).add(vector.normalize().multiplyScalar(distance))
      camera.lookAt(target.current)
    }
    canvas.addEventListener('pointerdown', down); canvas.addEventListener('pointermove', move)
    canvas.addEventListener('pointerup', up); canvas.addEventListener('pointercancel', up)
    canvas.addEventListener('wheel', wheel, { passive: false })
    return () => { canvas.removeEventListener('pointerdown', down); canvas.removeEventListener('pointermove', move)
      canvas.removeEventListener('pointerup', up); canvas.removeEventListener('pointercancel', up); canvas.removeEventListener('wheel', wheel) }
  }, [camera, gl])
  return null
}
