import {test,expect} from '@playwright/test';import path from 'node:path';
test('final inventory is independent of seeking and line configuration',async({page,request})=>{
 await request.post('http://127.0.0.1:9415/test-only/reset?scenario=short');await page.goto('/');await expect(page.locator('main')).toHaveAttribute('data-session-state','ready');await page.getByRole('tab',{name:'Video',exact:true}).click();await page.locator('input[type=file][aria-label=Video]').setInputFiles(path.resolve('../.runtime/e2e-009/source.mp4'));await page.getByRole('button',{name:'Procesar video',exact:true}).click();
 const summary=page.getByRole('region',{name:'Resumen de detecciones de todo el video'});await expect(summary.getByText('Definitivo',{exact:true})).toBeVisible({timeout:30000});await expect(summary.getByText('10 identidades de vehículos')).toBeVisible();
 const before=await summary.innerText();const slider=page.getByRole('slider',{name:/Posición del video/});if(await slider.isEnabled()){await slider.focus();await page.keyboard.press('End');await page.keyboard.press('Home')}
 expect(await summary.innerText()).toBe(before);await page.getByRole('button',{name:'Limpiar video',exact:true}).click();
});
