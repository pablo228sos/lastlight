import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const require = createRequire(new URL('../../../apps/web/package.json', import.meta.url))
const { chromium, expect } = require('@playwright/test')
const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const url = process.env.LASTLIGHT_WEB_URL || 'http://127.0.0.1:4173'
const browser = await chromium.launch({
  channel: 'chrome',
  headless: true,
  args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'],
})
const context = await browser.newContext({
  baseURL: url,
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
  acceptDownloads: true,
})
const errors = []

function watch(page) {
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  page.on('requestfailed', request => errors.push(`${request.url()} ${request.failure()?.errorText}`))
}

async function twoFrames(page) {
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))))
}

async function waitForShot(page, shot) {
  await expect(page.locator('html')).toHaveAttribute('data-camera-shot', shot)
  await expect(page.locator('html')).toHaveAttribute('data-camera-idle', 'true', { timeout: 30000 })
  await page.evaluate(() => document.fonts.ready)
  await twoFrames(page)
}

async function schoolPage() {
  const page = await context.newPage()
  watch(page)
  const response = await page.goto('/?capture=1', { waitUntil: 'domcontentloaded' })
  assert.equal(response.status(), 200)
  await expect(page.getByTestId('skip-intro')).toBeVisible()
  assert.equal(await page.locator('canvas').evaluate(canvas => {
    const gl = canvas.getContext('webgl2')
    return Boolean(gl && !gl.isContextLost())
  }), true)
  await page.getByTestId('skip-intro').click()
  await waitForShot(page, 'district')
  await page.getByTestId('site-school').click()
  await waitForShot(page, 'facility')
  await expect(page.locator('main')).toHaveAttribute('data-site', 'school')
  return page
}

async function seek(page, hour) {
  await page.getByTestId('simulation-scrub').evaluate((element, value) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(element, String(value))
    element.dispatchEvent(new Event('input', { bubbles: true }))
    element.dispatchEvent(new Event('change', { bubbles: true }))
  }, hour)
  await twoFrames(page)
}

async function startLive(page) {
  const simulation = page.waitForResponse(response => response.url().includes('/api/v1/simulations') && response.request().method() === 'POST')
  await page.getByTestId('disconnect-grid').click()
  const response = await simulation
  assert.equal(response.status(), 200)
  await expect(page.locator('main')).toHaveAttribute('data-physics-source', 'live')
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await page.getByTestId('simulation-rewind').click()
  await twoFrames(page)
}

try {
  // P0: the live design search and its exact browser response.
  const design = await schoolPage()
  await startLive(design)
  const searchResponse = design.waitForResponse(response => response.url().includes('/api/v1/design-search') && response.request().method() === 'POST')
  await design.getByTestId('open-design-search').click()
  const searched = await searchResponse
  assert.equal(searched.status(), 200)
  const searchText = await searched.text()
  const search = JSON.parse(searchText)
  assert.equal(search.physics_model_version, 'lastlight-dispatch-1.0.0')
  assert.equal(search.schema_version, '1.0.0')
  assert.equal(search.physics_verified, true)
  assert.equal(search.selected_capacity_kwh, 32)
  assert.deepEqual(search.candidates.map(item => [item.capacity_kwh, item.survived_target, item.first_critical_failure_hours]),
    [[24, false, 9.12], [30, false, 11.4], [32, true, null], [36, true, null]])
  await expect(design.getByTestId('design-selected')).toHaveText('32 kWh')
  await expect(design.getByTestId('design-search-panel')).toContainText('11.40 h')
  await writeFile(resolve(root, '03-optimization/design-search-response.json'), searchText)
  await twoFrames(design)
  await design.screenshot({ path: resolve(root, '03-optimization/design-search-original.png') })
  await design.close()

  // Connected and blackout frames share the authored facility camera.
  const school = await schoolPage()
  await school.screenshot({ path: resolve(root, '01-inside-lastlight/school-hero-original.png') })
  await school.screenshot({ path: resolve(root, '01-inside-lastlight/school-connected-original.png') })
  const connectedShot = await school.locator('main').getAttribute('data-shot')
  await startLive(school)
  assert.equal(await school.locator('main').getAttribute('data-shot'), connectedShot)
  await expect(school.locator('main')).toHaveAttribute('data-critical-lit', 'true')
  await school.screenshot({ path: resolve(root, '01-inside-lastlight/school-blackout-original.png') })
  await school.close()

  // Actual equipment camera with projected WebGL hotspots.
  const equipment = await schoolPage()
  await equipment.getByTestId('inspect').click()
  await waitForShot(equipment, 'equipment')
  await expect(equipment.locator('#hotspot-pv')).toBeVisible()
  await expect(equipment.locator('#hotspot-inverter')).toBeVisible()
  await expect(equipment.locator('#hotspot-battery')).toBeVisible()
  await equipment.screenshot({ path: resolve(root, '01-inside-lastlight/school-equipment-original.png') })
  await equipment.close()

  // The live Frontier payload is captured from the same request as the screenshot.
  const frontier = await schoolPage()
  await startLive(frontier)
  const frontierResponse = frontier.waitForResponse(response => response.url().includes('/api/v1/frontiers') && response.request().method() === 'POST')
  await frontier.getByTestId('open-frontier').click()
  const mapped = await frontierResponse
  assert.equal(mapped.status(), 200)
  const frontierText = await mapped.text()
  const data = JSON.parse(frontierText)
  assert.equal(data.physics_version, 'lastlight-dispatch-1.0.0')
  assert.equal(data.schema_version, '1.0.0')
  assert.equal(data.summary.verified_cells, 273)
  assert.equal(data.trace.length, 273)
  assert.equal(data.ml_estimates.length, 0)
  await writeFile(resolve(root, '02-failure-frontier/frontier-data.json'), frontierText)
  await expect(frontier.getByTestId('frontier-panel')).toContainText('273 VERIFIED CELLS')
  await expect(frontier.getByTestId('frontier-current-case')).toBeVisible()
  await twoFrames(frontier)
  await frontier.screenshot({ path: resolve(root, '02-failure-frontier/frontier-original.png') })
  await frontier.close()

  // The failure frame uses the real baseline trace and visible service loss.
  const failure = await schoolPage()
  await startLive(failure)
  await failure.getByTestId('failure-marker').click()
  await expect(failure.locator('main')).toHaveAttribute('data-critical-lit', 'false')
  await expect(failure.getByTestId('engineering-verdict')).toContainText('09:07:12')
  await twoFrames(failure)
  await failure.screenshot({ path: resolve(root, '04-fallback/first-critical-failure-original.png') })
  await failure.close()

  assert.deepEqual(errors, [])
  const baseline = JSON.parse(await readFile(resolve(root, '03-optimization/design-search-response.json'), 'utf8'))
  await writeFile(resolve(root, 'documentation/capture-verification.json'), JSON.stringify({
    source_sha: '0463d42282b371b57c68de7b1a9ba0323e09fd60',
    url,
    viewport: '1920x1080',
    physics_model_version: baseline.physics_model_version,
    design_search_run_id: baseline.run_id,
    selected_capacity_kwh: baseline.selected_capacity_kwh,
    verified_candidates: baseline.candidates.map(item => ({ capacity_kwh: item.capacity_kwh, survived_target: item.survived_target, first_critical_failure_hours: item.first_critical_failure_hours })),
    frontier_cells: 273,
    browser_errors: errors,
  }, null, 2))
  console.log('Real application captures passed.')
} finally {
  await context.close()
  await browser.close()
}
