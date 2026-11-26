import {test,expect} from '@playwright/test';import {open,stop} from './multilineHelpers';
test('keyboard selection, touch editor and fullscreen keep cards readable',async({page,request},info)=>{
 await open(page,request,10);const card=page.locator('.count-line-card').first();await card.getByRole('button',{name:'Seleccionar línea AV SIMÓN BOLIVAR'}).click();await expect(card.getByRole('button',{name:'Seleccionar línea AV SIMÓN BOLIVAR'})).toHaveAttribute('aria-pressed','true');
 await page.getByRole('button',{name:'Pantalla completa',exact:true}).click();await expect.poll(()=>page.evaluate(()=>!!document.fullscreenElement)).toBeTruthy();await expect(card).toBeVisible();expect(await page.locator('.progressive-surface .count-line-card').count()).toBe(0);await page.screenshot({path:info.outputPath('fullscreen-lines.png')});await page.keyboard.press('Escape');
 const handle=page.getByRole('button',{name:'Extremo 1',exact:true});await handle.focus();await page.keyboard.press('ArrowRight');await page.keyboard.press('ArrowLeft');await expect(page.getByRole('button',{name:'Invertir sentido'})).toHaveCount(0);await stop(page,request);
});
