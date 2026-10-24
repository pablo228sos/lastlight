import { defineConfig } from '@playwright/test'
const webPort = Number(process.env.LASTLIGHT_WEB_TEST_PORT ?? 4173)
const apiPort = Number(process.env.LASTLIGHT_API_TEST_PORT ?? 8000)
export default defineConfig({
  testDir: './tests',
  reporter: 'list',
  timeout: 120000,
  // SwiftShader and model loading share CPU; parallel worlds starve animation frames on CI.
  workers: 1,
  use: {
    baseURL: `http://127.0.0.1:${webPort}`,
    browserName: 'chromium',
    channel: process.env.CI ? undefined : 'chrome',
    launchOptions: { args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] },
    trace: 'retain-on-failure',
  },
  webServer: [
    { command: `python -m uvicorn services.simulation.api:app --host 127.0.0.1 --port ${apiPort}`, cwd: '../..', port: apiPort, reuseExistingServer: !process.env.CI, timeout: 60000 },
    { command: `npm run dev -- --host 127.0.0.1 --port ${webPort}`, port: webPort, env: { LASTLIGHT_API_URL: `http://127.0.0.1:${apiPort}` }, reuseExistingServer: !process.env.CI, timeout: 30000 },
  ],
})
