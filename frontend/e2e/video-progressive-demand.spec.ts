import {test,expect} from "@playwright/test";
import path from "node:path";
test("enriches only the selected vehicle and counts crossings at the playback time",async({page,request},info)=>{
 await request.post("http://127.0.0.1:9415/test-only/reset?scenario=count");
 const uploads:string[]=[];page.on("request",r=>{if(r.method()==="POST"&&r.url().includes("video-jobs?"))uploads.push(r.url())});
 await page.goto("/");await expect(page.locator("main")).toHaveAttribute("data-session-state","ready");await page.getByRole("tab",{name:"Video",exact:true}).click();
 await page.locator('input[type="file"][aria-label="Video"]').setInputFiles(path.resolve("../.runtime/e2e-009/source.mp4"));await page.getByRole("button",{name:"Procesar video",exact:true}).click();
 const surface=page.locator(".progressive-surface canvas");await expect(surface).toBeVisible({timeout:20000});
 if(!(await page.evaluate(()=>typeof VideoDecoder==="function"))){await expect(page.getByText(/La reproducción progresiva no es compatible/)).toBeVisible();return}
 await expect.poll(()=>surface.getAttribute("data-frame-index")).not.toBeNull();await page.getByRole("button",{name:"Pausar e inspeccionar",exact:true}).click();
 expect((await(await request.get("http://127.0.0.1:9415/test-only/calls")).json()).enrichment_calls).toBe(0);
 await expect(page.getByRole("progressbar",{name:"Vehículos con resultado final"})).toHaveCount(0);
 await page.getByRole("button",{name:/^Consultar vehículo 1,/}).click();
 await expect(page.getByRole("heading",{name:"Vehículo #1",exact:true})).toBeVisible();await expect(page.getByText("SYN123",{exact:true})).toBeVisible();await expect(page.getByRole("img",{name:"Recorte del vehículo",exact:true})).toBeVisible();
 const calls=(await(await request.get("http://127.0.0.1:9415/test-only/calls")).json()).enrichment_calls;expect(calls).toBeGreaterThan(0);expect(calls).toBeLessThanOrEqual(3);
 await page.getByRole("button",{name:/^Consultar vehículo 1,/}).click();await page.waitForTimeout(600);expect((await(await request.get("http://127.0.0.1:9415/test-only/calls")).json()).enrichment_calls).toBe(calls);
 const slider=page.getByRole("slider",{name:/Posición del video/});await slider.focus();await page.keyboard.press("Home");await expect.poll(()=>surface.getAttribute("data-frame-index")).toBe("0");
 await expect(page.getByText(/Fotograma de 0:00/)).toBeVisible();
 const editor=page.locator(".count-frame-editor");await expect(editor).toBeVisible();await editor.scrollIntoViewIfNeeded();const box=(await editor.boundingBox())!;
 if(info.project.use.hasTouch){await editor.tap({position:{x:box.width*.1,y:box.height*.3}});await editor.tap({position:{x:box.width*.9,y:box.height*.3}})}else{await editor.click({position:{x:box.width*.1,y:box.height*.3}});await editor.click({position:{x:box.width*.9,y:box.height*.3}})}
 if(!info.project.use.hasTouch){
  const r=(await editor.boundingBox())!;
  await page.mouse.move(r.x+r.width*.5,r.y+r.height*.3);await page.mouse.down();await page.mouse.move(r.x+r.width*.5,r.y+r.height*.34,{steps:12});await page.mouse.up();
  const top=await page.getByRole("button",{name:"Extremo 1",exact:true}).evaluate(e=>parseFloat((e as HTMLElement).style.top));expect(top).toBeCloseTo(34,0);
 }
 await page.locator(".count-advanced summary").click();
 await page.getByRole("slider",{name:"Punto A vertical",exact:true}).focus();await page.keyboard.press("ArrowRight");await page.keyboard.press("ArrowLeft");
 await page.getByRole("button",{name:"Activar conteo",exact:true}).click();const counter=page.getByLabel("Contador de cruces");await expect(counter.locator("strong")).toHaveText("0");
 await slider.focus();await page.keyboard.press("End");await expect.poll(()=>surface.getAttribute("data-frame-index")).toBe("179");await expect(counter.locator("strong")).toHaveText("5");
 await slider.focus();await page.keyboard.press("Home");await expect(counter.locator("strong")).toHaveText("0");await slider.focus();await page.keyboard.press("End");await expect(counter.locator("strong")).toHaveText("5");
 expect(uploads).toHaveLength(1);expect(uploads[0]).toContain("enrichment=on-demand");
 await page.screenshot({path:info.outputPath("selective-count-desktop.png"),fullPage:true});
 await page.getByRole("button",{name:"Desactivar conteo",exact:true}).click();await expect(counter).toHaveCount(0);
 await page.evaluate(()=>document.documentElement.style.fontSize="200%");expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
 await page.screenshot({path:info.outputPath("selective-inspection-count.png"),fullPage:true});
 await page.getByRole("button",{name:"Limpiar video",exact:true}).click();await expect(surface).toHaveCount(0);
});
test.afterEach(async({page,request})=>{const clear=page.getByRole("button",{name:"Limpiar video",exact:true});if(await clear.count())await clear.click({timeout:3000}).catch(()=>{});await request.post("http://127.0.0.1:9415/test-only/release")});
