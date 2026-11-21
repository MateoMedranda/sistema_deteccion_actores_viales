import {test,expect} from "@playwright/test";
import {complete} from "./helpers";
import {mockScenario} from "./scenarios";
for(const scenario of ["preparing","failed","not_applicable"]){
 test("plate preview "+scenario+" keeps original evidence and selection",async({page},info)=>{
  await mockScenario(page,"completed");
  let release!:()=>void;const pending=new Promise<void>(r=>release=r);let attempts=0;
  await page.route(/plate-preview\?profile=/,async route=>{
   attempts++;if(scenario==="preparing")await pending;
   await route.fulfill({status:scenario==="failed"?503:422,json:{code:scenario==="failed"?"plate_preview_unavailable":"plate_not_applicable",message:"safe"}});
  });
  await complete(page);
  await expect(page.getByRole("img",{name:"Recorte de la placa",exact:true})).toBeVisible();
  await expect(page.locator(".preview-status")).toHaveText(scenario==="preparing"?"Preparando versión procesada…":scenario==="failed"?"No se pudo preparar la versión procesada. El original sigue disponible.":"El tratamiento no es aplicable a esta placa.");
  await expect(page.locator(".vehicle-details h3")).toHaveText("Detección 1");
  await page.screenshot({path:info.outputPath("preview-"+scenario+".png"),fullPage:true});
  if(scenario==="failed"){
   await page.getByRole("button",{name:"Reintentar versión procesada"}).click();
   await expect.poll(()=>attempts).toBe(2);
  }
  release();
 });
}
