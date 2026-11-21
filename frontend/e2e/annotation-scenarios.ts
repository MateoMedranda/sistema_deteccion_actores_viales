import { readFileSync } from "node:fs";
import path from "node:path";
import type { Page } from "@playwright/test";
import { detectionResponse, expiresAt } from "../tests/fixtures/imageAnalysis";
export const annotationScenes=JSON.parse(readFileSync(path.resolve("e2e/fixtures/annotations/manifest.json"),"utf8"));
export async function serveAnnotation(page:Page, scene:any){
 const original=readFileSync(path.resolve("e2e/fixtures/annotations/"+scene.name+".png"));
 const annotated=readFileSync(path.resolve("e2e/fixtures/annotations/"+scene.name+"-annotated.png"));
 const calls={annotations:0,posts:0};
 const accepted={enrichment_job_id:"synthetic-job",status:"queued",created_at:new Date().toISOString(),expires_at:expiresAt()};
 await page.route("http://127.0.0.1:8767/api/**",async route=>{
  const req=route.request(),u=new URL(req.url());
  if(u.pathname.endsWith("/image-policy"))return route.continue();
  if(u.pathname.endsWith("/images")){calls.posts++;return route.fulfill({json:{...detectionResponse(),image:{width:scene.width,height:scene.height,media_type:"image/png"},detections:scene.detections}});}
  if(u.pathname.endsWith("annotated-image")){calls.annotations++;return route.fulfill({contentType:"image/png",body:annotated});}
  if(u.pathname.endsWith("original-image"))return route.fulfill({contentType:"image/png",body:original});
  if(u.pathname.endsWith("plate-preview"))return route.fulfill({status:422,json:{code:"plate_not_applicable",message:"Not applicable"}});
  if(req.method()==="POST"){calls.posts++;return route.fulfill({status:202,json:accepted});}
  if(req.method()==="DELETE")return route.fulfill({json:{status:"cancelled"}});
  if(u.pathname.endsWith("/results"))return route.fulfill({json:{items:scene.results,page:1,page_size:50,total:scene.results.length}});
  return route.fulfill({json:{...accepted,status:"completed",source:{kind:"image",source_id:detectionResponse().request_id},progress_percent:100,processed_units:scene.results.length,total_units:scene.results.length,results_ready:scene.results.length}});
 });
 return calls;
}
export const annotationFile=(scene:any)=>path.resolve("e2e/fixtures/annotations/"+scene.name+".png");
