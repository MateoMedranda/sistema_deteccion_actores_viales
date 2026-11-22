import { existsSync } from "node:fs";

const executable = process.platform === "win32" ? "Scripts/python.exe" : "bin/python";
const localEnvironment = new URL(`../backend/.venv/${executable}`, import.meta.url);
export const backendPython = existsSync(localEnvironment)
  ? `".venv/${executable}"`
  : `"../.venv/${executable}"`;
