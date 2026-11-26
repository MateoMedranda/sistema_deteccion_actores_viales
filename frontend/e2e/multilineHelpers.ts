import {expect,type Page,type APIRequestContext} from '@playwright/test';import path from 'node:path';
export const API='http://127.0.0.1:9415',headers={'X-API-Key':'controlled-009'};
export async function open(page:Page,request:APIRequestContext,lines=2,complete=false){
 await request.post(API+'/test-only/reset?scenario=count');await page.goto('/');await expect(page.locator('main')).toHaveAttribute('data-session-state','ready');await page.getByRole('tab',{name:'Video',exact:true}).click();await page.locator('input[type=file][aria-label=Video]').setInputFiles(path.resolve('../.runtime/e2e-009/source.mp4'));
 for(let i=0;i<lines;i++){
  await page.getByRole('button',{name:'Añadir línea',exact:true}).click();await page.getByLabel('Nombre de la línea',{exact:true}).fill(i===0?'AV SIMÓN BOLIVAR':i===1?'RUTA VIVA':'VÍA '+(i+1));await page.getByRole('button',{name:'Activar conteo',exact:true}).click();
 }
 await page.getByRole('button',{name:'Procesar video',exact:true}).click();if(complete)await request.post(API+'/test-only/release');
 const surface=page.locator('.progressive-surface canvas');await expect(surface).toBeVisible({timeout:30000});expect(await page.evaluate(()=>typeof VideoDecoder)).toBe('function');await expect.poll(()=>surface.getAttribute('data-frame-index'),{timeout:30000}).not.toBeNull();await page.getByRole('button',{name:'Pausar e inspeccionar'}).click();
 const job=(await surface.getAttribute('data-job-id'))!;const playback=await (await request.get(API+'/api/v1/video-jobs/'+job+'/playback',{headers})).json();
 await expect(page.locator('.count-line-card')).toHaveCount(lines);if(lines)await expect(page.locator('.count-line-card input[type=color]').first()).toBeEnabled();return {surface,job,generation:playback.generation,path:API+'/api/v1/video-jobs/'+job+'/playback/count-lines'};
}
export async function stop(page:Page,request:APIRequestContext){await page.getByRole('button',{name:'Limpiar video',exact:true}).click();await request.post(API+'/test-only/release')}
export async function seek(page:Page,key:'Home'|'End'){const slider=page.getByRole('slider',{name:/Posición del video/});await slider.focus();await page.keyboard.press(key)}
