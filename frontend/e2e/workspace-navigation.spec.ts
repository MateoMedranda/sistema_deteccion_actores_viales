import {test,expect} from "@playwright/test";
import {connect} from "./helpers";
test("modes remain mounted, have keyboard navigation and do not start work",async({page})=>{
 const mutations:string[]=[];page.on("request",r=>{if(["POST","DELETE"].includes(r.method()))mutations.push(r.url());});
 await connect(page);
 await page.evaluate(()=>document.documentElement.style.fontSize="200%");
 await expect(page.getByRole("tab",{name:"Imagen"})).toHaveAttribute("aria-selected","true");
 await page.getByRole("tab",{name:"Imagen"}).focus();await page.keyboard.press("ArrowRight");await page.keyboard.press("Enter");
 await expect(page.getByRole("tab",{name:"Video"})).toHaveAttribute("aria-selected","true");
 await expect(page.locator("#panel-image")).toHaveCount(1);await expect(page.locator("#panel-image")).toBeHidden();
 await page.getByRole("tab",{name:"Imagen"}).click();
 expect(mutations.filter(url=>url.includes("/video-jobs")||url.includes("/enrichment-jobs"))).toHaveLength(0);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});
