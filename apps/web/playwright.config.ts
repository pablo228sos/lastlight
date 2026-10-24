import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests',
  reporter: 'list',
  timeout: 120000,
  // SwiftShader and model loading share CPU; parallel worlds starve animation frames on CI.
  workers: 1,
  use: {
    baseURL: 'http://127.0.0.1:4173',
    browserName: 'chromium',
    channel: process.env.CI ? undefined : 'chrome',
    launchOptions: { args: ['--enable-webgl', '--use-gl=angle', '--use-angle=swiftshader'] },
    trace: 'retain-on-failure',
  },
  webServer: [
    { command: 'python -m uvicorn services.simulation.api:app --host 127.0.0.1 --port 8000', cwd: '../..', port: 8000, reuseExistingServer: !process.env.CI, timeout: 60000 },
    { command: 'npm run dev -- --host 127.0.0.1 --port 4173', port: 4173, reuseExistingServer: !process.env.CI, timeout: 30000 },
  ],
})
