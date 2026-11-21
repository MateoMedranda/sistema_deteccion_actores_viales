import {test,expect,type Locator} from "@playwright/test";
import {connect} from "./helpers";
import {annotationScenes,serveAnnotation,annotationFile} from "./annotation-scenarios";
import {classPresentation} from "../src/features/image-analysis/classPresentation";
const rgb=(hex:string)=>"rgb("+[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16)).join(", ")+")";
const luminance=(color:string)=>color.match(/[\d.]+/g)!.slice(0,3).map(Number).map(n=>n/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
const contrast=(a:string,b:string)=>{const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);};
async function styles(control:Locator){
 return control.evaluate(el=>{const s=getComputedStyle(el);return {color:s.borderColor,style:s.borderStyle,width:s.borderTopWidth,outline:s.outlineColor,outlineWidth:s.outlineWidth,shadow:s.boxShadow,background:s.backgroundColor};});
}
async function textContrast(control:Locator){
 return control.evaluate(el=>{
  const foreground=getComputedStyle(el).color;let node:Element|null=el,background="";
  while(node){background=getComputedStyle(node).backgroundColor;if(background!=="rgba(0, 0, 0, 0)"&&background!=="transparent")break;node=node.parentElement;}
  return {foreground,background:background||"rgb(255, 255, 255)"};
 });
}
test("full class matrix preserves tokens, contextual states and actual contrast",async({page},info)=>{
 test.setTimeout(120000);await connect(page);const measurements:any[]=[];
 for(const scene of annotationScenes.slice(0,2)){
  const calls=await serveAnnotation(page,scene);
  await page.getByLabel("Seleccionar imagen",{exact:true}).setInputFiles(annotationFile(scene));
  await page.getByRole("button",{name:"Analizar imagen"}).click();
  await expect(page.locator(".analysis-status strong")).toHaveText(/Análisis completo|Resultado parcial/);
  await expect(page.locator(".preview-status")).toHaveText("El tratamiento no es aplicable a esta placa.");
  const background=scene.name==="scene-0"?"rgb(0, 0, 0)":"rgb(255, 255, 255)";
  await page.locator(".scene-viewer").evaluate((el,bg)=>(el as HTMLElement).style.background=bg,background);
  await page.locator(".scene-viewer img").evaluate(el=>(el as HTMLElement).style.opacity="0");
  await expect(page.locator(".class-legend li")).toHaveCount(14);
  for(const font of [100,200]){
   await page.addStyleTag({content:"html{font-size:"+font+"% !important}"});
   for(const d of scene.detections.slice(0,14)){
    const p=classPresentation(d.class_name),expected=rgb(p.color);
    const legend=page.locator(".class-legend li").filter({hasText:p.label});
    expect(await legend.locator(".class-swatch").evaluate(el=>getComputedStyle(el).backgroundColor)).toBe(expected);
    const contour=page.locator(".scene-contour").nth(scene.detections.indexOf(d));
    expect((await styles(contour)).color).toBe(expected);
    const text=await textContrast(legend);expect(contrast(text.foreground,text.background)).toBeGreaterThanOrEqual(4.5);
    if(!d.enrichment_eligible){
     expect(await contour.evaluate(el=>el.tagName)).toBe("DIV");
     await expect(page.locator(".detection-list .chip-id").filter({hasText:new RegExp("^#"+d.detection_id+"$")})).toHaveCount(0);
     continue;
    }
    await page.getByRole("button",{name:"Cerrar ficha del vehículo"}).click();
    await page.mouse.move(0,0);
    const list=page.locator(".detection-list button").filter({has:page.locator(".chip-id",{hasText:new RegExp("^#"+d.detection_id+"$")})});
    const normal=await styles(contour);expect(normal.style).toBe("solid");
    const outlineColors=[normal.color,...(normal.shadow.match(/rgb\([^)]+\)/g)??[])];
    expect(Math.max(...outlineColors.map(c=>contrast(c,background)))).toBeGreaterThanOrEqual(3);
    expect(await list.evaluate(el=>getComputedStyle(el).borderLeftColor)).toBe(expected);
    const rect=await list.boundingBox();expect(rect!.height).toBeGreaterThanOrEqual(44);expect(rect!.width).toBeGreaterThanOrEqual(44);
    await list.focus();await expect(contour).toHaveAttribute("data-context","focus");
    await expect(list).toBeFocused();await expect(page.locator(".vehicle-details")).toContainText("Explora cada vehículo");
    const focused=await styles(contour);
    expect(focused.color).toBe(expected);expect(parseFloat(focused.outlineWidth)).toBeGreaterThan(0);
    expect(Math.max(...[focused.outline,...(focused.shadow.match(/rgb\([^)]+\)/g)??[])].map(c=>contrast(c,background)))).toBeGreaterThanOrEqual(3);
    // Hover a different scene control while focus stays in the list.
    const alternate=page.locator(".scene-viewer button").nth(d.detection_id===scene.detections[0].detection_id?1:0);
    await alternate.hover();await expect(contour).toHaveAttribute("data-context","focus");
    await list.evaluate(el=>(el as HTMLElement).blur());
    await expect(alternate).toHaveAttribute("data-context","hover");
    await list.hover();await expect(contour).toHaveAttribute("data-context","hover");
    const hovered=await styles(contour);expect(hovered.style).toBe("dashed");expect(hovered.color).toBe(expected);
    expect(calls.posts).toBe(2);await expect(list).toHaveAttribute("aria-pressed","false");
    await list.press("Enter");
    await expect(page.locator(".details-heading h3")).toHaveText("Detección "+d.detection_id);
    await expect(contour).toHaveAttribute("aria-pressed","true");
    expect((await styles(contour)).style).toBe("double");
    expect(await page.locator(".vehicle-meta .class-swatch").evaluate(el=>getComputedStyle(el).backgroundColor)).toBe(expected);
    await expect(page.locator(".vehicle-meta")).toContainText(p.label);
    const localized=scene.results.find((r:any)=>r.detection_id===d.detection_id).plate.status!=="not_detected";
    await expect(page.locator(".preview-status")).toHaveText(localized?"El tratamiento no es aplicable a esta placa.":"Sin versión procesada: se requiere una placa localizada y un original disponible.");
    expect(await page.locator(".context-id").evaluate(el=>getComputedStyle(el).whiteSpace)).toBe("nowrap");
    measurements.push({class:p.key,background,font,normal,focused,hovered,text});
   }
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  expect(calls.annotations).toBe(0);expect(calls.posts).toBe(2);
  await page.screenshot({path:info.outputPath(scene.name+"-class-matrix.png"),fullPage:true});
  await page.addStyleTag({content:"html{font-size:100% !important}"});
  await page.getByRole("button",{name:"Limpiar imagen",exact:true}).click();
 }
 await info.attach("class-matrix",{body:JSON.stringify({viewport:info.project.name,measurements}),contentType:"application/json"});
});
