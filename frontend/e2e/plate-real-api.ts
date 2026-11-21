import {expect,type Page} from "@playwright/test";
import {annotationFile,annotationScenes} from "./annotation-scenarios";
export const fixtureScenes=annotationScenes;
export async function realScene(page:Page,scene:any){
 const detected=page.waitForResponse(r=>r.url().endsWith("/api/v1/detections/images")&&r.request().method()==="POST");
 await page.getByLabel("Seleccionar imagen",{exact:true}).setInputFiles(annotationFile(scene));
 await page.getByRole("button",{name:"Analizar imagen"}).click();
 const source=await (await detected).json();
 await expect(page.locator(".analysis-status strong")).toHaveText(/Análisis completo|Resultado parcial/);
 await expect(page.locator(".scene-viewer img")).toBeVisible();
 return source;
}
export async function controls(page:Page,clear=false){
 return page.evaluate(async clear=>{
 const r=await fetch("http://127.0.0.1:8767/test-only/preview-control",{method:clear?"DELETE":"GET",headers:{"X-API-Key":"ui-synthetic-key"}});
 if(!r.ok)throw new Error("test control unavailable");return r.json();
 },clear);
}
export async function inspectVehicle(page:Page,id:number){
 await page.locator(".detection-list button").filter({hasText:"Detección "+id}).filter({has:page.locator(".chip-id",{hasText:new RegExp("^#"+id+"$")})}).click();
 await expect(page.locator(".preview-status")).toHaveText("Versión procesada disponible");
 await expect(page.getByRole("img",{name:"Recorte de la placa",exact:true})).toBeVisible();
}
