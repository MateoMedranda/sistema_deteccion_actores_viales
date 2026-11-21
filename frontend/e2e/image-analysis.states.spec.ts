import { test, expect } from "@playwright/test";
import { analyze } from "./helpers";
import { mockScenario } from "./scenarios";
for (const [scenario, label] of [
  ["detecting", "Detectando actores"],
  ["enriching", "Procesando vehículos"],
  ["partial", "Resultado parcial"],
  ["empty", "Sin vehículos elegibles"],
  ["error", "Requiere atención"],
  ["cancelled", "Enriquecimiento cancelado"],
  ["interrupted", "Consulta interrumpida"],
  ["expired", "Evidencia vencida"],
]) {
  test("controlled " + scenario + " state", async ({ page }, info) => {
    await mockScenario(page, scenario);
    await analyze(page);
    await expect(page.locator(".analysis-status strong")).toHaveText(label);
    if (scenario === "enriching") {
      const button = page.locator(".detection-list button").last();
      await button.click();
      await expect(button).toHaveAttribute("aria-pressed", "true");
      await expect(page.locator("#vehicle-details h3")).toHaveText(
        "Detección 2",
      );
    }
    if (scenario === "partial")
      await expect(
        page.getByText("No se pudieron consultar los atributos."),
      ).toBeVisible();
    if (scenario === "expired")
      await expect(page.locator(".scene-viewer")).toHaveCount(0);
    await page.screenshot({
      path: info.outputPath(scenario + ".png"),
      fullPage: true,
    });
  });
}
