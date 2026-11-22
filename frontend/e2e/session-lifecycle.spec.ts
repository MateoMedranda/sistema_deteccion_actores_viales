import { test, expect } from "@playwright/test";
import { complete } from "./helpers";
test("reset removes scene, crops and credentials without persistence", async ({
  page,
}) => {
  await complete(page);
  await page.getByRole("button",{name:"Reiniciar sesión"}).click();
  await expect(page.getByLabel("API key",{exact:true})).toHaveCount(0);
  await expect(page.getByLabel("URL backend")).toHaveCount(0);
  await expect(page.locator(".scene-viewer")).toHaveCount(0);
  await expect(page.getByText("SYN123", { exact: true })).toHaveCount(0);
  const stored = await page.evaluate(async () => ({
    local: localStorage.length,
    session: sessionStorage.length,
    databases: (await indexedDB.databases()).length,
  }));
  expect(stored).toEqual({ local: 0, session: 0, databases: 0 });
});
