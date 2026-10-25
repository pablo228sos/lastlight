import { createRequire } from 'node:module';
import { mkdir, stat, unlink, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const require = createRequire(new URL('../../apps/web/package.json', import.meta.url));
const { chromium, expect } = require('@playwright/test');
const out = resolve('presentation-delivery/cinematic-v2/assets');
await mkdir(out, { recursive: true });

const browser = await chromium.launch({channel:'chrome',headless:true,args:['--enable-webgl','--enable-gpu','--use-gl=angle','--use-angle=d3d11','--disable-software-rasterizer']});
const context = await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,baseURL:'http://127.0.0.1:4173',acceptDownloads:true});
const page = await context.newPage();
page.setDefaultTimeout(60000);
const pause = (ms)=>page.waitForTimeout(ms);
const snap = async (name)=>page.screenshot({path:resolve(out,`${name}.png`)});
const capture = async (name,ms,action) => {
  const supported = await page.evaluate(()=>({types:['video/webm;codecs=vp9','video/webm;codecs=vp8'].filter(MediaRecorder.isTypeSupported),canvas:!!document.querySelector('canvas')}));
  if (!supported.canvas || !supported.types.length) throw new Error(JSON.stringify(supported));
  await page.evaluate(({mimeType})=>{
    const canvas=document.querySelector('canvas');
    const stream=canvas.captureStream(30);
    window.__captureChunks=[];
    window.__captureRecorder=new MediaRecorder(stream,{mimeType,videoBitsPerSecond:10000000});
    window.__captureRecorder.ondataavailable=(e)=>{if(e.data.size)window.__captureChunks.push(e.data)};
    window.__captureRecorder.start(500);
  },{mimeType:supported.types[1]});
  if(action) await action();
  await pause(ms);
  const downloadPromise=page.waitForEvent('download');
  await page.evaluate((filename)=>new Promise((resolveDownload)=>{
    const recorder=window.__captureRecorder;
    recorder.onstop=()=>{
      const blob=new Blob(window.__captureChunks,{type:recorder.mimeType});
      const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download=filename;link.click();
      resolveDownload();
    };
    recorder.stop();
  }),`${name}.webm`);
  const download=await downloadPromise;
  const path=resolve(out,`${name}.webm`);
  await download.saveAs(path);
  const bytes=(await stat(path)).size;
  if(bytes===0){await unlink(path);console.warn(name,'no encoded frames; use the full-browser capture for this shot')}
  else console.log(name,bytes,JSON.stringify(supported));
};

try {
  await page.goto('/?capture=1',{waitUntil:'domcontentloaded'});
  console.log('webgl renderer',await page.evaluate(()=>{const gl=document.createElement('canvas').getContext('webgl');const ext=gl?.getExtension('WEBGL_debug_renderer_info');return ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'unknown'}));
  await expect(page.getByTestId('enter-lab')).toBeVisible();
  await pause(2500);
  await capture('00-encoder-warmup',900);
  await capture('01-district-approach',4200,async()=>{await page.getByTestId('enter-lab').click()});
  await capture('02-school-hero',3800,async()=>{await page.getByTestId('focus-school').click()});
  await snap('02-school-hero-ui');
  if(process.argv[2]==='early') {
    console.log('early capture complete');
  } else {
  await capture('03-equipment',3300,async()=>{await page.getByTestId('inspect').click()});
  await snap('03-equipment-ui');
  await capture('04-school-orbit',3000,async()=>{await page.getByTestId('orbit').click()});
  await page.getByTestId('site-school').click();
  await pause(2200);
  await snap('05-before-blackout-ui');
  await capture('05-blackout',4500,async()=>{
    await page.getByTestId('disconnect-grid').click();
    await expect(page.getByTestId('physics-instrument')).toBeVisible();
    await expect(page.getByTestId('rehearsal-label')).toContainText('LIVE LOCAL PHYSICS API');
  });
  await snap('05-blackout-ui');
  await page.getByTestId('simulation-scrub').evaluate((input)=>{
    const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
    setter.call(input,'9.121');input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));
  });
  await expect(page.getByTestId('engineering-verdict')).toContainText('09:07:12');
  await snap('06-first-failure-ui');
  await capture('06-first-failure',2000);
  await page.getByTestId('compare-upgrade').click();
  await expect(page.getByTestId('comparison-result')).toBeVisible();
  await page.getByTestId('show-upgraded').click();
  await page.getByTestId('simulation-scrub').evaluate((input)=>{
    const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
    setter.call(input,'12');input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));
  });
  await expect(page.getByTestId('engineering-verdict')).toContainText('SUSTAINED 12:00:00');
  await snap('07-upgrade-ui');
  await capture('07-upgraded-school',2600);
  await page.getByTestId('open-design-search').click();
  await expect(page.getByTestId('design-selected')).toHaveText('32 kWh');
  await snap('08-capacity-search-ui');
  await page.keyboard.press('Escape');
  await page.getByTestId('open-frontier').click();
  await expect(page.getByTestId('frontier-panel')).toContainText('273 VERIFIED CELLS');
  await snap('09-frontier-ui');
  await page.keyboard.press('Escape');
  await page.getByRole('button',{name:/data & methods/i}).click();
  await snap('10-report-ui');
  const downloadPromise=page.waitForEvent('download');
  await page.getByTestId('download-report').click();
  await (await downloadPromise).saveAs(resolve(out,'actual-live-report.json'));
  await writeFile(resolve(out,'capture-provenance.json'),JSON.stringify({url:'http://127.0.0.1:4173/?capture=1',browser:'Google Chrome / Playwright on NVIDIA RTX 3070 D3D11',viewport:'1920x1080',capture:'HTMLCanvasElement.captureStream(30), MediaRecorder VP8 target 10 Mbps',physics:'Live local Physics API',recorded:new Date().toISOString()},null,2));
  }
}finally{await context.close();await browser.close()}
