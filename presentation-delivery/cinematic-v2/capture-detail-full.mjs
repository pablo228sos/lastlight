import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {rename,writeFile} from 'node:fs/promises';
const require=createRequire(new URL('../../apps/web/package.json',import.meta.url));
const {chromium,expect}=require('@playwright/test');
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-webgl','--enable-gpu','--use-gl=angle','--use-angle=d3d11','--disable-software-rasterizer']});
const out=resolve('presentation-delivery/cinematic-v2/assets');
const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,baseURL:'http://127.0.0.1:4173',recordVideo:{dir:out,size:{width:1920,height:1080}}});
const page=await context.newPage();
const start=Date.now(),marks={};
try{
  await page.goto('/?capture=1',{waitUntil:'domcontentloaded'});
  await expect(page.getByTestId('skip-intro')).toBeVisible();
  await page.getByTestId('skip-intro').click();
  await page.getByTestId('focus-school').click();
  await page.waitForTimeout(2000);
  await page.getByTestId('inspect').click();
  await page.waitForTimeout(1800);
  marks.zoom_start=(Date.now()-start)/1000;
  await page.mouse.move(960,540);
  for(let i=0;i<6;i++){await page.mouse.wheel(0,-450);await page.waitForTimeout(240)}
  await page.waitForTimeout(1600);
  marks.zoom_end=(Date.now()-start)/1000;
}finally{
  const video=page.video();await context.close();
  if(video)await rename(await video.path(),resolve(out,'roof-zoom-full-browser.webm'));
  await writeFile(resolve(out,'roof-zoom-marks.json'),JSON.stringify(marks,null,2));
  await browser.close();
}
