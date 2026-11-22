import { expect, type Page } from "@playwright/test";
import path from "node:path";
export const scene = path.resolve("e2e/fixtures/scene.jpg");
export async function connect(page: Page) {
  await page.goto("/");
  await expect(page.getByText("Servicio conectado", {exact:true})).toBeVisible();
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
