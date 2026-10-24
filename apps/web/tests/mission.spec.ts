import { test, expect } from '@playwright/test'
import { mkdir } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const evidence = resolve(fileURLToPath(new URL('.', import.meta.url)), '../../../evidence/phase-00')
test.beforeAll(async () => { await mkdir(evidence, { recursive: true }) })

test('mission select at 1440×900: selection, systems layer, evidence and theater', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', error => errors.push(error.message))
  page.on('console', message => { if (message.type() === 'error') errors.push(message.text()) })
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: /The last light/ })).toBeVisible()
  expect(await page.locator('.scene-plate').evaluate(image => (image as HTMLImageElement).naturalWidth > 0)).toBe(true)
  await page.screenshot({ path: resolve(evidence, 'mission-1440x900.png') })
  await page.getByTestId('site-clinic').click()
  await expect(page.getByTestId('site-clinic')).toHaveAttribute('aria-pressed', 'true')
  await expect(page.getByText('COMMUNITY CARE / ARCHETYPE')).toBeVisible()
  await page.getByTestId('layer-systems').click()
  await expect(page.getByTestId('layer-systems')).toHaveAttribute('aria-pressed', 'true')
  await expect(page.locator('.system-overlay')).toBeVisible()
  await page.screenshot({ path: resolve(evidence, 'systems-1440x900.png') })
  await page.getByRole('button', { name: /DATA & METHODS/ }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toHaveCount(0)
  await page.getByTestId('enter-simulation').click()
  await expect(page.getByRole('heading', { name: 'Clinic.' })).toBeVisible()
  await expect(page.getByText(/PHYSICS CONNECTS IN ITERATION 01/)).toBeVisible()
  expect(errors).toEqual([])
})

test('1920×1080 theater screenshot and keyboard controls', async ({ page }) => {
  await page.setViewportSize({ width: 1920, height: 1080 })
  await page.goto('/')
  await page.getByTestId('enter-simulation').click()
  await page.getByTestId('site-school').click()
  await page.screenshot({ path: resolve(evidence, 'theater-1920x1080.png') })
  await page.getByTestId('site-business').focus()
  await page.keyboard.press('Enter')
  await expect(page.getByRole('heading', { name: 'Small business.' })).toBeVisible()
  await expect(page.locator('body')).toHaveJSProperty('scrollWidth', 1920)
})

test('laptop viewport and reduced motion remain usable', async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 768 })
  await page.emulateMedia({ reducedMotion: 'reduce' })
  await page.goto('/')
  await expect(page.getByTestId('enter-simulation')).toBeInViewport()
  await expect(page.getByTestId('site-residential')).toBeInViewport()
  await page.getByTestId('site-residential').click()
  await expect(page.getByTestId('site-residential')).toHaveAttribute('aria-pressed', 'true')
  const assumptionsBottom = await page.locator('.evidence-button').evaluate(el => el.getBoundingClientRect().bottom)
  const footerTop = await page.locator('.statusbar').evaluate(el => el.getBoundingClientRect().top)
  expect(assumptionsBottom).toBeLessThan(footerTop)
  await page.screenshot({ path: resolve(evidence, 'laptop-1366x768.png') })
})

test('vector district remains when the generated plate fails to load', async ({ page }) => {
  await page.route('**/district-night*.webp', route => route.abort())
  await page.goto('/')
  await expect(page.locator('.scene--plate')).toHaveCount(0)
  await expect(page.locator('.vector-fallback')).toBeVisible()
  await page.getByRole('button', { name: 'Select clinic on map' }).click()
  await expect(page.getByTestId('site-clinic')).toHaveAttribute('aria-pressed', 'true')
})
