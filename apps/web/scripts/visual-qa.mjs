import { chromium } from '@playwright/test'
import { mkdir, writeFile, copyFile, unlink } from 'node:fs/promises'
import { resolve } from 'node:path'

const [base = 'http://127.0.0.1:4173', directory = '../../evidence/phase-04/after', mode = 'stills'] = process.argv.slice(2)
const output = resolve(directory)
await mkdir(output, { recursive: true })
const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] })
const sizes = [[1366, 768], [1440, 900], [1920, 1080]]
const sites = ['clinic', 'business', 'residential']
const evidence = []

if (mode !== 'walkthrough-only') for (const [width, height] of sizes) {
  const context = await browser.newContext({ viewport: { width, height }, reducedMotion: 'reduce' })
  const page = await context.newPage()
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto(`${base}/?demo=offline&capture=1`)
  await page.getByTestId('skip-intro').click()
  for (const site of sites) {
    await page.getByTestId(`site-${site}`).click()
    await page.waitForTimeout(350)
    await page.screenshot({ path: resolve(output, `${site}-${width}x${height}.png`), timeout: 120_000 })
    const metrics = await page.evaluate(() => {
      const selectors = ['.masthead', '.scene-title', '.facility-strip', '.equipment-spine', '.transport', '.footnote']
      return Object.fromEntries(selectors.map(selector => {
        const rect = document.querySelector(selector)?.getBoundingClientRect()
        return [selector, rect && { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom }]
      }))
    })
    evidence.push({ site, width, height, phase: await page.locator('main').getAttribute('data-phase'), camera: await page.locator('main').getAttribute('data-shot'), metrics, errors })
  }
  await context.close()
}

if (mode === 'walkthrough' || mode === 'walkthrough-only') {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, recordVideo: { dir: output, size: { width: 1440, height: 900 } } })
  const page = await context.newPage()
  await page.goto(`${base}/?demo=offline&capture=1`)
  await page.waitForTimeout(500)
  await page.getByTestId('enter-lab').click()
  await page.waitForTimeout(3800)
  for (const site of sites) {
    await page.getByTestId(`site-${site}`).click()
    await page.waitForTimeout(2300)
    await page.getByTestId('inspect').click()
    await page.waitForTimeout(1700)
  }
  await page.getByTestId('site-school').click()
  await page.waitForTimeout(2300)
  await page.getByTestId('inspect').click()
  await page.waitForTimeout(1800)
  await page.getByTestId('disconnect-grid').click()
  await page.getByTestId('physics-instrument').waitFor()
  await page.getByTestId('simulation-play').click()
  await page.getByTestId('simulation-scrub').evaluate(element => {
    const input = element
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set
    setter?.call(input, '9.13')
    input.dispatchEvent(new Event('input', { bubbles: true }))
    input.dispatchEvent(new Event('change', { bubbles: true }))
  })
  await page.waitForTimeout(1400)
  await page.getByTestId('compare-upgrade').click()
  await page.waitForTimeout(1000)
  await page.getByTestId('open-frontier').click()
  await page.getByTestId('frontier-panel').waitFor()
  await page.waitForTimeout(2200)
  await page.getByRole('button', { name: 'Close Failure Frontier' }).click()
  await page.getByTestId('reset-scene').click()
  await page.locator('main[data-phase="INSPECT"]').waitFor()
  await page.waitForTimeout(3500)
  await page.screenshot({ path: resolve(output, 'reset-1440x900.png'), timeout: 120_000 })
  const video = page.video()
  await context.close()
  if (video) { const source = await video.path(); await copyFile(source, resolve(output, 'release-walkthrough.webm')); await unlink(source) }
}

if (mode !== 'walkthrough-only') await writeFile(resolve(output, 'layout-metrics.json'), JSON.stringify(evidence, null, 2) + '\n')
await browser.close()
