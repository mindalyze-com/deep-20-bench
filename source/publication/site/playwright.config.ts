import { defineConfig } from "@playwright/test";

const baseURL = "http://127.0.0.1:4173/deep-20-bench/";

export default defineConfig({
  testDir: "./tests/ui",
  fullyParallel: true,
  workers: process.env.CI ? 2 : "75%",
  timeout: 30_000,
  retries: 0,
  expect: {
    timeout: 8_000,
    toHaveScreenshot: {
      animations: "disabled",
      caret: "hide",
      maxDiffPixels: 0,
    },
  },
  reporter: process.env.CI
    ? [["github"], ["html", { open: "never" }]]
    : [["line"]],
  use: {
    baseURL,
    colorScheme: "light",
    deviceScaleFactor: 1,
    locale: "en-US",
    timezoneId: "UTC",
    contextOptions: {
      reducedMotion: "reduce",
    },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "desktop-chromium",
      grep: /@(desktop|both)/,
      use: {
        browserName: "chromium",
        viewport: { width: 1280, height: 720 },
      },
    },
    {
      name: "mobile-chromium",
      grep: /@(mobile|both)/,
      use: {
        browserName: "chromium",
        hasTouch: true,
        isMobile: true,
        viewport: { width: 390, height: 844 },
      },
    },
    {
      name: "firefox-smoke",
      grep: /(?=.*@smoke)(?=.*@(desktop|both))/,
      use: {
        browserName: "firefox",
        viewport: { width: 1280, height: 720 },
      },
    },
    {
      name: "webkit-smoke",
      grep: /(?=.*@smoke)(?=.*@(desktop|both))/,
      use: {
        browserName: "webkit",
        viewport: { width: 1280, height: 720 },
      },
    },
  ],
  webServer: [
    {
      command: "npm run dev -- --host 127.0.0.1 --port 4173",
      url: baseURL,
      reuseExistingServer: true,
      timeout: 120_000,
    },
    {
      command:
        "DEEP20_OUTPUT_DIR=../../../docs npm run preview -- --host 127.0.0.1 --port 4174",
      url: "http://127.0.0.1:4174/deep-20-bench/",
      reuseExistingServer: true,
      timeout: 120_000,
    },
  ],
});
