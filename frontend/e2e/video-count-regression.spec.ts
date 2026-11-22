import {readFileSync} from "node:fs";
import { test, expect } from "@playwright/test";
import path from "node:path";
import { connect } from "./helpers";
test("existing video, line, count and video enrichment remain usable", async ({
  page,
}) => {
  await connect(page);
  await page
    .getByRole("tab", {name:"Video",exact:true})
    .click();
  await page
    .locator('input[aria-label="Video"]')
    .setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
  await page
    .getByRole("button", { name: "Procesar video", exact: true })
    .click();
  await expect(page.locator("video.result-video")).toBeVisible({timeout:15000});
  await page.getByText("Conteo por línea",{exact:true}).click();
  const editor = page.locator(".line-editor");
  await editor.scrollIntoViewIfNeeded();
  const rect = await editor.boundingBox();
  await page.mouse.move(
    rect!.x + rect!.width * 0.2,
    rect!.y + rect!.height * 0.5,
  );
  await page.mouse.down();
  await page.mouse.move(
    rect!.x + rect!.width * 0.8,
    rect!.y + rect!.height * 0.5,
  );
  await page.mouse.up();
  await page
    .getByRole("button", { name: "Iniciar conteo", exact: true })
    .click();
  const counts=page.getByRole("heading",{name:"Conteo",exact:true}).locator("..");
  await expect(counts.getByRole("status")).toContainText("completed", {
    timeout: 15000,
  });
  await expect(page.getByText("Enriquecimiento completado",{exact:true})).toBeVisible();
  await page.getByRole("button",{name:/Trayectoria/}).first().click();
  await expect(page.locator(".video-track-details")).toContainText("SYN123");
});

test("clearing or replacing the line prevents stale count requests",async({page})=>{
 await connect(page);await page.getByRole("tab",{name:"Video",exact:true}).click();
 await page.locator('input[aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
 await page.getByRole("button",{name:"Procesar video",exact:true}).click();
 await expect(page.locator("video.result-video")).toBeVisible({timeout:15000});
 await page.getByText("Conteo por línea",{exact:true}).click();
 let countPosts=0;page.on("request",r=>{if(r.method()==="POST"&&r.url().endsWith("/count-jobs"))countPosts++;});
 const draw=async()=>{const editor=page.locator(".line-editor");await editor.scrollIntoViewIfNeeded();const box=await editor.boundingBox();await page.mouse.move(box!.x+box!.width*.2,box!.y+box!.height*.4);await page.mouse.down();await page.mouse.move(box!.x+box!.width*.8,box!.y+box!.height*.6);await page.mouse.up();};
 await draw();await expect(page.locator(".line-handle")).toHaveCount(2);
 await page.getByRole("button",{name:"Borrar l\u00ednea",exact:true}).click();
 await page.getByRole("button",{name:"Iniciar conteo",exact:true}).click();await expect(page.getByText("Completa video y l\u00ednea primero.",{exact:true})).toBeVisible();expect(countPosts).toBe(0);
 await draw();await page.getByRole("button",{name:"Iniciar conteo",exact:true}).click();await expect.poll(()=>countPosts).toBe(1);
 const panel=page.getByRole("heading",{name:"Conteo",exact:true}).locator("..");await expect(panel.getByRole("status")).toContainText("completed");
 await page.locator('input[aria-label="Video"]').setInputFiles({name:"replacement.mp4",mimeType:"video/mp4",buffer:readFileSync(path.resolve("e2e/fixtures/controlled.mp4"))});
 await expect(page.locator(".line-handle")).toHaveCount(0);await expect(page.getByRole("button",{name:"Iniciar conteo",exact:true})).toHaveCount(0);expect(countPosts).toBe(1);
});
