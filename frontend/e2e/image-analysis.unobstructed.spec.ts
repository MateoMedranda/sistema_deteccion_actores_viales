import {test,expect} from "@playwright/test";
import {connect} from "./helpers";
import {annotationScenes,serveAnnotation,annotationFile} from "./annotation-scenarios";
test("ten clean scenes, contextual identity and no overlaid labels at 200% text",async({page},info)=>{
 test.setTimeout(120000);
 await connect(page);
 for(const scene of annotationScenes){
  const calls=await serveAnnotation(page,scene);
  await page.getByLabel("Seleccionar imagen",{exact:true}).setInputFiles(annotationFile(scene));
  await page.getByRole("button",{name:"Analizar imagen"}).click();
  await expect(page.locator(".scene-viewer img")).toBeVisible();
  await expect(page.locator(".detection-list button")).toHaveCount(scene.results.length);
  expect(calls.annotations).toBe(0);
  expect(await page.locator(".scene-viewer").innerText()).toBe("");
  expect(await page.locator(".scene-viewer button").evaluateAll(bs=>bs.every(b=>["none",'""',"normal"].includes(getComputedStyle(b,"::after").content)))).toBe(true);
  const pixel=await page.locator(".scene-viewer img").evaluate((img:HTMLImageElement)=>{const c=document.createElement("canvas");c.width=c.height=1;const x=c.getContext("2d")!;x.drawImage(img,0,0);return [...x.getImageData(0,0,1,1).data];});
  expect(pixel.slice(0,3)).toEqual(scene.name.endsWith("0")||scene.name.endsWith("2")||scene.name.endsWith("4")||scene.name.endsWith("6")||scene.name.endsWith("8")?[0,0,0]:[255,255,255]);
  const first=scene.results[0].detection_id,second=scene.results[1].detection_id;
  const list=page.locator(".detection-list button");
  const start=await page.evaluate(()=>performance.now());
  await list.nth(1).focus();
  await expect(page.locator(".detection-context")).toContainText("#"+second);
  await expect(page.locator(".details-heading h3")).toHaveText("Detección "+first);
  await list.nth(1).press("Enter");
  await expect(page.locator(".details-heading h3")).toHaveText("Detección "+second);
  expect((await page.evaluate(()=>performance.now()))-start).toBeLessThan(1000);
  // Every eligible identity remains reachable, including tiny/overlapping boxes.
  for(let i=0;i<scene.results.length;i++){
   const id=scene.results[i].detection_id,control=list.nth(i);
   if(info.project.name==="desktop"){await control.focus();await control.press("Enter");}
   else await control.tap();
   await expect(page.locator(".details-heading h3")).toHaveText("Detección "+id);
   await expect(page.locator(".scene-viewer button[aria-label^='Detección "+id+",']")).toHaveAttribute("aria-pressed","true");
   await expect(page.locator(".context-id")).toHaveText("#"+id);
  }
  expect(calls.posts).toBe(2);
  await page.addStyleTag({content:"html{font-size:200% !important}"});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  expect(await page.locator(".context-id").evaluate(el=>getComputedStyle(el).whiteSpace)).toBe("nowrap");
  await page.screenshot({path:info.outputPath(scene.name+".png"),fullPage:true});
  await page.addStyleTag({content:"html{font-size:100% !important}"});
  await page.getByRole("button",{name:"Limpiar imagen",exact:true}).click();
 }
});
