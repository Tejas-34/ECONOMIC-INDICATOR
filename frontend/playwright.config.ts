import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig({
  testDir: './tests/visual',
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: true,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
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
    command: 'npm run dev',
    port: 5173,
    cwd: __dirname,
    reuseExistingServer: !process.env.CI,
  },
});
