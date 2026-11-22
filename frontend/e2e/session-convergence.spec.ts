import {test,expect} from "@playwright/test";
import path from "node:path";
import {connect} from "./helpers";
const expires=()=>new Date(Date.now()+300000).toISOString();
const processing=()=>({job_id:"active-job",status:"processing",processed_frames:1,total_frames:20,progress_percent:5,expires_at:expires()});
test("reset aborts an upload before its job ID exists and ignores its late receipt",async({page})=>{
 let release!:()=>void,arrived!:()=>void,aborted=false;
 const gate=new Promise<void>(r=>release=r),started=new Promise<void>(r=>arrived=r);
 page.on("requestfailed",r=>{if(r.method()==="POST"&&r.url().endsWith("/video-jobs"))aborted=true;});
 await page.route("**/api/v1/video-jobs",async route=>{arrived();await gate;await route.fulfill({status:202,json:{job_id:"late",status:"queued",expires_at:expires()}}).catch(()=>{});});
 await connect(page);await page.getByRole("tab",{name:"Video",exact:true}).click();await page.locator('input[aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));await page.getByRole("button",{name:"Procesar video",exact:true}).click();await started;
 await page.getByRole("button",{name:"Reiniciar sesión"}).click();await expect.poll(()=>aborted).toBe(true);await expect(page.locator(".line-editor")).toHaveCount(0);release();await expect(page.getByText("late",{exact:true})).toHaveCount(0);
});
for(const status of [401,403])test("managed access rejection "+status+" withdraws both workspaces",async({page})=>{
 await connect(page);await page.route("**/api/v1/video-jobs",route=>route.fulfill({status,json:{code:"access_rejected",message:"Denied"}}));
 await page.getByRole("tab",{name:"Video",exact:true}).click();await page.locator('input[aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));await page.getByRole("button",{name:"Procesar video",exact:true}).click();
 await expect(page.locator("main")).toHaveAttribute("data-session-state","access_rejected");await expect(page.locator("video")).toHaveCount(0);await expect(page.getByLabel("API key",{exact:true})).toHaveCount(0);
});
test("failed remote cancellation still clears the session immediately",async({page})=>{
 let cancelled=false;
 await page.route("**/api/v1/video-jobs",r=>r.fulfill({status:202,json:{job_id:"active-job",status:"queued",expires_at:expires()}}));
 await page.route("**/api/v1/video-jobs/active-job",r=>{if(r.request().method()==="DELETE"){cancelled=true;return r.fulfill({status:503,json:{code:"unavailable"}});}return r.fulfill({json:processing()});});
 await connect(page);await page.getByRole("tab",{name:"Video",exact:true}).click();await page.locator('input[aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));await page.getByRole("button",{name:"Procesar video",exact:true}).click();await expect(page.getByRole("button",{name:"Cancelar procesamiento"})).toBeVisible();
 await page.getByRole("button",{name:"Reiniciar sesión"}).click();await expect(page.locator(".line-editor")).toHaveCount(0);await expect.poll(()=>cancelled).toBe(true);
});
test("native media rejection is checked by authorized GET and withdraws evidence",async({page})=>{
 let gets=0;
 await page.route("**/api/v1/video-jobs",r=>r.fulfill({status:202,json:{job_id:"active-job",status:"queued",expires_at:expires()}}));
 await page.route("**/api/v1/video-jobs/active-job",r=>{gets++;return gets>1?r.fulfill({status:401,json:{code:"invalid_api_key",message:"Denied"}}):r.fulfill({json:{...processing(),status:"completed",progress_percent:100}});});
 await page.route("**/api/v1/video-jobs/active-job/annotated-video/content",r=>r.fulfill({status:401,json:{code:"invalid_api_key",message:"Denied"}}));
 await connect(page);await page.getByRole("tab",{name:"Video",exact:true}).click();await page.locator('input[aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));await page.getByRole("button",{name:"Procesar video",exact:true}).click();
 await expect(page.locator("main")).toHaveAttribute("data-session-state","access_rejected");await expect(page.locator("video")).toHaveCount(0);
});
