import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
const executable =
  process.platform === "win32" ? "Scripts/python.exe" : "bin/python";
const selected = ["../backend/.venv", "../.venv"]
  .map((p) => path.resolve(p, executable))
  .find(
    (p) =>
      existsSync(p) &&
      spawnSync(
        p,
        ["-c", "import sys,av,fastapi;assert sys.version_info[:2]==(3,12)"],
        { windowsHide: true },
      ).status === 0,
  );
if (!selected)
  throw Error(
    "Instala las dependencias de backend con Python 3.12 antes de ejecutar las pruebas.",
  );
process.env.PROGRESSIVE_TEST_PYTHON = selected;
const python = '"' + selected + '"';
export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/progressiveSetup.ts",
  testMatch: /video-progressive.*\.spec\.ts/,
  outputDir: "test-results/009-artifacts",
  workers: 1,
  fullyParallel: false,
  timeout: 60000,
  reporter: [["list"], ["json", { outputFile: "test-results/009.json" }]],
  use: { baseURL: "http://127.0.0.1:9413", trace: "retain-on-failure" },
  projects: [
    {
      name: "firefox",
      use: {
        ...devices["Desktop Firefox"],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "webkit",
      use: {
        ...devices["Desktop Safari"],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "desktop",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1440, height: 1000 },
      },
    },
    {
      name: "tablet",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 768, height: 1024 },
        hasTouch: true,
      },
    },
    {
      name: "mobile",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 360, height: 800 },
        hasTouch: true,
      },
    },
  ],
  webServer: [
    {
      command:
        python +
        " -m uvicorn tests.e2e.serve_progressive_gateway_009:app --host 127.0.0.1 --port 9414",
      cwd: "../backend",
      url: "http://127.0.0.1:9414/health/live",
      reuseExistingServer: false,
    },
    {
      command:
        python +
        " -m uvicorn tests.e2e.serve_progressive_009:app --host 127.0.0.1 --port 9415",
      cwd: "../backend",
      url: "http://127.0.0.1:9415/health/live",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 9413 --strictPort",
      env: { TEST_WEB_PROXY: "http://127.0.0.1:9414" },
      url: "http://127.0.0.1:9413",
      reuseExistingServer: false,
    },
  ],
});
