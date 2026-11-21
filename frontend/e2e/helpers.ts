import { expect, type Page } from "@playwright/test";
import path from "node:path";
export const scene = path.resolve("e2e/fixtures/scene.jpg");
export async function connect(page: Page) {
  await page.goto("/");
  await page.getByText("Configurar sesión", { exact: true }).click();
  await page.getByLabel("URL backend").fill("http://127.0.0.1:8767");
  await page.getByLabel("API key", { exact: true }).fill("ui-synthetic-key");
  await page.getByText("Configurar sesión", { exact: true }).click();
}
export async function analyze(page: Page) {
  await connect(page);
  await page
    .getByLabel("Seleccionar imagen", { exact: true })
    .setInputFiles(scene);
  await page.getByRole("button", { name: "Analizar imagen" }).click();
}
export async function complete(page: Page) {
  await analyze(page);
  await expect(
    page.getByText("Análisis completo", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("img", { name: "Recorte del vehículo", exact: true }),
  ).toBeVisible();
}
