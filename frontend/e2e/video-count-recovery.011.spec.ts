import {test,expect} from '@playwright/test';import {open,stop,headers,API,seek} from './multilineHelpers';
test('removed line never reappears and old collection revision cannot overwrite it',async({page,request})=>{
 const {path,generation}=await open(page,request,2);const old=await(await request.get(path+'?generation='+generation,{headers})).json();await page.locator('.count-line-card').first().locator('summary').click();await page.getByRole('button',{name:'Eliminar línea AV SIMÓN BOLIVAR',exact:true}).click();await expect(page.locator('.count-line-card')).toHaveCount(1);const response=await request.put(path,{headers,data:{generation,expected_revision:old.revision,lines:old.lines.map(({line_id,name,color,segment}:any)=>({line_id,name,color,segment}))}});expect(response.status()).toBe(409);await stop(page,request);
});

test('imports legacy geometry once, recalculates both ways and removes expired cards',async({page,request})=>{
 const {job,path,generation}=await open(page,request,0);
 const response=await request.put(API+'/api/v1/video-jobs/'+job+'/playback/directed-count',{headers,data:{generation,expected_revision:0,line:{point_a:{x:.1,y:.5},point_b:{x:.9,y:.5}},direction:'negative_to_positive'}});expect(response.ok()).toBeTruthy();
 await page.reload();await expect(page.locator('main')).toHaveAttribute('data-session-state','ready');await page.getByRole('tab',{name:'Video',exact:true}).click();await expect(page.locator('.count-line-card')).toHaveCount(1);
 await page.getByRole('button',{name:'Pausar e inspeccionar'}).click();await seek(page,'End');await expect(page.locator('.count-line-card strong')).toHaveText('5');
 const imported=await(await request.get(path+'?generation='+generation,{headers})).json();expect(imported.legacy_import.status).toBe('imported');
 await request.post(API+'/test-only/expire?job='+job);await expect(page.locator('.count-line-card')).toHaveCount(0,{timeout:10000});await request.post(API+'/test-only/release');
});
