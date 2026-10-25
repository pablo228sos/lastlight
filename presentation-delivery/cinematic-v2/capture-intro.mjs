import {createRequire} from 'node:module';
import {resolve} from 'node:path';
import {mkdir,rename,writeFile} from 'node:fs/promises';
const require=createRequire(new URL('../../apps/web/package.json',import.meta.url));
const {chromium,expect}=require('@playwright/test');
const out=resolve('presentation-delivery/cinematic-v2/assets');
await mkdir(out,{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-webgl','--enable-gpu','--use-gl=angle','--use-angle=d3d11','--disable-software-rasterizer']});
const context=await browser.newContext({viewport:{width:1920,height:1080},deviceScaleFactor:1,baseURL:'http://127.0.0.1:4173',recordVideo:{dir:out,size:{width:1920,height:1080}}});
const page=await context.newPage();
const start=Date.now(),marks={};
try{
  await page.goto('/?capture=1',{waitUntil:'domcontentloaded'});
  await expect(page.getByTestId('enter-lab')).toBeVisible();
  await page.waitForTimeout(2500);
  marks.enter=(Date.now()-start)/1000;
  await page.getByTestId('enter-lab').click();
  await page.waitForTimeout(5200);
  marks.school=(Date.now()-start)/1000;
  await page.getByTestId('focus-school').click();
  await page.waitForTimeout(4000);
}finally{
  const video=page.video();
  await context.close();
  if(video)await rename(await video.path(),resolve(out,'intro-full-browser.webm'));
  await writeFile(resolve(out,'intro-marks.json'),JSON.stringify(marks,null,2));
  await browser.close();
}
