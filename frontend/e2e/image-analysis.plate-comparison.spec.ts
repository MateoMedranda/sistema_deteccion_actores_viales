import {test,expect} from "@playwright/test";
import {connect} from "./helpers";
import {fixtureScenes,realScene,controls,inspectVehicle} from "./plate-real-api";
test("thirty authorized plate comparisons keep ROI, provenance, CORS and model counts",async({page},info)=>{
 test.setTimeout(90000);
 await connect(page);
 let comparisons=0,posts=0;const headers:any[]=[];
 page.on("request",r=>{if(r.method()==="POST"&&r.url().includes("/api/"))posts++;});
 page.on("response",async r=>{if(r.url().includes("plate-preview")&&r.status()===200)headers.push({url:r.url(),metadata:JSON.parse((await r.allHeaders())["x-plate-preview-metadata"])});});
 for(const scene of fixtureScenes.slice(0,3)){
  const source=await realScene(page,scene),before=(await controls(page)).models;
  const eligible=source.detections.filter((d:any)=>d.enrichment_eligible);
  // Actual localizer returns no bbox for ordinal % 4 == 3; include read/unreadable/failed.
  for(const detection of eligible.filter((d:any)=>(d.detection_id-1)%4!==3)){
   if(comparisons>=30)break;
   await inspectVehicle(page,detection.detection_id);
   const region=page.getByRole("region",{name:"Inspección de placa"});
   const original=page.getByRole("img",{name:"Recorte de la placa",exact:true});
   const pixels=await original.evaluate((img:HTMLImageElement)=>{
    const c=document.createElement("canvas");c.width=img.naturalWidth;c.height=img.naturalHeight;const x=c.getContext("2d")!;x.drawImage(img,0,0);
    return {width:c.width,height:c.height,pixel:[...x.getImageData(0,0,1,1).data]};
   });
   expect(pixels.width).toBeGreaterThanOrEqual(2);expect(pixels.height).toBeGreaterThanOrEqual(2);
   expect(pixels.pixel).toEqual([8,detection.detection_id-1,8,255]);
   const bbox=detection.bbox,w=bbox.x_max-bbox.x_min,h=bbox.y_max-bbox.y_min;
   await expect.poll(()=>headers.find(m=>m.metadata.source_id===source.request_id&&m.metadata.detection_id===detection.detection_id)?.metadata.original_bbox).toEqual({x_min:bbox.x_min+Math.floor(w/4),y_min:bbox.y_min+Math.floor(h*2/3),x_max:bbox.x_min+Math.floor(w*3/4),y_max:bbox.y_min+Math.floor(h*5/6)});
   await page.getByRole("button",{name:"Procesada",exact:true}).click();
   const processed=page.getByRole("img",{name:"Versión procesada de la placa",exact:true});
   await expect(processed).toBeVisible();await processed.evaluate((img:HTMLImageElement)=>img.decode());
   const size=await processed.evaluate((img:HTMLImageElement)=>({width:img.naturalWidth,height:img.naturalHeight}));
   expect(size.width/pixels.width).toBe(size.height/pixels.height);
   if(comparisons===0)await page.screenshot({path:info.outputPath("processed-plate.png"),fullPage:true});
   const callsBefore=await page.evaluate(()=>performance.getEntriesByType("resource").filter(e=>e.name.includes("plate-preview")).length);
   await page.getByRole("button",{name:"4x",exact:true}).click();await region.focus();await region.press("ArrowRight");
   await page.getByRole("button",{name:"Original",exact:true}).click();
   expect(await page.evaluate(()=>performance.getEntriesByType("resource").filter(e=>e.name.includes("plate-preview")).length)).toBe(callsBefore);
   expect(await controls(page)).toMatchObject({models:before});
   comparisons++;
  }
  await page.addStyleTag({content:"html{font-size:200% !important}"});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath(scene.name+"-plate.png"),fullPage:true});
  await page.addStyleTag({content:"html{font-size:100% !important}"});
  await page.getByRole("button",{name:"Limpiar imagen",exact:true}).click();
 }
 expect(comparisons).toBe(30);expect(posts).toBe(6);
 expect(headers.length).toBeGreaterThanOrEqual(30);
 expect(headers.every(h=>h.metadata.profile_id==="display-contrast-v1")).toBe(true);
 await info.attach("plate-comparisons",{body:JSON.stringify({comparisons,posts,metadata:headers.map(h=>h.metadata)}),contentType:"application/json"});
});
