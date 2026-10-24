import { useEffect, useRef } from 'react'
import { useFrame, useThree } from '@react-three/fiber'
import gsap from 'gsap'
import { Vector3 } from 'three'
import type { CameraShotId, ScenePhase } from '../app/useMissionState'
import { SHOTS } from '../app/useMissionState'
import type { SiteId } from '../features/sites'

const siteOffsets: Record<SiteId, [number, number]> = {
  school: [0, 0], clinic: [-71, -61], business: [61, -60], residential: [-71, 67],
}

type Props = {
  shot: CameraShotId; phase: ScenePhase; siteId: SiteId; paused: boolean
  reducedMotion: boolean; onDescentComplete: () => void
}

export function CameraDirector({ shot, phase, siteId, paused, reducedMotion, onDescentComplete }: Props) {
  const { camera, gl } = useThree()
  const exposeCapturePose = new URLSearchParams(window.location.search).has('capture')

  // Test-only observation: never mutates camera transforms, camera targets or
  // animation timelines. Browser art tests wait for the actual destination pose.
  useFrame(() => {
    if (!exposeCapturePose) return
    gl.domElement.dataset.cameraPosition = [
      camera.position.x.toFixed(3),
      camera.position.y.toFixed(3),
      camera.position.z.toFixed(3),
    ].join(',')
  })
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
    const offset = siteId === 'school' ? [0, 0] : siteOffsets[siteId]
    const state = { x: camera.position.x, y: camera.position.y, z: camera.position.z,
      tx: target.current.x, ty: target.current.y, tz: target.current.z }
    const move = (id: CameraShotId, at?: number) => {
      const pose = SHOTS[id]
      const [ox, oz] = id === 'facility' || id === 'equipment' || id === 'orbit' ? offset : [0, 0]
      const destination = { x: pose.position[0] + ox, y: pose.position[1], z: pose.position[2] + oz,
        tx: pose.target[0] + ox, ty: pose.target[1], tz: pose.target[2] + oz }
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
      if (reducedMotion) onDescentComplete()
      else timeline.current?.eventCallback('onComplete', onDescentComplete)
    } else move(shot)
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
