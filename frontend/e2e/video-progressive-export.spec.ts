import {test,expect} from "@playwright/test";
import path from "node:path";
import {stat} from "node:fs/promises";

test("exports an annotated MP4 only on request without another detection",async({page,request},info)=>{
  await request.post("http://127.0.0.1:9415/test-only/reset?scenario=short");
  const exports:string[]=[];
  page.on("request",r=>{if(r.method()==="POST"&&r.url().endsWith("/playback/export"))exports.push(r.url());});
  await page.goto("/");
  await expect(page.locator("main")).toHaveAttribute("data-session-state","ready");
  await page.getByRole("tab",{name:"Video",exact:true}).click();
  await page.locator('input[type="file"][aria-label="Video"]').setInputFiles(path.resolve("../.runtime/e2e-009/source.mp4"));
  await page.getByRole("button",{name:"Procesar video",exact:true}).click();
  const button=page.getByRole("button",{name:"Exportar video anotado",exact:true});
  await expect(button).toBeEnabled({timeout:30000});
  expect(exports).toHaveLength(0);
  const before=(await(await request.get("http://127.0.0.1:9415/test-only/calls")).json()).calls;
  await button.click();
  const link=page.getByRole("link",{name:"Descargar MP4",exact:true});
  await expect(link).toBeVisible({timeout:30000});
  expect(exports).toHaveLength(1);
  expect((await(await request.get("http://127.0.0.1:9415/test-only/calls")).json()).calls).toBe(before);
  const downloading=page.waitForEvent("download");
  await link.click();
  const download=await downloading;
  expect(await download.failure()).toBeNull();
  expect(download.suggestedFilename()).toMatch(/\.mp4$/);
  expect((await stat((await download.path())!)).size).toBeGreaterThan(100);
  await page.screenshot({path:info.outputPath("export-ready.png"),fullPage:true});
});

test.afterEach(async({request})=>{await request.post("http://127.0.0.1:9415/test-only/release");});
