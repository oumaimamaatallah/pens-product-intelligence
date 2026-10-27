import { defineConfig } from "@playwright/test"
const external = process.env.PLAYWRIGHT_BASE_URL
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  timeout: 45000,
  use: {
    baseURL: external || "http://127.0.0.1:8515",
    browserName: "chromium",
    channel: process.env.PLAYWRIGHT_CHANNEL || undefined,
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 1000 } } },
    {
      name: "mobile",
      use: { isMobile: true, hasTouch: true, viewport: { width: 390, height: 844 } },
    },
  ],
  webServer: external
    ? undefined
    : {
        command:
          (process.env.APP_PYTHON || "python") +
          " -m uvicorn server:app --host 127.0.0.1 --port 8515",
        cwd: "..",
        url: "http://127.0.0.1:8515/health",
        reuseExistingServer: false,
        timeout: 60000,
      },
})
