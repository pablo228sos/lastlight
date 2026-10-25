import { test, expect } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'

async function captureLayouts(page: import('@playwright/test').Page, state: string) {
  const evidence = resolve('../../evidence/unified')
  if (process.env.LASTLIGHT_CAPTURE) await mkdir(evidence, { recursive: true })
  for (const [width, height] of [[1366, 768], [1440, 900], [1920, 1080]]) {
    await page.setViewportSize({ width, height })
    const dialog = page.getByRole('dialog')
    expect(await dialog.evaluate(element => { const r = element.getBoundingClientRect(); return r.left >= 0 && r.top >= 0 && r.right <= innerWidth && r.bottom <= innerHeight && element.scrollWidth <= element.clientWidth + 1 })).toBe(true)
    if (process.env.LASTLIGHT_CAPTURE) await page.screenshot({ path: resolve(evidence, `${state}-${width}x${height}.png`) })
  }
}

test('school connects real official physics, FragilityNet and verified map candidates', async ({ page }) => {
  test.skip(!process.env.LASTLIGHT_LIVE_API, 'Requires the actual unified API, no successful response mocks')
  await page.goto('/')
  await expect(page.locator('canvas')).toBeVisible()
  await page.getByTestId('skip-intro').click()
  await page.getByTestId('site-school').click()
  await page.getByTestId('disconnect-grid').click()
  await expect(page.getByTestId('physics-instrument')).toBeVisible()
  await page.getByTestId('run-ai').click()
  await expect(page.getByTestId('ai-model')).toContainText('fragility-official-v1-8b40929366e6', { timeout: 30_000 })
  await expect(page.getByTestId('ai-physical-verdict')).toContainText('9.12')
  await expect(page.getByTestId('ai-score')).toContainText(/0\.\d+/)
  await expect(page.getByText('It is not the real-world probability of a city power outage.', { exact: false })).toBeVisible()
  await captureLayouts(page, 'fragility')
  await page.getByRole('button', { name: 'Close AI resilience analysis' }).click()
  await page.getByTestId('open-frontier').click()
  await page.getByTestId('show-ai-candidates').click()
  await expect(page.getByTestId('candidate-count')).toContainText('12 independently checked', { timeout: 30_000 })
  await expect(page.locator('.frontier-plot .ai-checked')).toHaveCount(12)
  await expect(page.getByTestId('candidate-model')).toContainText('fragility-official-v1-8b40929366e6')
  await captureLayouts(page, 'frontier')
  await page.getByRole('button', { name: 'Close Failure Frontier' }).click()
  await page.getByTestId('change-horizon').click()
  await expect(page.getByTestId('physics-instrument')).toContainText('16:00:00')
  await page.getByTestId('compare-upgrade').click()
  await expect(page.getByTestId('comparison-result')).toContainText('13.68 H OBSERVED FAILURE')
  await page.getByTestId('open-frontier').click()
  await expect(page.locator('.frontier-identity')).toContainText('36 kWh')
  await expect(page.locator('.frontier-axis-x')).toContainText('16 H')
})

test('research preview performs actual GRU inference and shows the preferred baseline', async ({ page }) => {
  test.skip(!process.env.LASTLIGHT_LIVE_API, 'Requires the actual unified API')
  await page.goto('/')
  await page.getByTestId('open-forecast').click()
  await page.getByTestId('run-forecast').click()
  await expect(page.getByTestId('forecast-model')).toContainText('energydna-gru-v1-56d366ec3532', { timeout: 30_000 })
  await expect(page.getByTestId('forecast-neural')).toContainText(/\d+\.\d+ kW/)
  await expect(page.getByTestId('forecast-baseline')).toContainText('Persistence')
  await expect(page.getByTestId('forecast-actual')).toContainText(/\d+\.\d+ kW/)
  await expect(page.locator('.frontier-intro')).toContainText('Not connected to emergency critical-load physics.')
  await captureLayouts(page, 'forecast')
})

test('real missing-checkpoint backend leaves physical verdict and map usable', async ({ page }) => {
  test.skip(!process.env.LASTLIGHT_FALLBACK_API, 'Requires a second real unified API started with missing model directories')
  await page.route('**/api/v1/ml/**', async route => {
    const path = new URL(route.request().url()).pathname
    const response = await route.fetch({ url: `${process.env.LASTLIGHT_FALLBACK_API}${path}` })
    await route.fulfill({ response })
  })
  await page.goto('/')
  await page.getByTestId('skip-intro').click()
  await page.getByTestId('site-school').click()
  await page.getByTestId('disconnect-grid').click()
  await page.getByTestId('run-ai').click()
  await expect(page.getByRole('heading', { name: 'Model unavailable' })).toBeVisible()
  await expect(page.getByTestId('ai-physical-verdict')).toContainText('9.12')
  await expect(page.getByTestId('ai-score')).toHaveCount(0)
  await page.getByRole('button', { name: 'Close AI resilience analysis' }).click()
  await page.getByTestId('open-frontier').click()
  await page.getByTestId('show-ai-candidates').click()
  await expect(page.getByTestId('candidate-count')).toContainText('physical map remains available')
  await expect(page.locator('.frontier-plot button')).toHaveCount(273)
  await captureLayouts(page, 'ml-unavailable')
})
