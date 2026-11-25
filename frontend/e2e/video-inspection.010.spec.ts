import {test,expect} from '@playwright/test';import path from 'node:path';
test('selected frame has frozen evidence and exact context',async({page,request})=>{
 await request.post('http://127.0.0.1:9415/test-only/reset?scenario=count');await page.goto('/');await expect(page.locator('main')).toHaveAttribute('data-session-state','ready');await page.getByRole('tab',{name:'Video',exact:true}).click();
 await page.locator('input[type=file][aria-label=Video]').setInputFiles(path.resolve('../.runtime/e2e-009/source.mp4'));await page.getByRole('button',{name:'Procesar video',exact:true}).click();
 const surface=page.locator('.progressive-surface canvas');await expect(surface).toBeVisible({timeout:20000});
 if(!await page.evaluate(()=>typeof VideoDecoder==='function'))return;
 await expect.poll(()=>surface.getAttribute('data-frame-index')).not.toBeNull();await page.getByRole('button',{name:'Pausar e inspeccionar'}).click();
 const frame=await surface.getAttribute('data-frame-index');const bodies:any[]=[];page.on('request',r=>{if(r.method()==='POST'&&r.url().endsWith('/inspections'))bodies.push(r.postDataJSON())});
 await page.getByRole('button',{name:/^Consultar vehÃ­culo 1,/}).click();await expect(page.getByRole('heading',{name:'VehÃ­culo #1',exact:true})).toBeVisible();
 await expect(page.getByRole('img',{name:'Recorte del vehÃ­culo',exact:true})).toBeVisible({timeout:15000});expect(bodies[0].frame_index).toBe(Number(frame));
 const image=page.getByRole('img',{name:'Recorte del vehÃ­culo',exact:true});const url=await image.getAttribute('src');await expect(page.getByText('SYN123',{exact:true})).toBeVisible();
 await page.waitForTimeout(30000);expect(await image.getAttribute('src')).toBe(url);
 await page.getByRole('slider',{name:/PosiciÃ³n del video/}).focus();await page.keyboard.press('Home');await expect(page.getByRole('heading',{name:'VehÃ­culo #1',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'Limpiar video',exact:true}).click();await request.post('http://127.0.0.1:9415/test-only/release');
});
