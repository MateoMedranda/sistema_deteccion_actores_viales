import { test, expect } from "@playwright/test";
import { complete } from "./helpers";
test("single action exercises real test API, annotations and canonical crops", async ({
  page,
}) => {
  const posts: string[] = [];
  page.on("request", (r) => {
    if (r.method() === "POST") posts.push(new URL(r.url()).pathname);
  });
  await complete(page);
  await expect(page.getByText("SYN123", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("img", { name: "Recorte de la placa", exact: true }),
  ).toBeVisible();
  expect(posts.filter((p) => p.endsWith("/images"))).toHaveLength(1);
  expect(posts.filter((p) => p.endsWith("/enrichment-jobs"))).toHaveLength(1);
  await expect(page.getByText(/Track ID/)).toHaveCount(0);
});
