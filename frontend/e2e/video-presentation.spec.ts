import {test,expect} from "@playwright/test";
import path from "node:path";
import {connect} from "./helpers";
test("processed video has confirmed metadata and external class legend",async({page})=>{
 await connect(page);await page.getByRole("tab",{name:"Video",exact:true}).click();
 await page.locator('input[type="file"][aria-label="Video"]').setInputFiles(path.resolve("e2e/fixtures/controlled.mp4"));
 await page.getByRole("button",{name:"Procesar video",exact:true}).click();
 await expect(page.locator("video.result-video")).toBeVisible({timeout:20000});
 await expect(page.getByText("Video disponible",{exact:true})).toBeVisible();
 await expect(page.getByText("Clases detectadas",{exact:true})).toBeVisible();
 const aligned=await page.locator("video.result-video").evaluate((element:HTMLVideoElement)=>element.videoWidth>0&&element.videoHeight>0);
 expect(aligned).toBeTruthy();
});
