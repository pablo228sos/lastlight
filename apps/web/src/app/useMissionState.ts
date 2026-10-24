import { useState } from 'react'
import type { SiteId } from '../features/sites'

export type View = 'mission' | 'theater'
export type Layer = 'night' | 'systems'

export function useMissionState() {
  const [view, setView] = useState<View>('mission')
  const [siteId, setSiteId] = useState<SiteId>('school')
  const [layer, setLayer] = useState<Layer>('night')
  const [evidenceOpen, setEvidenceOpen] = useState(false)
  return { view, setView, siteId, setSiteId, layer, setLayer, evidenceOpen, setEvidenceOpen }
}
