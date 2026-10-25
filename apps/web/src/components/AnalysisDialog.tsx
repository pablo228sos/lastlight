import { useEffect, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'

export function AnalysisDialog({ title, label, onClose, children, closeLabel, testId }: { title: string; label: string; onClose: () => void; children: ReactNode; closeLabel?: string; testId?: string }) {
  const panel = useRef<HTMLElement>(null)
  const dismiss = useRef<HTMLButtonElement>(null)
  const callback = useRef(onClose)
  useEffect(() => { callback.current = onClose }, [onClose])
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    dismiss.current?.focus()
    const key = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { event.stopImmediatePropagation(); callback.current(); return }
      if (event.key !== 'Tab') return
      const nodes = [...(panel.current?.querySelectorAll<HTMLElement>('button:not(:disabled),a[href],input,select,[tabindex="0"]') ?? [])].filter(node => node.getClientRects().length)
      const first = nodes[0], last = nodes.at(-1)
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
    }
    window.addEventListener('keydown', key, true)
    return () => { window.removeEventListener('keydown', key, true); previous?.focus() }
  }, [])
  return createPortal(<div className="frontier-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}>
    <section ref={panel} className="frontier-panel intelligence-panel" role="dialog" aria-modal="true" aria-label={title} data-testid={testId}>
      <header><span>{label}</span><button ref={dismiss} onClick={onClose} aria-label={closeLabel ?? `Close ${title}`}>×</button></header>
      {children}
    </section>
  </div>, document.body)
}
