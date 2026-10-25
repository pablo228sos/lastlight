import { expect, test, chromium, type Page } from '@playwright/test'
import { copyFile, mkdir, readFile, unlink } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const evidence = resolve(fileURLToPath(new URL('.', import.meta.url)), '../../../evidence/final-demo/after')
const capture = !process.env.CI

async function openSchool(page: Page) {
  await page.goto('/?demo=offline&capture=1')
  await page.getByTestId('skip-intro').click()
  await page.getByTestId('site-school').click()
  await expect(page.locator('main')).toHaveAttribute('data-site', 'school')
}

async function seek(page: Page, hour: number) {
  await page.getByTestId('simulation-scrub').evaluate((element, value) => {
    const input = element as HTMLInputElement
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, String(value))
    input.dispatchEvent(new Event('input', { bubbles: true }))
    input.dispatchEvent(new Event('change', { bubbles: true }))
  }, hour)
}

test('school walkthrough shows the physical verdict, frontier and downloadable evidence', async ({ page }) => {
  test.setTimeout(180000)
  await page.setViewportSize({ width: 1440, height: 900 })
  await openSchool(page)
  await page.waitForTimeout(1900)
  if (capture) { await mkdir(evidence, { recursive: true }); await page.screenshot({ path: resolve(evidence, '01-school-connected-1440x900.png') }) }
  await page.getByTestId('inspect').click()
  await page.getByTestId('disconnect-grid').click()
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await page.waitForTimeout(1900)
  await seek(page, 0)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'true')
  if (capture) await page.screenshot({ path: resolve(evidence, '02-initial-outage-1440x900.png') })
  await seek(page, 9.119)
  await expect(page.getByTestId('critical-coverage')).toContainText('1.50 / 1.50')
  if (capture) await page.screenshot({ path: resolve(evidence, '03-critical-served-1440x900.png') })
  await seek(page, 9.121)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'false')
  await expect(page.getByTestId('engineering-verdict')).toContainText('09:07:12')
  await expect(page.getByTestId('engineering-verdict')).toContainText('1.50 kW')
  await expect(page.getByTestId('engineering-verdict')).toContainText('24 kWh / 80%')
  if (capture) await page.screenshot({ path: resolve(evidence, '04-first-critical-failure-1440x900.png') })
  await page.getByTestId('compare-upgrade').click()
  await expect(page.getByTestId('engineering-verdict')).toContainText('SUSTAINED 12:00:00')
  await seek(page, 12)
  await expect(page.locator('main')).toHaveAttribute('data-critical-lit', 'true')
  if (capture) await page.screenshot({ path: resolve(evidence, '05-upgraded-end-window-1440x900.png') })
  await page.getByTestId('open-frontier').click()
  await expect(page.getByTestId('frontier-panel')).toBeVisible()
  await expect(page.getByTestId('frontier-current-case')).toHaveAttribute('aria-label', /80% charge, 12.00 hours.*active baseline case/)
  await expect(page.getByTestId('frontier-panel')).toContainText('273 VERIFIED CELLS')
  if (capture) await page.screenshot({ path: resolve(evidence, '06-failure-frontier-1440x900.png') })
  await page.keyboard.press('Escape')
  await page.locator('.text-action').click()
  const event = page.waitForEvent('download')
  await page.getByTestId('download-report').click()
  const download = await event
  const report = JSON.parse(await readFile(await download.path(), 'utf8'))
  expect(report.physics_source).toBe('Verified engine-generated offline replay')
  expect(report.scenario_input.battery.capacity_kwh).toBe(36)
  expect(report.scenario_input.load.critical_kw).toBe(1.5)
  expect(report.result.first_unmet_critical_demand_utc).toBeNull()
  expect(report.result.survived_full_window).toBe(true)
  expect(report.result.trace.length).toBeGreaterThan(0)
  expect(report.comparison.baseline.summary.critical_survival_hours).toBe(9.12)
  expect(report.comparison.upgraded.summary.first_failure_utc).toBeNull()
  expect(report.selected_input_hash).toMatch(/^[a-f0-9]{64}$/)
  if (capture) await page.screenshot({ path: resolve(evidence, '07-evidence-report-1440x900.png') })
  await page.getByRole('button', { name: 'Close data and methods' }).click()
  await page.getByTestId('reset-scene').click()
  await expect(page.locator('main')).toHaveAttribute('data-physics-source', 'none')
  if (capture) await page.screenshot({ path: resolve(evidence, '08-reset-1440x900.png') })
})

