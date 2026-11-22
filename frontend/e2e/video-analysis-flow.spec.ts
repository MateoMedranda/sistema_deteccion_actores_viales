import {test,expect} from "@playwright/test";
import path from "node:path";
import {connect} from "./helpers";
test("one action processes, enriches and keeps native playback available",async({page})=>{
 const posts:string[]=[];page.on("request",r=>{if(r.method()==="POST")posts.push(r.url());});
 await connect(page);await page.getByRole("tab",{name:"Video",exact:true}).click();
 await page.locator('input[type="file"][aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
 await page.getByRole("button",{name:"Procesar video",exact:true}).dblclick();
 await expect(page.getByText("Video disponible",{exact:true})).toBeVisible({timeout:20000});
 await expect(page.getByText("Enriquecimiento completado",{exact:true})).toBeVisible({timeout:20000});
 await expect(page.locator("video.result-video")).toBeVisible();
 await page.getByRole("tab",{name:"Imagen",exact:true}).click();await page.getByRole("tab",{name:"Video",exact:true}).click();
 expect(posts.filter(u=>u.endsWith("/api/v1/video-jobs"))).toHaveLength(1);
 expect(posts.filter(u=>u.endsWith("/api/v1/enrichment-jobs"))).toHaveLength(1);
 const before=posts.length;
 await page.locator("video.result-video").evaluate(async(v:HTMLVideoElement)=>{v.currentTime=Math.min(.2,v.duration||0);v.pause();});
 expect(posts).toHaveLength(before);
});
test("count uses processed video geometry and source replacement clears the line",async({page})=>{
 await connect(page);await page.getByRole("tab",{name:"Video",exact:true}).click();
 await page.locator('input[type="file"][aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
 await page.getByRole("button",{name:"Procesar video",exact:true}).click();
 await expect(page.locator("video.result-video")).toBeVisible({timeout:20000});
 await page.getByText("Conteo por línea",{exact:true}).click();
 const editor=page.locator(".line-editor");await editor.scrollIntoViewIfNeeded();const box=await editor.boundingBox();expect(box).not.toBeNull();
 await page.mouse.move(box!.x+box!.width*.2,box!.y+box!.height*.4);await page.mouse.down();await page.mouse.move(box!.x+box!.width*.8,box!.y+box!.height*.6);await page.mouse.up();
 await expect(page.locator(".line-handle")).toHaveCount(2);
 await page.locator('input[type="file"][aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
 await expect(page.locator(".line-handle")).toHaveCount(0);
});

for(const scenario of ["encoding","no-eligible","unavailable","lost-receipt","cancelled","expired"]){
 test("video recovery and independent phases: "+scenario,async({page})=>{
  await connect(page);
  let gets=0,enrichPosts=0;const intents:string[]=[];
  const until=()=>new Date(Date.now()+60000).toISOString();
  await page.route("**/web-api/api/v1/**",async route=>{
   const req=route.request(),u=new URL(req.url()),p=u.pathname;
   if(p.endsWith("/video-jobs")&&req.method()==="POST")return route.fulfill({status:202,json:{job_id:"controlled-video"}});
   if(p.endsWith("/video-jobs/controlled-video")&&req.method()==="GET"){
    gets++;const encoding=scenario==="encoding"&&gets<3;
    return route.fulfill({json:{job_id:"controlled-video",status:encoding?"processing":"completed",progress_percent:100,processed_frames:10,total_frames:10,expires_at:scenario==="expired"?new Date(Date.now()+500).toISOString():until(),processing_phase:encoding?"encoding":"ready",frame_total_confirmed:true,video_metadata:{width:640,height:360,fps:10,frame_count:10,duration_seconds:1,timebase:"processed-cfr"},eligible_track_count:scenario==="no-eligible"?0:1,classes_present:["car"]}});
   }
   if(p.endsWith("/enrichment-jobs")&&req.method()==="POST"){
    enrichPosts++;intents.push(req.headers()["x-ui-intent"]);
    if(scenario==="unavailable"&&enrichPosts===1)return route.fulfill({status:503,json:{code:"model_unavailable",message:"Unavailable"}});
    if(scenario==="lost-receipt"&&enrichPosts===1)return route.abort("failed");
    return route.fulfill({status:202,json:{enrichment_job_id:"controlled-enrichment",status:"queued",created_at:new Date().toISOString(),expires_at:until()}});
   }
   if(p.endsWith("/enrichment-jobs/controlled-enrichment")){
    if(req.method()==="DELETE")return route.fulfill({json:{status:"cancelled"}});
    return route.fulfill({json:{enrichment_job_id:"controlled-enrichment",status:scenario==="cancelled"?"cancelled":"completed",source:{kind:"video",source_id:"controlled-video"},created_at:new Date().toISOString(),expires_at:until(),progress_percent:100,processed_units:1,total_units:1,results_ready:0}});
   }
   if(p.endsWith("/results"))return route.fulfill({json:{items:[],page:1,page_size:25,total:0}});
   return route.fulfill({status:404,json:{code:"not_found",message:"Not found"}});
  });
  await page.getByRole("tab",{name:"Video",exact:true}).click();
  await page.locator('input[aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
  await page.getByRole("button",{name:"Procesar video",exact:true}).click();
  if(scenario==="encoding"){
   await expect(page.getByText("Preparando video",{exact:true})).toBeVisible();
   expect(await page.getByRole("progressbar",{name:"Cuadros procesados"}).getAttribute("aria-valuenow")).toBeNull();
   await expect(page.locator("video.result-video")).toBeVisible({timeout:15000});
  }else if(scenario==="no-eligible"){await expect(page.getByText("No aplicable",{exact:true})).toBeVisible();expect(enrichPosts).toBe(0);}
  else if(scenario==="unavailable"){
   await expect(page.getByText("Enriquecimiento fallido",{exact:true})).toBeVisible();
   await expect(page.locator("video.result-video")).toBeVisible();
   await page.getByRole("button",{name:"Reintentar enriquecimiento",exact:true}).click();await expect(page.getByText("Enriquecimiento completado",{exact:true})).toBeVisible();expect(intents[0]).not.toBe(intents[1]);
  }else if(scenario==="lost-receipt"){
   await expect(page.getByText("Conexión interrumpida",{exact:true})).toBeVisible();
   await page.getByRole("button",{name:"Reanudar consulta",exact:true}).click();await expect(page.getByText("Enriquecimiento completado",{exact:true})).toBeVisible();expect(intents[0]).toBe(intents[1]);
  }else if(scenario==="cancelled"){await expect(page.getByText("Cancelado",{exact:true})).toBeVisible();await expect(page.locator("video.result-video")).toBeVisible();}
  else{await page.getByRole("tab",{name:"Imagen",exact:true}).click();await page.waitForTimeout(750);await page.getByRole("tab",{name:"Video",exact:true}).click();await expect(page.locator("video.result-video")).toHaveCount(0);}
 });
}
