import {test,expect} from "@playwright/test";
import {connect} from "./helpers";
import {fixtureScenes,realScene,controls,inspectVehicle} from "./plate-real-api";
test("thirty cold and thirty warm full preview operations meet the measured budget",async({page},info)=>{
 test.setTimeout(90000);await connect(page);
 const cold:number[]=[],warm:number[]=[];
 for(const scene of fixtureScenes.slice(0,3)){
  const source=await realScene(page,scene);
  await expect(page.locator(".preview-status")).toHaveText("Versión procesada disponible");
  const eligible=source.detections.filter((d:any)=>d.enrichment_eligible&&(d.detection_id-1)%4!==3);
  for(const d of eligible){
   if(cold.length>=30)break;
   const button=page.locator(".detection-list button").filter({has:page.locator(".chip-id",{hasText:new RegExp("^#"+d.detection_id+"$")})});
   await page.getByRole("button",{name:"Cerrar ficha del vehículo"}).click();
   await controls(page,true);
   const measure=async()=>{
    const start=await page.evaluate(()=>performance.now());
    await button.click();
    await expect(page.locator(".preview-status")).toHaveText("Versión procesada disponible");
    await page.getByRole("button",{name:"Procesada",exact:true}).click();
    await page.getByRole("img",{name:"Versión procesada de la placa"}).evaluate((img:HTMLImageElement)=>img.decode());
    return (await page.evaluate(()=>performance.now()))-start;
   };
   cold.push(await measure());
   await page.getByRole("button",{name:"Cerrar ficha del vehículo"}).click();
   warm.push(await measure());
  }
  await page.getByRole("button",{name:"Limpiar imagen",exact:true}).click();
 }
 const percentile=(v:number[])=>[...v].sort((a,b)=>a-b)[Math.ceil(.95*v.length)-1];
 expect(cold).toHaveLength(30);expect(warm).toHaveLength(30);
 expect(percentile(cold)).toBeLessThanOrEqual(2000);expect(Math.max(...cold,...warm)).toBeLessThanOrEqual(10000);
 await info.attach("preview-latency",{body:JSON.stringify({viewport:info.project.name,samples:30,cold_ms:cold,warm_ms:warm,cold_p95_ms:percentile(cold),warm_p95_ms:percentile(warm),scope:"synthetic authorized plates, real API, headers/body/decode/render, local machine"}),contentType:"application/json"});
});
