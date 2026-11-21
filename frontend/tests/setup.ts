import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";
afterEach(() => cleanup());
if (!URL.createObjectURL)
  URL.createObjectURL = vi.fn(() => "blob:test-resource");
if (!URL.revokeObjectURL) URL.revokeObjectURL = vi.fn();

Object.defineProperty(HTMLImageElement.prototype, "decode", {
  configurable: true,
  value: () => Promise.resolve(),
});
Object.defineProperty(HTMLImageElement.prototype, "naturalWidth", {
  configurable: true,
  get: () => 640,
});
Object.defineProperty(HTMLImageElement.prototype, "naturalHeight", {
  configurable: true,
  get: () => 400,
});