for (const [width, height] of [[1366, 768], [1920, 1080]]) {
  test(`critical failure stays legible at ${width}x${height}`, async ({ page }) => {
    test.setTimeout(120000)
    await page.setViewportSize({ width, height })
    await openSchool(page)
    await page.getByTestId('disconnect-grid').click()
    await expect(page.getByTestId('engineering-verdict')).toBeVisible()
    await seek(page, 9.121)
    await page.waitForTimeout(1900)
    const bounds = await page.getByTestId('engineering-verdict').evaluate(element => {
      const box = element.getBoundingClientRect()
      return { left: box.left, right: box.right, top: box.top, bottom: box.bottom, viewportWidth: window.innerWidth, viewportHeight: window.innerHeight }
    })
    expect(bounds.left).toBeGreaterThanOrEqual(0)
    expect(bounds.right).toBeLessThanOrEqual(width)
    expect(bounds.bottom).toBeLessThanOrEqual(height - 140)
    for (const action of ['compare-upgrade', 'open-frontier']) {
      expect(await page.getByTestId(action).evaluate(element => element.getBoundingClientRect().bottom <= element.closest('.simulation-instrument')!.getBoundingClientRect().bottom)).toBe(true)
    }
    if (capture) { await mkdir(evidence, { recursive: true }); await page.screenshot({ path: resolve(evidence, `04-first-critical-failure-${width}x${height}.png`) }) }
    await page.getByTestId('compare-upgrade').click()
    await expect(page.getByTestId('engineering-verdict')).toContainText('SUSTAINED 12:00:00')
    await seek(page, 12)
    await expect(page.getByTestId('battery-soc')).toContainText('27.4')
    expect(await page.getByTestId('open-frontier').evaluate(element => element.getBoundingClientRect().bottom <= element.closest('.simulation-instrument')!.getBoundingClientRect().bottom)).toBe(true)
    if (capture) await page.screenshot({ path: resolve(evidence, `05-upgraded-end-window-${width}x${height}.png`) })
  })
}

test('complete presenter walkthrough is recorded from WebGL', async () => {
  test.skip(!capture, 'Local evidence capture only')
  test.setTimeout(480000)
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] })
  const context = await browser.newContext({ baseURL: process.env.LASTLIGHT_WEB_URL || 'http://127.0.0.1:4173', viewport: { width: 1366, height: 768 }, recordVideo: { dir: evidence, size: { width: 960, height: 540 } } })
  const page = await context.newPage()
  await page.goto('/?demo=offline')
  await page.getByTestId('enter-lab').click()
  await page.waitForTimeout(2400)
  await page.getByTestId('focus-school').click()
  await page.waitForTimeout(1900)
  await page.getByTestId('inspect').click()
  await page.waitForTimeout(1900)
  await page.getByTestId('disconnect-grid').click()
  await expect(page.getByTestId('engineering-verdict')).toBeVisible()
  await seek(page, 9.121)
  await page.waitForTimeout(1800)
  await page.getByTestId('compare-upgrade').click()
  await seek(page, 12)
  await page.waitForTimeout(1300)
  await page.getByTestId('open-frontier').click()
  await page.waitForTimeout(1500)
  await page.keyboard.press('Escape')
  await page.locator('.text-action').click()
  await page.waitForTimeout(1300)
  await page.getByRole('button', { name: 'Close data and methods' }).click()
  await page.getByTestId('reset-scene').click()
  await page.waitForTimeout(1400)
  const video = page.video()
  await context.close()
  if (video) { await mkdir(evidence, { recursive: true }); const path = await video.path(); await copyFile(path, resolve(evidence, 'final-demo-walkthrough.webm')); await unlink(path) }
  await browser.close()
})
