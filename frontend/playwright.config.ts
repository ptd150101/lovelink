import { defineConfig, devices } from "@playwright/test";

const fakeMediaArgs = [
  "--use-fake-device-for-media-stream",
  "--use-fake-ui-for-media-stream",
];

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 8_000 },
  fullyParallel: true,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: process.env.CI
    ? undefined
    : {
        command: "npm run dev",
        url: "http://127.0.0.1:3000",
        reuseExistingServer: true,
        timeout: 120_000,
      },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: { args: fakeMediaArgs },
      },
    },
    {
      name: "mobile",
      use: {
        ...devices["iPhone 13"],
        launchOptions: { args: fakeMediaArgs },
      },
    },
  ],
});
