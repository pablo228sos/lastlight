import assert from 'node:assert/strict'
import { createRequire } from 'node:module'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const require = createRequire(new URL('../../../apps/web/package.json', import.meta.url))
const { chromium } = require('@playwright/test')
const root = resolve(fileURLToPath(new URL('..', import.meta.url)))
const file = path => resolve(root, path)
const readJson = async path => JSON.parse(await readFile(file(path), 'utf8'))
const png = async path => 'data:image/png;base64,' + (await readFile(file(path))).toString('base64')
const design = await readJson('03-optimization/design-search-response.json')
const frontier = await readJson('02-failure-frontier/frontier-data.json')
assert.equal(design.selected_capacity_kwh, 32)
assert.deepEqual(design.candidates.map(c => [c.capacity_kwh, c.survived_target, c.first_critical_failure_hours]),
  [[24, false, 9.12], [30, false, 11.4], [32, true, null], [36, true, null]])
assert.equal(frontier.trace.length, 273)
assert.equal(frontier.summary.physics_calls, 13)
assert.equal(frontier.ml_estimates.length, 0)

const hero = await png('01-inside-lastlight/school-hero-original.png')
const connected = await png('01-inside-lastlight/school-connected-original.png')
const blackout = await png('01-inside-lastlight/school-blackout-original.png')
const search = await png('03-optimization/design-search-original.png')
const failure = await png('04-fallback/first-critical-failure-original.png')
const C = { bg: '#06090b', ink: '#f4f3ed', amber: '#e5c04e', coral: '#dd806e', teal: '#76d5c5', muted: '#9aaeb0', line: '#385053' }
const css = `<style>
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:${C.bg};color:${C.ink};font-family:Arial,Helvetica,sans-serif}
.stage{position:relative;width:100%;height:100%;overflow:hidden;background:${C.bg}}
.mono{font-family:'Courier New',monospace;font-weight:700;letter-spacing:.15em}
.kicker{color:${C.amber};font:700 22px 'Courier New',monospace;letter-spacing:.18em}
.title{font-family:'Arial Black',Arial,sans-serif;font-weight:900;line-height:.91;letter-spacing:-.045em}
.small{color:${C.muted};font:700 21px 'Courier New',monospace;letter-spacing:.055em}
.rule{height:2px;background:${C.line}}
.source{color:${C.muted};font:700 17px 'Courier New',monospace;letter-spacing:.04em}
.frame{border:2px solid ${C.line};overflow:hidden;background:#071015}
.frame img{display:block;width:100%;height:100%;object-fit:cover}
</style>`
const browser = await chromium.launch({ channel: 'chrome', headless: true })

async function render(path, width, height, body) {
  const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 })
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8">${css}</head><body><div class="stage">${body}</div></body></html>`)
  await page.evaluate(() => document.fonts.ready)
  await page.screenshot({ path: file(path) })
  await page.close()
}

function authenticModal(src, width, height, cropY = 157) {
  const scale = width / 960
  const sourceWidth = 1920 * scale
  const sourceHeight = 1080 * scale
  return `<div class="frame" style="position:relative;width:${width}px;height:${height}px;border-color:#577375">
    <img src="${src}" style="position:absolute;max-width:none;width:${sourceWidth}px;height:${sourceHeight}px;left:${-480 * scale}px;top:${-cropY * scale}px;object-fit:unset">
  </div>`
}

function schoolSceneCrop(src) {
  const scale = 850 / 1100
  return `<div class="frame" style="position:relative;width:850px;height:557px">
    <img src="${src}" style="position:absolute;max-width:none;width:${1920 * scale}px;height:${1080 * scale}px;left:${-350 * scale}px;top:${-180 * scale}px;object-fit:unset">
  </div>`
}

