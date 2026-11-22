import {test,expect} from "@playwright/test";
import path from "node:path";
import {connect} from "./helpers";
import {vehicleResult,expiresAt} from "../tests/fixtures/imageAnalysis";
test("three pages expose real track IDs and evidence without another inference",async({page},info)=>{
 await connect(page);let mutations=0,crops=0;
 page.on("request",r=>{if(r.method()==="POST")mutations++;if(r.url().includes("plate-preview"))crops++;});
 await page.route("**/web-api/api/v1/**",async route=>{
  const req=route.request(),u=new URL(req.url()),p=u.pathname;
  if(p.endsWith("/video-jobs")&&req.method()==="POST")return route.fulfill({json:{job_id:"video-tracks",status:"queued"}});
  if(p.endsWith("/video-jobs/video-tracks"))return route.fulfill({json:{job_id:"video-tracks",status:"completed",progress_percent:100,processed_frames:90,total_frames:90,expires_at:expiresAt(),processing_phase:"ready",frame_total_confirmed:true,video_metadata:{width:640,height:360,fps:30,frame_count:90,duration_seconds:3,timebase:"processed-cfr"},eligible_track_count:61,classes_present:["car"]}});
  if(p.endsWith("/enrichment-jobs")&&req.method()==="POST")return route.fulfill({json:{enrichment_job_id:"tracks",status:"queued",created_at:new Date().toISOString(),expires_at:expiresAt()}});
  if(p.endsWith("/results")){
   const n=Number(u.searchParams.get("page")),items=Array.from({length:n===3?11:25},(_,i)=>{const id=(n-1)*25+i+1;return {...vehicleResult(id),track_id:id*10,evidence_frame_indexes:[30],plate:{...vehicleResult(id).plate,evidence_frame_indexes:[60]}};});
   return route.fulfill({json:{items,page:n,page_size:25,total:61}});
  }
  if(p.endsWith("/processed-video"))return route.fulfill({contentType:"video/mp4",body:await import("node:fs").then(fs=>fs.readFileSync(path.resolve("e2e/fixtures/controlled.mp4")))});
  return route.fulfill({json:{enrichment_job_id:"tracks",status:"completed",source:{kind:"video",source_id:"video-tracks"},created_at:new Date().toISOString(),expires_at:expiresAt(),progress_percent:100,processed_units:61,total_units:61,results_ready:61}});
 });
 await page.getByRole("tab",{name:"Video",exact:true}).click();await page.locator('input[aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));await page.getByRole("button",{name:"Procesar video",exact:true}).click();
 await expect(page.getByText("Página 1 de 3")).toBeVisible();const before=mutations;
 await page.getByRole("button",{name:/Trayectoria 10\b/}).click();await expect(page.getByRole("heading",{name:"Trayectoria 10",exact:true})).toBeVisible();await expect(page.getByText("Cuadro 60 · 2.00 s del video procesado")).toBeVisible();
 await page.getByRole("button",{name:"Siguiente",exact:true}).click();await expect(page.getByText("Página 2 de 3")).toBeVisible();await expect(page.getByRole("heading",{name:"Trayectoria 10",exact:true})).toHaveCount(0);
 await page.getByRole("button",{name:"Siguiente",exact:true}).click();await expect(page.getByText("Página 3 de 3")).toBeVisible();await page.getByRole("button",{name:/Trayectoria 610\b/}).click();await expect(page.getByRole("heading",{name:"Trayectoria 610",exact:true})).toBeVisible();
 await page.getByRole("button",{name:"Anterior",exact:true}).click();await expect(page.getByText("Página 2 de 3")).toBeVisible();
 expect(mutations).toBe(before);expect(crops).toBe(0);
 await page.evaluate(()=>{document.documentElement.style.fontSize="200%";});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:info.outputPath("tracks-200-text.png"),fullPage:true});
});
