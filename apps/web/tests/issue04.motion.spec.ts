/**
 * Genuine WebGL motion evidence in a laptop viewport, not Higgsfield video.
 * Separate opt-in workflow keeps this out of regular smoke tests.
 */
import { test,expect } from '@playwright/test'
import { mkdir,writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'

const enabled=process.env.LASTLIGHT_MOTION_CAPTURE==='1'
test.use({viewport:{width:1366,height:768},video:'on'})
test('record browser WebGL district pan and measure camera movement',async({page})=>{
  test.setTimeout(150_000)
  test.skip(!enabled,'Only runs in dedicated real camera motion workflow')
  const dest=resolve(process.cwd(),'artifacts','issue04','motion')
  await mkdir(dest,{recursive:true})
  const errors:string[]=[]
  page.on('pageerror',e=>errors.push(e.message))
  await page.goto('/?capture=1')
  await expect(page.locator('canvas')).toBeVisible()
  await page.getByTestId('skip-intro').click()
  await expect(page.locator('main')).toHaveAttribute('data-shot','district')
  const canvas=page.locator('canvas')
  await canvas.evaluate((el:HTMLCanvasElement)=>{
    el.dispatchEvent(new CustomEvent('lastlight:capture-lock-pose',{detail:{shot:'district'}}))
  })
  await expect.poll(async()=>canvas.getAttribute('data-camera-position')).toBe('81.000,63.000,83.000')
  await page.waitForTimeout(400)
  const image=await canvas.evaluate((el:HTMLCanvasElement)=>el.toDataURL('image/png'))
  await writeFile(resolve(dest,'district-before-pan-1366x768.png'),Buffer.from(image.split(',')[1],'base64'))

  const initial=(await canvas.getAttribute('data-camera-position'))!.split(',').map(Number)
  const bounds=await canvas.boundingBox()
  if(!bounds)throw Error('no WebGL canvas')
  const startX=bounds.x+bounds.width*.5,startY=bounds.y+bounds.height*.53
  await page.mouse.move(startX,startY)
  await page.mouse.down({button:'right'})
  await page.mouse.move(startX+140,startY+45,{steps:18})
  await page.mouse.up({button:'right'})
  await page.waitForTimeout(600)
  const finalPos=(await canvas.getAttribute('data-camera-position'))!.split(',').map(Number)
  const delta=Math.hypot(...finalPos.map((v,i)=>v-initial[i]))
  expect(delta).toBeGreaterThan(1)
  await expect(page.locator('main')).toHaveAttribute('data-phase','DISTRICT')
  await expect(page.locator('main')).toHaveAttribute('data-shot','district')
  expect(errors).toEqual([])
  await writeFile(resolve(dest,'motion-manifest.json'),JSON.stringify({
    source:'real Chromium WebGL',viewport:'1366x768',
    cameraStart:initial,cameraEnd:finalPos,distanceMovedWorldUnits:delta,
    mouseInput:'right-button pan',sceneSwitched:false,physicsValid:false,
    fpsBenchmarked:false,recordedVideoIsNotAI:true,
  },null,2))
  const video=page.video()
  await page.close()
  if(!video)throw Error('Playwright video recorder unavailable')
  await video.saveAs(resolve(dest,'district-right-drag-1366x768.webm'))
})
