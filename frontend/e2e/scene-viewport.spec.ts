import {test,expect} from "@playwright/test";
import {readFileSync,writeFileSync} from "node:fs";
import path from "node:path";
import {connect,scene} from "./helpers";
import {detectionResponse,expiresAt,vehicleResult} from "../tests/fixtures/imageAnalysis";
const root=path.resolve("e2e/fixtures/video-presentation"),manifest=JSON.parse(readFileSync(path.join(root,"manifest.json"),"utf8"));
test("ten scenes keep contours aligned at every zoom with bounded local interaction",async({page},info)=>{
 await connect(page);let current:any=manifest.images[0],posts=0,previews=0;
 page.on("request",r=>{if(r.method()==="POST")posts++;if(r.url().includes("plate-preview"))previews++;});
 await page.route("**/web-api/api/v1/**",async route=>{
  const req=route.request(),u=new URL(req.url()),p=u.pathname;
  if(p.endsWith("/images")){
   const source=detectionResponse();source.request_id="scene-"+current.file.replace(".png","");
   source.image={width:current.width,height:current.height,media_type:"image/png"};
   source.detections=current.boxes.map((b:any,i:number)=>({detection_id:b.id,class_id:0,class_name:"car",confidence:.9,enrichment_eligible:true,bbox:{x_min:b.bbox[0],y_min:b.bbox[1],x_max:b.bbox[2],y_max:b.bbox[3]}}));
   source.original_image.url="/api/v1/detections/"+source.request_id+"/original-image";source.annotated_image.url="/api/v1/detections/"+source.request_id+"/annotated-image";
   return route.fulfill({json:source});
  }
  if(p.endsWith("plate-preview"))return route.fulfill({status:422,json:{code:"plate_not_applicable",message:"Not applicable"}});
  if(p.endsWith("original-image"))return route.fulfill({contentType:"image/png",body:readFileSync(path.join(root,current.file))});
  if(req.method()==="POST")return route.fulfill({json:{enrichment_job_id:"scene-job",status:"queued",created_at:new Date().toISOString(),expires_at:expiresAt()}});
  if(p.endsWith("/results"))return route.fulfill({json:{page:1,page_size:50,total:current.boxes.length,items:current.boxes.map((b:any)=>vehicleResult(b.id))}});
  return route.fulfill({json:{enrichment_job_id:"scene-job",status:"completed",source:{kind:"image",source_id:"scene-"+current.file.replace(".png","")},created_at:new Date().toISOString(),expires_at:expiresAt(),progress_percent:100,processed_units:current.boxes.length,total_units:current.boxes.length,results_ready:current.boxes.length}});
 });
 const times:number[]=[],errors:number[]=[];
 for(const image of manifest.images){
  current=image;await page.locator('input[aria-label="Seleccionar imagen"]').setInputFiles(scene);
  await page.getByRole("button",{name:"Analizar imagen",exact:true}).click();
  const stage=page.getByTestId("scene-stage");await expect(stage).toBeVisible();await expect(stage.locator(".scene-contour")).toHaveCount(image.boxes.length);
  await expect(page.locator(".analysis-status strong")).toHaveText(/Análisis completo|Resultado parcial/);
  await expect(stage.locator("img")).toHaveJSProperty("naturalWidth",image.width);
  await page.locator(".detection-list button").last().click();
  await expect(page.locator(".vehicle-details h3")).toHaveText("Detección "+image.boxes.at(-1).id);
  await expect(page.locator(".preview-status")).toHaveText("El tratamiento no es aplicable a esta placa.");
  const before=posts,previewBefore=previews;
  for(const zoom of ["Ajustar","100%","200%","400%"]){
   const start=await page.evaluate(()=>performance.now());
   await page.getByRole("button",{name:zoom,exact:true}).click();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   times.push(await page.evaluate(()=>performance.now())-start);
   const measured=await stage.evaluate((element,args:any)=>{
    const stage=element.getBoundingClientRect(),image=element.querySelector("img")!.getBoundingClientRect(),boxes=[...element.querySelectorAll(".scene-contour")];
    let max=Math.max(Math.abs(stage.width-image.width),Math.abs(stage.height-image.height));
    for(let i=0;i<50;i++){const b=args.boxes[i%args.boxes.length].bbox,box=boxes[i%boxes.length].getBoundingClientRect(),tx=(i%7)/6,ty=(i%5)/4;
     const x=stage.left+(b[0]+(b[2]-b[0])*tx)/args.width*stage.width,y=stage.top+(b[1]+(b[3]-b[1])*ty)/args.height*stage.height;
     max=Math.max(max,Math.abs(box.left+box.width*tx-x),Math.abs(box.top+box.height*ty-y));}
    return max;
   },image);
   errors.push(measured);expect(measured).toBeLessThanOrEqual(1);
  }
  expect(posts).toBe(before);expect(previews).toBe(previewBefore);await expect(page.locator(".vehicle-details h3")).toHaveText("Detección "+image.boxes.at(-1).id);
 }
 const sorted=[...times].sort((a,b)=>a-b),p95=sorted[Math.ceil(sorted.length*.95)-1];
 writeFileSync(info.outputPath("zoom-metrics.json"),JSON.stringify({viewport:info.project.name,scenes:10,denseScenes:3,pointsPerScenePerScale:50,operations:times.length,maxError:Math.max(...errors),p95ms:p95}));
 expect(times.length).toBeGreaterThanOrEqual(30);expect(p95).toBeLessThanOrEqual(200);
 await page.getByRole("button",{name:"Ajustar",exact:true}).click();
 await page.evaluate(()=>{document.documentElement.style.fontSize="200%";});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:info.outputPath("zoom-200-text.png"),fullPage:true});
 await info.attach("zoom-metrics",{body:JSON.stringify({viewport:info.project.name,scenes:10,denseScenes:3,pointsPerScenePerScale:50,operations:times.length,maxError:Math.max(...errors),p95ms:p95}),contentType:"application/json"});
});