function frontierSvg(width, height, compact = false) {
  const sorted = [...frontier.axes.initial_soc].reverse()
  const hours = frontier.axes.duration_hours
  const x = compact ? 170 : 200
  const y = compact ? 120 : 115
  const w = width - x - 50
  const h = height - y - (compact ? 160 : 170)
  const cw = w / hours.length
  const ch = h / sorted.length
  const byKey = new Map(frontier.trace.map(cell => [`${cell.initial_soc.toFixed(6)}|${cell.duration_hours.toFixed(6)}`, cell]))
  const cells = sorted.flatMap((soc, row) => hours.map((duration, col) => {
    const cell = byKey.get(`${soc.toFixed(6)}|${duration.toFixed(6)}`)
    assert.ok(cell?.physics_verified)
    const fill = cell.failed ? '#8e3d39' : '#145956'
    return `<rect x="${(x + col * cw + 1.7).toFixed(1)}" y="${(y + row * ch + 1.7).toFixed(1)}" width="${(cw - 3.4).toFixed(1)}" height="${(ch - 3.4).toFixed(1)}" fill="${fill}"/>`
  })).join('')
  const xTicks = [0, 5, 10, 15, 20].map(i => `<text x="${(x + (i + .5) * cw).toFixed(1)}" y="${y + h + 43}" text-anchor="middle" fill="${C.muted}" font-size="${compact ? 23 : 25}" font-family="Courier New">${hours[i].toFixed(2)}</text>`).join('')
  const yTicks = [1, .8, .6, .4, .2].map(soc => {
    const row = sorted.findIndex(value => Math.abs(value - soc) < 1e-6)
    return `<text x="${x - 20}" y="${(y + (row + .5) * ch + 8).toFixed(1)}" text-anchor="end" fill="${C.muted}" font-size="${compact ? 23 : 25}" font-family="Courier New">${Math.round(soc * 100)}%</text>`
  }).join('')
  const row80 = sorted.findIndex(value => Math.abs(value - .8) < 1e-6)
  const mx = x + (20.5) * cw
  const my = y + (row80 + .5) * ch
  const diamond = `<polygon points="${mx},${my - 18} ${mx + 18},${my} ${mx},${my + 18} ${mx - 18},${my}" fill="${C.amber}" stroke="#fff" stroke-width="4"/>`
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="display:block">
    <text x="${x}" y="66" fill="${C.muted}" font-size="25" font-family="Courier New" letter-spacing="3">INITIAL BATTERY CHARGE</text>
    ${cells}${diamond}${xTicks}${yTicks}
    <text x="${x + w / 2}" y="${height - 15}" text-anchor="middle" fill="${C.muted}" font-size="25" font-family="Courier New" letter-spacing="2">BLACKOUT DURATION / HOURS</text>
  </svg>`
}

function candidateRows(barWidth, rowHeight) {
  return design.candidates.map((candidate, i) => {
    const selected = candidate.capacity_kwh === 32
    const time = candidate.first_critical_failure_hours ?? 12
    const fill = candidate.survived_target ? C.teal : C.coral
    const y = i * rowHeight
    const status = candidate.survived_target ? 'PASS / 12 H WINDOW' : `FAIL / ${candidate.first_critical_failure_hours.toFixed(2)} H`
    return `<div style="display:grid;grid-template-columns:205px 1fr 380px;align-items:center;gap:36px;height:${rowHeight}px;padding:0 25px;border-bottom:2px solid ${C.line};${selected ? 'background:#102925;border-left:7px solid '+C.amber+';' : ''}">
      <div style="font:900 52px 'Arial Black',Arial,sans-serif;color:${selected ? C.amber : C.ink}">${candidate.capacity_kwh} <span style="font-size:28px">kWh</span></div>
      <div style="height:25px;background:#1a292b;position:relative;border-right:3px solid #dce5dc">
        <div style="height:25px;width:${time / 12 * 100}%;background:${fill}"></div>
      </div>
      <div style="font:700 29px 'Courier New',monospace;color:${fill};text-align:right">${status}</div>
    </div>`
  }).join('')
}

try {
  // Slide 9: a data-first comparison at 1920 x 1080.
  await render('03-optimization/battery-comparison-chart.png', 1920, 1080, `
    <div class="kicker" style="position:absolute;left:100px;top:70px">LASTLIGHT / BATTERY DESIGN SEARCH</div>
    <div class="title" style="position:absolute;left:100px;top:126px;font-size:100px">Four capacities.<br><span style="color:${C.amber}">One tested choice.</span></div>
    <div class="small" style="position:absolute;left:104px;top:338px">CRITICAL DEMAND SERVED UNTIL FIRST DEFICIT, OR THROUGH THE 12 H TEST WINDOW</div>
    <div style="position:absolute;left:100px;right:100px;top:405px">${candidateRows(820, 123)}</div>
    <div class="small" style="position:absolute;left:366px;top:910px;width:1013px;display:flex;justify-content:space-between"><span>0 H</span><span>3 H</span><span>6 H</span><span>9 H</span><span>12 H</span></div>
    <div class="rule" style="position:absolute;left:100px;right:100px;top:962px"></div>
    <div class="source" style="position:absolute;left:100px;top:984px">SYNTHETIC SCHOOL / 80% START CHARGE / 1.5 kW CRITICAL LOAD / 0 kW SOLAR</div>
    <div class="source" style="position:absolute;right:100px;top:1012px">OFFICIAL PHYSICS 1.0.0 · NO FIELD MEASUREMENT</div>
  `)

  await render('03-optimization/slide09-hero-result.png', 1920, 1080, `
    <div class="kicker" style="position:absolute;left:100px;top:76px">PHYSICS-VERIFIED DESIGN SEARCH</div>
    <div class="title" style="position:absolute;left:90px;top:185px;font-size:246px;color:${C.amber}">32<span style="font-size:100px"> kWh</span></div>
    <div class="title" style="position:absolute;left:103px;top:470px;font-size:62px;line-height:1.08">SMALLEST PASSING<br>TESTED CAPACITY</div>
    <div style="position:absolute;left:102px;top:675px;width:650px;height:4px;background:${C.teal}"></div>
    <div style="position:absolute;left:103px;top:708px;font:700 32px 'Courier New',monospace;line-height:1.6">24 / 30 <span style="color:${C.coral}">FAILED</span><br>32 / 36 <span style="color:${C.teal}">PASSED</span></div>
    <div style="position:absolute;left:912px;top:158px">${authenticModal(search, 864, 690)}</div>
    <div class="rule" style="position:absolute;left:100px;right:100px;top:925px"></div>
    <div class="source" style="position:absolute;left:103px;top:951px">12-HOUR SYNTHETIC BLACKOUT · FOUR OFFICIAL RUNS · NO EQUIPMENT PRICES</div>
    <div class="source" style="position:absolute;left:103px;top:992px">PASS = NO CRITICAL DEFICIT OBSERVED WITHIN THE TEST WINDOW</div>
  `)

  await render('03-optimization/slide09-optimization-square.png', 2000, 2000, `
    <div class="kicker" style="position:absolute;left:125px;top:90px">LASTLIGHT / ENGINEERING RESULT</div>
    <div class="title" style="position:absolute;left:110px;top:185px;font-size:305px;color:${C.amber}">32 <span style="font-size:145px">kWh</span></div>
    <div class="title" style="position:absolute;left:125px;top:495px;font-size:69px">SMALLEST PASSING TESTED CAPACITY</div>
    <div class="rule" style="position:absolute;left:125px;right:125px;top:620px"></div>
    <div style="position:absolute;left:125px;right:125px;top:675px">${candidateRows(740, 125)}</div>
    <div style="position:absolute;left:520px;top:1220px">${authenticModal(search, 960, 600, 300)}</div>
    <div class="source" style="position:absolute;left:125px;top:1187px">SOURCE / LIVE LOCAL PHYSICS API SCREENSHOT, UNALTERED WITHIN CROP</div>
    <div class="source" style="position:absolute;left:125px;top:1880px">SYNTHETIC 12 H TEST · 80% START CHARGE · NO COST OPTIMIZATION</div>
  `)

  // Slide 5: actual WebGL imagery drives both outputs.
  await render('01-inside-lastlight/slide05-hero-square.png', 2000, 2000, `
    <div class="kicker" style="position:absolute;left:120px;top:90px">01 / THE WORKING DIGITAL TWIN</div>
    <div class="title" style="position:absolute;left:110px;top:165px;font-size:142px">INSIDE LASTLIGHT</div>
    <div class="frame" style="position:absolute;left:120px;top:340px;width:1760px;height:990px"><img src="${hero}"></div>
    <div class="rule" style="position:absolute;left:120px;right:120px;top:1400px"></div>
    <div style="position:absolute;left:120px;top:1460px;width:790px"><div class="kicker">01 / ROOFTOP PV</div><div style="font-size:39px;font-weight:700;margin-top:26px">The school rooftop array is visible in the real 3D scene.</div></div>
    <div style="position:absolute;left:1000px;top:1460px;width:850px"><div class="kicker">02 / RESERVE SYSTEM</div><div style="font-size:39px;font-weight:700;margin-top:26px">Battery and inverter are inspectable in the real 3D scene.</div></div>
    <div class="source" style="position:absolute;left:120px;top:1875px">ACTUAL 1920 × 1080 CHROMIUM / WEBGL 2 FRAME · SYNTHETIC SCHOOL</div>
    <div class="source" style="position:absolute;left:120px;top:1918px">REFERENCE OUTAGE MODEL USES 0 kW SOLAR GENERATION</div>
  `)

  await render('01-inside-lastlight/slide05-before-after.png', 1920, 1080, `
    <div class="kicker" style="position:absolute;left:92px;top:65px">SAME CAMERA / REAL SCHOOL SCENE</div>
    <div class="title" style="position:absolute;left:90px;top:115px;font-size:91px">When the grid goes dark.</div>
    <div style="position:absolute;left:90px;top:305px">${schoolSceneCrop(connected)}</div>
    <div style="position:absolute;left:980px;top:305px">${schoolSceneCrop(blackout)}</div>
    <div style="position:absolute;left:90px;top:250px;font:900 34px 'Arial Black',Arial,sans-serif;color:${C.amber}">GRID CONNECTED</div>
    <div style="position:absolute;left:980px;top:250px;font:900 34px 'Arial Black',Arial,sans-serif;color:${C.teal}">GRID DISCONNECTED</div>
    <div class="source" style="position:absolute;left:92px;top:982px">ORDINARY LIGHTING TURNS OFF · CRITICAL DEMAND IS SERVED AT THE START OF THE OUTAGE</div>
    <div class="source" style="position:absolute;left:92px;top:1015px">MATCHED 1920 × 1080 WEBGL CAPTURES · LIVE LOCAL PHYSICS API / SYNTHETIC INPUTS</div>
  `)

  // Slide 8: every colored cell comes directly from the verified API trace.
  await render('02-failure-frontier/frontier-clean-chart.png', 2200, 1400, `
    <div class="kicker" style="position:absolute;left:100px;top:55px">PHYSICAL RESILIENCE MAP / 24 kWh BASELINE</div>
    <div class="title" style="position:absolute;left:90px;top:107px;font-size:110px">273 verified scenarios.</div>
    <div style="position:absolute;left:78px;top:270px">${frontierSvg(2050, 1000)}</div>
    <div style="position:absolute;left:295px;top:1280px;display:flex;gap:65px;font:700 23px 'Courier New',monospace">
      <span style="color:${C.teal}">■ SURVIVES HORIZON</span><span style="color:${C.coral}">■ CRITICAL DEFICIT</span><span style="color:${C.amber}">◆ ACTIVE 80% / 12 H CASE</span>
    </div>
    <div class="source" style="position:absolute;left:100px;top:1350px">13 OFFICIAL PHYSICS TRACES · SYNTHETIC SCHOOL · NO ML PREDICTIONS</div>
  `)

  await render('02-failure-frontier/slide08-frontier-square.png', 2000, 2000, `
    <div class="kicker" style="position:absolute;left:120px;top:90px">LASTLIGHT / FAILURE FRONTIER</div>
    <div class="title" style="position:absolute;left:110px;top:170px;font-size:144px;line-height:.95">273 PHYSICS-<br>VERIFIED SCENARIOS</div>
    <div style="position:absolute;left:125px;top:465px;color:${C.muted};font-size:38px">How starting charge and blackout duration change the result.</div>
    <div style="position:absolute;left:90px;top:600px">${frontierSvg(1830, 1100, true)}</div>
    <div style="position:absolute;left:175px;top:1710px;display:flex;gap:50px;font:700 26px 'Courier New',monospace">
      <span style="color:${C.teal}">■ SUSTAINED</span><span style="color:${C.coral}">■ DEFICIT</span><span style="color:${C.amber}">◆ BASELINE</span>
    </div>
    <div class="rule" style="position:absolute;left:120px;right:120px;top:1820px"></div>
    <div class="source" style="position:absolute;left:120px;top:1855px">24 kWh / 13 OFFICIAL TRACES / 273 CLASSIFIED CELLS / NO ML ESTIMATES</div>
    <div class="source" style="position:absolute;left:120px;top:1900px">SYNTHETIC SCHOOL · A FAILURE AT THE RIGHT EDGE IS OUTSIDE THAT TEST WINDOW</div>
  `)

  await render('04-fallback/first-critical-failure-presentation.png', 1920, 1080, `
    <div class="frame" style="position:absolute;left:0;top:0;width:1920px;height:1080px;border:0"><img src="${failure}"></div>
    <div style="position:absolute;left:0;top:0;width:950px;height:1080px;background:linear-gradient(90deg,rgba(3,7,8,.96),rgba(3,7,8,.74) 70%,transparent)"></div>
    <div class="kicker" style="position:absolute;left:95px;top:168px">SYNTHETIC SCHOOL / OFFICIAL PHYSICS</div>
    <div class="title" style="position:absolute;left:85px;top:270px;font-size:180px;color:${C.coral}">09:07:12</div>
    <div class="title" style="position:absolute;left:98px;top:500px;font-size:68px;line-height:1.1">FIRST CRITICAL<br>POWER DEFICIT</div>
    <div class="source" style="position:absolute;left:100px;top:990px">24 kWh BASELINE · 80% START CHARGE · 12 H OBSERVATION</div>
  `)

  console.log('Finished presentation PNG graphics.')
} finally {
  await browser.close()
}
