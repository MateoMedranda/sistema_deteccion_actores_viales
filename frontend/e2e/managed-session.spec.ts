import {test,expect} from "@playwright/test";
import {complete,connect} from "./helpers";
test("server configured image flow and reset keep secrets out of browser",async({page})=>{
 const requests:Array<{url:string;headers:Record<string,string>}>=[];
 page.on("request",r=>requests.push({url:r.url(),headers:r.headers()}));
 await complete(page);
 await expect(page.getByLabel("API key",{exact:true})).toHaveCount(0);
 await expect(page.getByRole("tab",{name:"Video"})).toBeVisible();
 expect(requests.every(r=>!r.headers["x-api-key"]&&!r.url.includes("ui-synthetic-key"))).toBeTruthy();
 await page.getByRole("button",{name:"Reiniciar sesión"}).click();
 await expect(page.getByText("Servicio conectado")).toBeVisible();
 await expect(page.getByRole("img",{name:"Recorte del vehículo",exact:true})).toHaveCount(0);
});
test("bootstrap rejection recovers automatically without a manual retry control",async({page})=>{
 let attempts=0;
 await page.route("**/web/session",r=>{if(r.request().method()==="POST"&&++attempts===1)return r.fulfill({status:401,contentType:"application/json",body:JSON.stringify({status:"access_rejected",code:"web_access_rejected",message:"Access rejected"})});return r.continue();});
 await page.goto("/");await expect(page.getByRole("button",{name:"Reintentar conexión"})).toHaveCount(0);
 await expect(page.locator("main")).toHaveAttribute("data-session-state","ready",{timeout:10000});
 expect(attempts).toBe(2);await expect(page.locator(".connection-status")).toHaveCount(0);
});
