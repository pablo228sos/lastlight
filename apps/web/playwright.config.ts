import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests',
  reporter: 'list',
  timeout: 120000,
  // WebGL scenes share a GPU context; parallel pages can stall camera timing.
  workers: 1,
  use: {
    baseURL: process.env.LASTLIGHT_WEB_URL || 'http://127.0.0.1:4173',
    browserName: 'chromium',
    channel: process.env.CI ? undefined : 'chrome',
    launchOptions: { args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] },
  },
  webServer: process.env.LASTLIGHT_WEB_URL ? undefined : { command: 'npm run dev -- --host 127.0.0.1 --port 4173', port: 4173, reuseExistingServer: !process.env.CI, timeout: 30000 },
})
