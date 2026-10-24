import { expect, test } from '@playwright/test'

for (const site of ['clinic', 'business', 'residential'] as const) {
  test(`${site} is identified as a visual site study with no simulated outage`, async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/?demo=offline')
    await page.getByTestId('skip-intro').click()
    await page.getByTestId(`site-${site}`).click()
    await expect(page.locator('main')).toHaveAttribute('data-site', site)
    await expect(page.getByTestId('rehearsal-label')).toContainText('NO VALIDATED ENERGY MODEL')
    await expect(page.getByTestId('disconnect-grid')).toHaveCount(0)
    await expect(page.getByTestId('layer-power')).toHaveCount(0)
    await expect(page.getByTestId('school-demo')).toBeVisible()
    await page.getByTestId('inspect').click()
    await expect(page.locator('main')).toHaveAttribute('data-phase', 'INSPECT')
    await expect(page.getByText('VISUAL PROTOTYPE / NO BLACKOUT CALCULATION FOR THIS SITE')).toBeVisible()
    if (site === 'residential') await expect(page.locator('.site-summary')).toContainText('Three blocks')
    await page.getByTestId('school-demo').click()
    await expect(page.locator('main')).toHaveAttribute('data-site', 'school')
    await expect(page.getByTestId('disconnect-grid')).toBeVisible()
  })
}

test('critical controls stay inside laptop, desktop and projector viewports', async ({ page }) => {
  for (const [width, height] of [[1366, 768], [1440, 900], [1920, 1080]]) {
    await page.setViewportSize({ width, height })
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/?demo=offline')
    await page.getByTestId('skip-intro').click()
    await page.getByTestId('site-clinic').click()
    for (const selector of ['.masthead', '.scene-title', '.facility-strip', '.equipment-spine', '.transport', '.footnote']) {
      const box = await page.locator(selector).boundingBox()
      expect(box, `${selector} has a visible box`).not.toBeNull()
      expect(box!.x).toBeGreaterThanOrEqual(0)
      expect(box!.y).toBeGreaterThanOrEqual(0)
      expect(box!.x + box!.width).toBeLessThanOrEqual(width + 1)
      expect(box!.y + box!.height).toBeLessThanOrEqual(height + 1)
    }
    await page.getByTestId('site-school').click()
    await page.getByTestId('disconnect-grid').click()
    await expect(page.getByTestId('physics-instrument')).toBeVisible()
    const instrument = await page.getByTestId('physics-instrument').boundingBox()
    expect(instrument!.y + instrument!.height).toBeLessThanOrEqual(height + 1)
    await page.getByTestId('open-frontier').click()
    await expect(page.getByTestId('frontier-panel')).toBeVisible()
    await expect(page.locator('.frontier-plot button')).toHaveCount(273)
    const frontier = await page.getByTestId('frontier-panel').boundingBox()
    expect(frontier!.x + frontier!.width).toBeLessThanOrEqual(width + 1)
    expect(frontier!.y + frontier!.height).toBeLessThanOrEqual(height + 1)
    await page.getByRole('button', { name: 'Close Failure Frontier' }).click()
  }
})
