/**
 * Read-only official-release WebGL acceptance.
 * This file is staged from Draft PR #15 into an EPHEMERAL GitHub Actions
 * checkout of integration/release-candidate. No changes are committed there.
 *
 * Authentic source: official PR #13 + live official Python physics service.
 * Screenshot evidence is valid only when all assertions pass.
 */
import { test, expect, type Page } from '@playwright/test'
import { mkdir, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const SHOT = 'facility'
const POSE = [78, 50, 73]
const TARGET = [13, 3, 7]
const output = resolve(process.cwd(), 'artifacts', 'issue04', 'official-release')
const observations: Record<string, unknown>[] = []

async function settled(page: Page, shot: string) {
  await expect(page.locator('main')).toHaveAttribute('data-shot', shot)
  await expect(page.locator('html')).toHaveAttribute('data-camera-idle', 'true', { timeout: 30000 })
  // The camera animation is complete; allow the actual WebGL renderer and
  // damping of emissive surfaces to settle before capturing a new frame.
  await page.waitForTimeout(2600)
}

async function capture(page: Page, name: string, expected: {
  phase: string, shot: string, source: string, critical: string,
}) {
  const main = page.locator('main')
  await expect(main).toHaveAttribute('data-phase', expected.phase)
  await expect(main).toHaveAttribute('data-shot', expected.shot)
  await expect(main).toHaveAttribute('data-physics-source', expected.source)
  await expect(main).toHaveAttribute('data-critical-lit', expected.critical)
  await settled(page, expected.shot)
  const attributes = await main.evaluate((element) => ({
    phase: element.getAttribute('data-phase'),
    shot: element.getAttribute('data-shot'),
    physicsSource: element.getAttribute('data-physics-source'),
    criticalLit: element.getAttribute('data-critical-lit'),
    quality: element.getAttribute('data-quality'),
  }))
  // Actual WebGL canvas rather than a synthetic or AI-generated image.
  const canvas = page.locator('canvas')
  await canvas.screenshot({ path: resolve(output, name + '-webgl.png') })
  await page.screenshot({ path: resolve(output, name + '-ui.png') })
  observations.push({
    name, ...attributes,
    cameraPoseFromVerifiedReleaseSource:
      expected.shot === SHOT ? { position: POSE, target: TARGET } : null,
    settledMarker: await page.locator('html').getAttribute('data-camera-idle'),
    display: await canvas.evaluate(c => ({
      width: c.clientWidth, height: c.clientHeight,
      bufferWidth: (c as HTMLCanvasElement).width,
      bufferHeight: (c as HTMLCanvasElement).height,
    })),
  })
}

async function seek(page: Page, hour: number) {
  await page.getByTestId('simulation-scrub').evaluate((element, value) => {
    const input = element as HTMLInputElement
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set
    setter?.call(input, String(value))
    input.dispatchEvent(new Event('input', { bubbles: true }))
    input.dispatchEvent(new Event('change', { bubbles: true }))
  }, hour)
}

test('official PR13: real engine connected, blackout, sustained, failed, reset, equipment', async ({page}) => {
  test.setTimeout(240000)
  test.skip(process.env.LASTLIGHT_RELEASE_ACCEPTANCE !== '1', 'Dedicated official release evidence job')
  observations.length = 0
  await mkdir(output, { recursive: true })
  const errors:string[] = []
  page.on('pageerror', e => errors.push(e.message))
  await page.setViewportSize({width: 1440, height: 900})
  await page.goto('/?capture=1')
  await expect(page.locator('canvas')).toBeVisible()
  await page.getByTestId('skip-intro').click()
  await page.getByTestId('site-school').click()
  await capture(page,'01-connected', {
    phase:'SITE',shot:'facility',source:'none',critical:'true',
  })

  await page.getByTestId('disconnect-grid').click()
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await expect(page.locator('main')).toHaveAttribute('data-physics-source','live',{timeout:30000})
  await page.getByTestId('simulation-play').click() // stop auto-play
  await seek(page,0)
  await capture(page,'02-grid-disconnected', {
    phase:'BLACKOUT',shot:'facility',source:'live',critical:'true',
  })
  await seek(page,8.7)
  await expect(page.getByTestId('critical-coverage')).toContainText('1.50 / 1.50')
  await capture(page,'03-critical-supplied', {
    phase:'BLACKOUT',shot:'facility',source:'live',critical:'true',
  })
  await seek(page,9.121)
  await expect(page.getByTestId('critical-coverage')).toContainText('0.00 / 1.50')
  await expect(page.getByTestId('failure-summary')).toContainText('09:07:12')
  await capture(page,'04-critical-failure', {
    phase:'BLACKOUT',shot:'facility',source:'live',critical:'false',
  })

  await page.getByTestId('reset-scene').click()
  await capture(page,'05-reset', {
    phase:'INSPECT',shot:'facility',source:'none',critical:'true',
  })

  await page.getByTestId('inspect').click()
  await capture(page,'06-equipment', {
    phase:'INSPECT',shot:'equipment',source:'none',critical:'true',
  })
  await page.getByTestId('layer-power').click()
  await expect(page.getByTestId('layer-power')).toHaveClass(/selected/)
  await expect(page.locator('main')).toHaveAttribute('data-physics-source','none')

  expect(errors).toEqual([])
  await writeFile(resolve(output,'manifest.json'),JSON.stringify({
    releaseBranch:'integration/release-candidate',
    releaseSha:process.env.LASTLIGHT_OFFICIAL_RELEASE_SHA,
    source:'official release checkout + live official localhost Physics API + Chromium WebGL',
    aiGenerated:false,
    connectedAndResetPresentationNotPhysicsTrace:true,
    realFailurePhysicsTrace:true,
    shotSourcePath:'apps/web/src/app/useMissionState.ts',
    facilityPose: {position:POSE,target:TARGET},
    disclaimer:'Pose is checked by official shot ID and GSAP idle marker; renderer camera quaternion is not separately instrumented.',
    performance:{fpsDistribution:null,rendererCalls:null,representativeWindowsHardware:false,
      reason:'CI Chromium uses software/virtualized GPU, not a representative Windows laptop.'},
    screenshots:observations,
    browser:await page.evaluate(()=>({userAgent:navigator.userAgent,hardwareConcurrency:navigator.hardwareConcurrency})),
    jsErrors:errors,
  },null,2)+'\n')
})
