import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  testDir: './tests/visual',
  timeout: 30000,
  expect: {
    timeout: 10000,
  },
  fullyParallel: false,
  reporter: process.env.CI ? 'dot' : 'list',
  use: {
    baseURL: 'http://localhost:5174',
    trace: 'on-first-retry',
    viewport: { width: 1214, height: 2159 },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1214, height: 2159 } },
    },
  ],
  webServer: {
    command: 'VITE_USE_MOCKS=true npm run dev -- --port 5174',
    port: 5174,
    cwd: __dirname,
    reuseExistingServer: !process.env.CI,
    env: {
      VITE_USE_MOCKS: 'true',
    },
  },
});
