import {test,expect} from '@playwright/test';import fs from 'node:fs';import {open,stop,headers} from './multilineHelpers';
test('ten named lines persist; cards remain outside the image and recover on reload',async({page,request},info)=>{
 const {path,generation}=await open(page,request,10);const before=await(await request.get(path+'?generation='+generation,{headers})).json();expect(before.lines).toHaveLength(10);expect(new Set(before.lines.map((l:any)=>l.color)).size).toBe(10);
 expect(await page.getByRole('button',{name:'Invertir sentido'}).count()).toBe(0);expect(await page.locator('.progressive-surface .count-line-card').count()).toBe(0);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
 const card=page.locator('.count-line-card').first();await card.locator('summary').click();const started=Date.now();await card.getByLabel('Nombre de AV SIMÓN BOLIVAR').fill('AV CENTRAL');await card.getByLabel('Nombre de AV SIMÓN BOLIVAR').press('Enter');await expect(card.getByRole('heading',{name:'AV CENTRAL'})).toBeVisible();const latency=Date.now()-started;expect(latency).toBeLessThan(1000);fs.writeFileSync(info.outputPath('metadata-latency.json'),JSON.stringify({project:info.project.name,confirmed_metadata_ms:latency}));
 await card.getByLabel('Color de AV CENTRAL').fill('#123456');await expect.poll(async()=>{const d=await(await request.get(path+'?generation='+generation,{headers})).json();return d.lines[0].color}).toBe('#123456');
 const after=await(await request.get(path+'?generation='+generation,{headers})).json();expect(after.lines[0].geometry_revision).toBe(before.lines[0].geometry_revision);
 await page.reload();await page.getByRole('tab',{name:'Video',exact:true}).click();await expect(page.locator('.count-line-card')).toHaveCount(10);await page.screenshot({path:info.outputPath('ten-lines.png'),fullPage:true});await stop(page,request);
});
