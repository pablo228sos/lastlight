import assert from 'node:assert/strict'
import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { chromium, expect } from '@playwright/test'

const url = process.env.LASTLIGHT_PUBLIC_URL || 'https://pablo228sos.github.io/lastlight/?demo=offline'
const evidence = resolve('..', '..', 'evidence', process.env.LASTLIGHT_PUBLIC_EVIDENCE_DIR || 'public-deployment')
await mkdir(evidence, { recursive: true })
const browser = await chromium.launch({ channel: process.env.CI ? undefined : 'chrome', headless: true, args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] })
const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, acceptDownloads: true })
const errors = []
const badResponses = []
const localRequests = []
function trackPage(tab) {
  tab.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  tab.on('pageerror', error => errors.push(error.message))
  tab.on('requestfailed', request => errors.push(`${request.url()} ${request.failure()?.errorText}`))
  tab.on('request', request => { if (/\b(localhost|127\.0\.0\.1)\b/.test(new URL(request.url()).hostname)) localRequests.push(request.url()) })
  tab.on('response', response => { if (response.status() >= 400) badResponses.push(`${response.status()} ${response.url()}`) })
}
trackPage(page)

async function seek(hours) {
  await page.getByTestId('simulation-scrub').evaluate((element, value) => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(element, String(value))
    element.dispatchEvent(new Event('input', { bubbles: true }))
    element.dispatchEvent(new Event('change', { bubbles: true }))
  }, hours)
}

try {
  const response = await page.goto(url, { waitUntil: 'domcontentloaded' })
  assert.equal(response.status(), 200)
  await expect(page.getByTestId('skip-intro')).toBeVisible()
  assert.equal(await page.locator('canvas').evaluate(canvas => {
    const gl = canvas.getContext('webgl2')
    return Boolean(gl && !gl.isContextLost())
  }), true, 'WebGL 2 context must render')
  await page.screenshot({ path: resolve(evidence, '01-public-intro-1440x900.png') })
  await page.getByTestId('skip-intro').click()
  await page.getByTestId('site-school').click()
  await page.getByTestId('inspect').click()
  await page.screenshot({ path: resolve(evidence, '02-public-school-1440x900.png') })
  await page.getByTestId('disconnect-grid').click()
  await expect(page.locator('main')).toHaveAttribute('data-physics-source', 'offline')
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await seek(9.121)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'false')
  await expect(page.getByTestId('engineering-verdict')).toContainText('09:07:12')
  await page.screenshot({ path: resolve(evidence, '03-public-failure-1440x900.png') })
  await page.getByTestId('compare-upgrade').click()
  await expect(page.getByTestId('engineering-verdict')).toContainText('SUSTAINED 12:00:00')
  await seek(12)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'true')
  await page.screenshot({ path: resolve(evidence, '04-public-comparison-1440x900.png') })
  await expect(page.getByTestId('open-design-search')).toHaveCount(0)
  await page.getByTestId('open-frontier').click()
  await expect(page.locator('.frontier-plot button')).toHaveCount(273)
  await page.screenshot({ path: resolve(evidence, '05-public-frontier-1440x900.png') })
  await page.keyboard.press('Escape')
  await page.locator('.text-action').click()
  const downloadPromise = page.waitForEvent('download')
  await page.getByTestId('download-report').click()
  const download = await downloadPromise
  const reportPath = resolve(evidence, 'public-offline-report.json')
  await download.saveAs(reportPath)
  const report = JSON.parse(await readFile(reportPath, 'utf8'))
  assert.equal(report.physics_source, 'Verified engine-generated offline replay')
  assert.equal(report.scenario_input.battery.capacity_kwh, 36)
  assert.equal(report.comparison.baseline.summary.critical_survival_hours, 9.12)
  await page.screenshot({ path: resolve(evidence, '06-public-report-1440x900.png') })
  await page.close()

  const mobile = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 })
  trackPage(mobile)
  const mobileResponse = await mobile.goto(url, { waitUntil: 'domcontentloaded' })
  assert.equal(mobileResponse.status(), 200)
  await expect(mobile.getByTestId('skip-intro')).toBeVisible()
  await mobile.waitForTimeout(2500)
  assert.equal(await mobile.locator('canvas').evaluate(canvas => {
    const gl = canvas.getContext('webgl2')
    return Boolean(gl && !gl.isContextLost())
  }), true, 'Mobile viewport must keep a WebGL 2 context')
  await mobile.screenshot({ path: resolve(evidence, '07-public-mobile-390x844.png') })
  await mobile.close()

  assert.deepEqual(localRequests, [], 'Public site must not call localhost')
  assert.deepEqual(badResponses, [], 'Public assets and requests must succeed')
  assert.deepEqual(errors, [], 'Public browser console must have no errors')
  const summary = { url, result: 'passed', webgl: true, baseline_failure: '09:07:12', comparison: '36 kWh sustained 12 hours', frontier_cells: 273, report_source: report.physics_source, local_requests: localRequests, bad_responses: badResponses, console_errors: errors, tested_viewports: ['1440x900', '390x844'] }
  await writeFile(resolve(evidence, 'verification.json'), JSON.stringify(summary, null, 2))
  console.log(JSON.stringify(summary, null, 2))
} finally {
  await browser.close()
}
