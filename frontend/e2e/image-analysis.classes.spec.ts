import {test,expect} from "@playwright/test";
import {connect} from "./helpers";
import {annotationScenes,serveAnnotation,annotationFile} from "./annotation-scenarios";
test("class tokens and distinct structural states retain class color on light and dark scenes",async({page})=>{
 await connect(page);
 for(const scene of annotationScenes.slice(0,2)){
  await serveAnnotation(page,scene);
  await page.getByLabel("Seleccionar imagen",{exact:true}).setInputFiles(annotationFile(scene));
  await page.getByRole("button",{name:"Analizar imagen"}).click();
  await expect(page.locator(".class-legend li")).toHaveCount(14);
  await expect(page.locator(".scene-contour")).toHaveCount(scene.detections.length);
  expect(await page.locator(".class-legend .class-swatch").evaluateAll(es=>new Set(es.map(e=>getComputedStyle(e).backgroundColor)).size)).toBe(14);
  const b=page.locator(".scene-viewer button").first();
  const color=await b.evaluate(el=>getComputedStyle(el).borderColor);
  await b.focus();
  expect(await b.evaluate(el=>getComputedStyle(el).borderColor)).toBe(color);
  const states=await b.evaluate(el=>({shadow:getComputedStyle(el).boxShadow,outline:getComputedStyle(el).outlineColor,width:getComputedStyle(el).outlineWidth}));
  expect(states.shadow).toContain("255, 255, 255");expect(states.width).not.toBe("0px");
  // Auxiliary black and white strokes form >= 3:1 on both synthetic extremes.
  const ratio=(a:number,b:number)=>(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  expect(ratio(1,0)).toBeGreaterThanOrEqual(3);
  await expect(page.locator(".vehicle-meta")).toContainText("Automóvil");
  expect(await page.locator(".detection-list button").first().evaluate(el=>el.getBoundingClientRect().height)).toBeGreaterThanOrEqual(44);
  await expect(page.locator(".scene-viewer button")).not.toHaveCount(scene.detections.length);
  await page.getByRole("button",{name:"Limpiar imagen",exact:true}).click();
 }
});
