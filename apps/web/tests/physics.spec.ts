import { test, expect, chromium, type Page } from '@playwright/test'
import { mkdir, copyFile, readFile, unlink } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { failureHours, traceInterval, validateComparison, validateSimulation } from '../src/lib/physics'

const evidence = resolve(fileURLToPath(new URL('.', import.meta.url)), '../../../evidence/phase-03-physics')
const capture = !process.env.CI

async function enterSchool(page: Page, query = '/?demo=offline') {
  await page.goto(query)
  await expect(page.locator('canvas')).toBeVisible()
  await page.getByTestId('skip-intro').click()
  await page.getByTestId('site-school').click()
  await page.getByTestId('inspect').click()
  await page.getByTestId('disconnect-grid').click()
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

test('official fixtures retain the exact split failure interval and right-censored upgrade', async () => {
  const run = validateSimulation(JSON.parse(await readFile(resolve(evidence, '../../apps/web/src/data/baseline.result.json'), 'utf8')) as unknown)
  const pair = validateComparison(JSON.parse(await readFile(resolve(evidence, '../../apps/web/src/data/comparison.result.json'), 'utf8')) as unknown)
  expect(failureHours(run)).toBe(9.12)
  expect(traceInterval(run, 9.119).row.unserved_critical_kw).toBe(0)
  expect(traceInterval(run, 9.12).row.unserved_critical_kw).toBeGreaterThan(0)
  expect(traceInterval(run, 9.12).row.duration_hours).toBeCloseTo(.13)
  expect(traceInterval(run, 9.12).row.t_utc).toBe(run.summary.first_failure_utc)
  expect(pair.upgraded.summary.first_failure_utc).toBeNull()
  expect(pair.upgraded.summary.survived_full_window).toBe(true)
  expect(pair.upgraded.summary.idealized_autonomy_hours).toBe(13.68)
})

test('verified replay drives SOC, critical lighting and comparison', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await enterSchool(page)
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await expect(page.locator('main')).toHaveAttribute('data-physics-source', 'offline')
  await page.getByTestId('simulation-play').click()
  await seek(page, 9.119)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'true')
  await expect(page.getByTestId('battery-soc')).toContainText('20.0')
  await expect(page.getByTestId('critical-coverage')).toContainText('1.50 / 1.50')
  if (capture) { await mkdir(evidence, { recursive: true }); await page.waitForTimeout(1900); await page.screenshot({ path: resolve(evidence, 'baseline-before-failure-1440x900.png') }) }
  await seek(page, 9.121)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'false')
  await expect(page.getByTestId('critical-coverage')).toContainText('0.00 / 1.50')
  await expect(page.getByTestId('failure-summary')).toContainText('09:07:12')
  if (capture) await page.screenshot({ path: resolve(evidence, 'baseline-critical-failure-1440x900.png') })
  await page.getByTestId('compare-upgrade').click()
  await expect(page.getByTestId('comparison-result')).toContainText('NO OBSERVED FAILURE IN 12 H')
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'true')
  await seek(page, 12)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'true')
  await expect(page.getByTestId('failure-summary')).toContainText('NONE IN 12-HOUR TEST')
  expect(await page.locator('.instrument-comparison small').evaluate(element => element.getBoundingClientRect().bottom < window.innerHeight - 180)).toBe(true)
  if (capture) await page.screenshot({ path: resolve(evidence, 'upgrade-end-window-1440x900.png') })
  await page.getByTestId('show-baseline').click()
  await seek(page, 10)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'false')
  await page.getByTestId('reset-scene').click()
  await expect(page.locator('main')).toHaveAttribute('data-physics-source', 'none')
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'true')
})

test('API failure stays visible until verified replay is explicitly selected', async ({ page }) => {
  await page.route('**/api/v1/simulations', route => route.fulfill({ status: 503, contentType: 'application/json', body: '{"error":"offline"}' }))
  await enterSchool(page, '/')
  await expect(page.getByRole('alert')).toContainText('HTTP 503')
  await expect(page.getByTestId('physics-instrument')).toHaveCount(0)
  await page.getByTestId('load-offline').click()
  await expect(page.locator('main')).toHaveAttribute('data-physics-source', 'offline')
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
})

test('projector viewport preserves scene and accessible instrument', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await enterSchool(page)
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await page.getByTestId('simulation-play').click()
  await seek(page, 9.121)
  await page.waitForTimeout(1900)
  if (capture) { await mkdir(evidence, { recursive: true }); await page.screenshot({ path: resolve(evidence, 'baseline-critical-failure-1920x1080.png') }) }
  expect(await page.locator('body').evaluate(element => element.scrollWidth)).toBe(1920)
  expect(await page.getByTestId('physics-instrument').evaluate(element => {
    const box = element.getBoundingClientRect()
    return box.right <= window.innerWidth && box.bottom <= window.innerHeight
  })).toBe(true)
})

test('live local API serves a fresh simulation and comparison over HTTP', async ({ page }) => {
  test.skip(!process.env.LASTLIGHT_LIVE_API, 'Run with the isolated Physics API on 127.0.0.1:8000')
  await enterSchool(page, '/')
  await expect(page.locator('main')).toHaveAttribute('data-physics-source', 'live')
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await page.getByTestId('simulation-play').click()
  await seek(page, 9.121)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'false')
  await page.getByTestId('compare-upgrade').click()
  await expect(page.getByTestId('comparison-result')).toContainText('NO OBSERVED FAILURE IN 12 H')
  if (capture) { await mkdir(evidence, { recursive: true }); await page.screenshot({ path: resolve(evidence, 'live-api-comparison-1440x900.png') }) }
})

test('presenter walkthrough is recorded from the running 3D application', async () => {
  test.skip(!capture, 'Local visual evidence only')
  const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'chrome', headless: true, args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] })
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, recordVideo: { dir: evidence, size: { width: 960, height: 600 } } })
  const page = await context.newPage()
  await enterSchool(page)
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await page.getByTestId('simulation-play').click()
  await seek(page, 8.7)
  await page.waitForTimeout(900)
  await seek(page, 9.13)
  await page.waitForTimeout(1100)
  await page.getByTestId('compare-upgrade').click()
  await expect(page.getByTestId('comparison-result')).toBeVisible()
  await seek(page, 12)
  await expect(page.getByTestId('failure-summary')).toContainText('NONE IN 12-HOUR TEST')
  await page.waitForTimeout(2400)
  const video = page.video()
  await context.close()
  if (video) { await mkdir(evidence, { recursive: true }); const path = await video.path(); await copyFile(path, resolve(evidence, 'physics-walkthrough.webm')); await unlink(path) }
  await browser.close()
})
