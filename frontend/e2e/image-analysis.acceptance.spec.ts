import { test, expect } from "@playwright/test";
import { connect } from "./helpers";
import { scenes, serveScenes, chooseScene, verifyVehicle } from "./exploration";
test("ten distinct scenes preserve all twenty vehicle and plate identities", async ({
  page,
}, testInfo) => {
  await serveScenes(page, scenes.slice(0, 10));
  await connect(page);
  for (const scene of scenes.slice(0, 10)) {
    await chooseScene(page, scene);
    for (let i = 0; i < 2; i++)
      await verifyVehicle(
        page,
        scene.expected[i],
        i,
        testInfo.project.name !== "desktop",
      );
  }
});
test("all pages are consumed and nonconsecutive IDs stay associated on screen", async ({
  page,
}, testInfo) => {
  const scene = scenes.find((s) => s.name === "many"),
    pages = await serveScenes(page, [scene]);
  await connect(page);
  await chooseScene(page, scene);
  await expect(page.locator(".detection-list button")).toHaveCount(55);
  expect(pages).toEqual([1, 2]);
  for (const index of [0, 24, 50, 54])
    await verifyVehicle(
      page,
      scene.expected[index],
      index,
      testInfo.project.name !== "desktop",
    );
});
test("loaded vehicle details appear within one second using a monotonic clock", async ({
  page,
}, testInfo) => {
  const scene = scenes[0];
  await serveScenes(page, [scene]);
  await connect(page);
  await chooseScene(page, scene);
  await verifyVehicle(page, scene.expected[0], 0);
  const durations: number[] = [];
  for (let n = 0; n < 6; n++) {
    const index = (n + 1) % 2,
      start = await page.evaluate(() => performance.now());
    await verifyVehicle(page, scene.expected[index], index);
    const duration = (await page.evaluate(() => performance.now())) - start;
    durations.push(duration);
    expect(duration).toBeLessThan(1000);
  }
  await testInfo.attach("loaded-detail-latency", {
    body: JSON.stringify({
      viewport: testInfo.project.use.viewport,
      durations_ms: durations,
      includes:
        "selection, correct details and local crop; source and enrichment already loaded",
    }),
    contentType: "application/json",
  });
});
