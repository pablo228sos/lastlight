/**
 * Issue #4: real browser captures for manual, screenshot-locked visual review.
 * Intentionally NOT in the normal test:smoke suite unless ISSUE04_CAPTURE=1.
 * Do not confuse these real WebGL pixels with AI concepts or approved art.
 */
import { test, expect } from '@playwright/test'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const enabled = process.env.ISSUE04_CAPTURE === '1'
const out = resolve(process.cwd(), 'artifacts', 'issue04')
test('capture one unchanged school from one WebGL canvas', async ({ page }) => {
  test.setTimeout(120_000)
  test.skip(!enabled, 'Only used by the dedicated Issue #4 art-review workflow')
  const errors: string[] = []
  const captures: Array<Record<string, string | number>> = []
  page.on('pageerror', error => errors.push(error.message))

  await mkdir(out, { recursive: true })
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/?capture=1')
  await expect(page.locator('canvas')).toBeVisible()

  const take = async (label: string, expectedShot: string, expectedPhase: string) => {
    const main = page.locator('main')
    await expect(main).toHaveAttribute('data-shot', expectedShot)
    await expect(main).toHaveAttribute('data-phase', expectedPhase)
    const pngUrl = await page.locator('canvas').evaluate((canvas: HTMLCanvasElement) => canvas.toDataURL('image/png'))
    expect(pngUrl.startsWith('data:image/png;base64,')).toBe(true)
    const png = Buffer.from(pngUrl.split(',')[1], 'base64')
    expect(png.byteLength).toBeGreaterThan(20_000)
    await writeFile(resolve(out, label + '-canvas.png'), png)
    await page.screenshot({ path: resolve(out, label + '-with-ui.png'), animations: 'disabled' })
    captures.push({
      label,
      shot: expectedShot,
      phase: expectedPhase,
      grid: await main.getAttribute('data-visual-step') ?? 'unknown',
      canvasWidth: await page.locator('canvas').evaluate((c: HTMLCanvasElement) => c.width),
      canvasHeight: await page.locator('canvas').evaluate((c: HTMLCanvasElement) => c.height),
      pngBytes: png.byteLength,
    })
  }

  // Navigate using exactly the same app state machine and virtual camera.
  await page.getByTestId('skip-intro').click()
  await expect(page.locator('main')).toHaveAttribute('data-phase', 'DISTRICT')
  await page.getByTestId('site-school').click()
  await page.waitForTimeout(2400)
  await take('01-facility-connected', 'facility', 'SITE')

  // Outage changes lights and visual rehearsal only; camera stays at facility.
  await page.getByTestId('disconnect-grid').click()
  await expect(page.locator('main')).toHaveAttribute('data-visual-step', '1')
  await page.waitForTimeout(1900)
  await take('02-facility-blackout', 'facility', 'BLACKOUT')

  await page.getByTestId('reset-scene').click()
  await expect(page.locator('main')).toHaveAttribute('data-visual-step', '0')
  await page.waitForTimeout(2000)
  await take('03-facility-reset', 'facility', 'INSPECT')

  // Equipment is another pose of the SAME world, not a second generated view.
  await page.getByTestId('inspect').click()
  await page.waitForTimeout(2000)
  await take('04-equipment', 'equipment', 'INSPECT')

  expect(errors).toEqual([])
  await writeFile(resolve(out, 'capture-manifest.json'), JSON.stringify({
    generatedAt: new Date().toISOString(),
    commit: process.env.GITHUB_SHA ?? 'local',
    cameraSource: 'apps/web/src/app/useMissionState.ts',
    sourceOfTruth: 'apps/web/src/scene/DistrictWorld.tsx',
    sourceGeometryChangedByThisTest: false,
    realBrowserCaptures: true,
    visualQualityApproved: false,
    noPhysicsClaim: true,
    details: 'These frames are actual WebGL output from the PR. Manual visual continuity approval is still required.',
    captures,
  }, null, 2))
})
