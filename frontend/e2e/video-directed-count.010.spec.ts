import {test,expect} from '@playwright/test';import path from 'node:path';
test('configures first local frame and directed historical counts',async({page,request})=>{
 await request.post('http://127.0.0.1:9415/test-only/reset?scenario=count');await page.goto('/');await expect(page.locator('main')).toHaveAttribute('data-session-state','ready');await page.getByRole('tab',{name:'Video',exact:true}).click();
 await page.locator('input[type=file][aria-label=Video]').setInputFiles(path.resolve('../.runtime/e2e-009/source.mp4'));
 const editor=page.locator('.count-frame-editor');await expect(editor).toBeVisible();const box=(await editor.boundingBox())!;
 await editor.scrollIntoViewIfNeeded();await editor.click({position:{x:box.width*.05,y:box.height*.3}});await editor.click({position:{x:box.width*.95,y:box.height*.3}});
 await page.getByRole('button',{name:'Activar conteo',exact:true}).click();await expect(page.getByText('El conteo se aplicará al iniciar el análisis.')).toBeVisible();
 await page.getByRole('button',{name:'Procesar video',exact:true}).click();
 const surface=page.locator('.progressive-surface canvas');await expect(surface).toBeVisible({timeout:20000});if(!await page.evaluate(()=>typeof VideoDecoder==='function'))return;
 await expect.poll(()=>surface.getAttribute('data-frame-index')).not.toBeNull();await page.getByRole('button',{name:'Pausar e inspeccionar'}).click();
 const slider=page.getByRole('slider',{name:/Posición del video/});const counter=page.getByLabel('Contador de cruces');
 for(let i=0;i<5;i++){
  await slider.focus();await page.keyboard.press('Home');await expect(counter.locator('strong')).toHaveText('0');
  await slider.focus();await page.keyboard.press('End');await expect(counter.locator('strong')).toHaveText('5');
 }
 await page.getByRole('button',{name:'Invertir sentido',exact:true}).click();await page.getByRole('button',{name:'Aplicar nueva línea',exact:true}).click();await expect(counter.locator('strong')).toHaveText('0');
 await page.getByRole('button',{name:'Limpiar video',exact:true}).click();await request.post('http://127.0.0.1:9415/test-only/release');
});
