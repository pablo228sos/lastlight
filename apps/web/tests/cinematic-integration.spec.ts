import { test, expect, chromium } from '@playwright/test'
import { copyFile, mkdir, unlink } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const evidence = resolve(fileURLToPath(new URL('.', import.meta.url)), '../../../evidence/cinematic-integration')

test('architectural scene holds its camera through a grid loss', async () => {
  if (!process.env.CI) await mkdir(evidence, { recursive: true })
  const browser = await chromium.launch({
    channel: process.env.CI ? undefined : 'chrome',
    args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'],
  })
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: process.env.CI ? undefined : { dir: evidence, size: { width: 1440, height: 900 } },
  })
  const page = await context.newPage()
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  await page.goto('http://127.0.0.1:4173/?capture=1')
  await expect(page.locator('canvas')).toBeVisible()
  await page.getByTestId('skip-intro').click()
  await expect(page.locator('main')).toHaveAttribute('data-phase', 'DISTRICT')
  await expect(page.locator('html')).toHaveAttribute('data-camera-shot', 'district')
  await expect(page.locator('html')).toHaveAttribute('data-camera-idle', 'true', { timeout: 20000 })
  if (!process.env.CI) await page.screenshot({ path: resolve(evidence, 'district-1440x900.png') })
  await page.getByTestId('site-school').click()
  await expect(page.locator('html')).toHaveAttribute('data-camera-shot', 'facility')
  await expect(page.locator('html')).toHaveAttribute('data-camera-idle', 'true', { timeout: 20000 })
  await page.getByTestId('layer-power').click()
  const shot = await page.locator('main').getAttribute('data-shot')
  if (!process.env.CI) await page.screenshot({ path: resolve(evidence, 'school-connected-1440x900.png') })
  const connected = await page.locator('canvas').evaluate((canvas: HTMLCanvasElement) => canvas.toDataURL())
  await page.getByTestId('disconnect-grid').click()
  await page.waitForTimeout(1500)
  expect(await page.locator('main').getAttribute('data-shot')).toBe(shot)
  expect(await page.locator('canvas').evaluate((canvas: HTMLCanvasElement) => canvas.toDataURL())).not.toBe(connected)
  await expect(page.getByTestId('rehearsal-label')).toContainText('SYNTHETIC, NOT PHYSICS')
  if (!process.env.CI) await page.screenshot({ path: resolve(evidence, 'school-disconnected-1440x900.png') })
  await page.getByTestId('reset-scene').click()
  await page.waitForTimeout(500)
  const video = page.video()
  await context.close()
  if (video && !process.env.CI) {
    const recorded = await video.path()
    await copyFile(recorded, resolve(evidence, 'school-rehearsal.webm'))
    await unlink(recorded)
  }
  await browser.close()
  expect(errors).toEqual([])
})

test('projector frame shows the same school before and after', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/?capture=1')
  await page.getByTestId('skip-intro').click()
  await page.getByTestId('site-school').click()
  await expect(page.locator('html')).toHaveAttribute('data-camera-shot', 'facility')
  await expect(page.locator('html')).toHaveAttribute('data-camera-idle', 'true', { timeout: 20000 })
  await page.getByTestId('layer-power').click()
  if (!process.env.CI) await page.screenshot({ path: resolve(evidence, 'school-connected-1920x1080.png') })
  await page.getByTestId('disconnect-grid').click()
  await page.waitForTimeout(1400)
  if (!process.env.CI) await page.screenshot({ path: resolve(evidence, 'school-disconnected-1920x1080.png') })
  await expect(page.locator('main')).toHaveAttribute('data-visual-step', '1')
})
