import { createRequire } from 'node:module'
import { mkdir, copyFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const require = createRequire(new URL('../apps/web/package.json', import.meta.url))
const { chromium, expect } = require('@playwright/test')
const output = resolve('presentation-delivery/.working')
await mkdir(output, { recursive: true })
const mode = process.argv[2] ?? 'probe'
const browser = await chromium.launch({
  channel: 'chrome',
  headless: true,
  args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'],
})
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
  baseURL: 'http://127.0.0.1:4173',
  acceptDownloads: true,
  recordVideo: { dir: output, size: { width: 1920, height: 1080 } },
})
const page = await context.newPage()
page.setDefaultTimeout(60000)
const startedAt = Date.now()
const marks = []
const mark = name => { const seconds = (Date.now() - startedAt) / 1000; marks.push({ name, seconds }); process.stdout.write(`${name}: ${seconds.toFixed(2)}s\n`) }
const pause = ms => page.waitForTimeout(ms)
const shot = name => page.screenshot({ path: resolve(output, `${name}.png`) })
const seek = async value => {
  await page.getByTestId('simulation-scrub').evaluate((element, nextValue) => {
    const input = element
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
    setter.call(input, String(nextValue))
    input.dispatchEvent(new Event('input', { bubbles: true }))
    input.dispatchEvent(new Event('change', { bubbles: true }))
  }, value)
}
const assertLive = async () => expect(page.getByTestId('rehearsal-label')).toContainText('LIVE LOCAL PHYSICS API')
try {
  await page.goto('/', { waitUntil: 'domcontentloaded' })
  mark('page-loaded')
  await expect(page.getByTestId('enter-lab')).toBeVisible()
  if (mode === 'probe') {
    await page.getByTestId('enter-lab').click()
    await pause(2500)
    await page.getByTestId('focus-school').click()
    await pause(4500)
    await shot('probe-school')
    await pause(2000)
  } else {
    await pause(1000)
    await page.getByTestId('enter-lab').click()
    await pause(3500)
    await page.getByTestId('focus-school').click()
    await pause(3500)
    await page.getByTestId('layer-power').click()
    await pause(1500)
    await page.getByTestId('inspect').click()
    await pause(4500)
    await shot('01-the-school')
    mark('school')
    await page.getByTestId('disconnect-grid').click()
    await expect(page.getByTestId('physics-instrument')).toBeVisible()
    await assertLive()
    await shot('02-the-blackout')
    mark('blackout')
    await pause(6000)
    await seek(9.121)
    await expect(page.getByTestId('engineering-verdict')).toContainText('09:07:12')
    await shot('03-first-failure')
    mark('failure')
    await pause(6500)
    await page.getByTestId('compare-upgrade').click()
    await expect(page.getByTestId('comparison-result')).toBeVisible()
    await page.getByTestId('show-upgraded').click()
    await seek(12)
    await expect(page.getByTestId('engineering-verdict')).toContainText('SUSTAINED 12:00:00')
    await shot('04-upgrade')
    mark('upgrade')
    await pause(7000)
    await page.getByTestId('open-design-search').click()
    await expect(page.getByTestId('design-selected')).toHaveText('32 kWh')
    await shot('05-capacity-search')
    mark('search')
    await pause(8000)
    await page.keyboard.press('Escape')
    await page.getByTestId('open-frontier').click()
    await expect(page.getByTestId('frontier-panel')).toContainText('273 VERIFIED CELLS')
    await shot('06-failure-frontier')
    mark('frontier')
    await pause(6500)
    await page.keyboard.press('Escape')
    await page.getByRole('button', { name: /data & methods/i }).click()
    await expect(page.getByTestId('download-report')).toBeVisible()
    await shot('07-report-export')
    mark('report')
    const downloadPromise = page.waitForEvent('download')
    await page.getByTestId('download-report').click()
    const download = await downloadPromise
    await download.saveAs(resolve(output, 'actual-live-report.json'))
    mark('downloaded')
    await pause(4500)
  }
} finally {
  const video = page.video()
  await context.close()
  if (video) await copyFile(await video.path(), resolve(output, mode === 'probe' ? 'native-1080-probe.webm' : 'native-1080-full.webm'))
  await writeFile(resolve(output, `${mode}-marks.json`), JSON.stringify(marks, null, 2))
  await browser.close()
}
