import {fileURLToPath} from "node:url";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  server:{fs:{allow:[fileURLToPath(new URL(".",import.meta.url)),fileURLToPath(new URL("../app/domain/class_presentation.json",import.meta.url))]},proxy:{"/web":{target:"http://127.0.0.1:4174",changeOrigin:false}}},
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
    restoreMocks: true,
  },
});
