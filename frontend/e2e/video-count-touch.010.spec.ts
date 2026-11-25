import {test,expect} from '@playwright/test';import path from 'node:path';
 test('first-frame editor supports touch, keyboard and a visible direction arrow',async({page},info)=>{
 test.skip(!info.project.use.hasTouch,'Touch project required');await page.goto('/');await expect(page.locator('main')).toHaveAttribute('data-session-state','ready');await page.getByRole('tab',{name:'Video',exact:true}).click();await page.locator('input[type=file][aria-label=Video]').setInputFiles(path.resolve('../.runtime/e2e-009/source.mp4'));
 const editor=page.locator('.count-frame-editor');await expect(editor).toBeVisible();const box=(await editor.boundingBox())!;await editor.tap({position:{x:box.width*.1,y:box.height*.3}});await editor.tap({position:{x:box.width*.9,y:box.height*.3}});
 const handle=page.getByRole('button',{name:'Extremo 1',exact:true});await handle.focus();await page.keyboard.press('ArrowRight');await page.keyboard.press('ArrowLeft');
 const arrow=editor.locator('line[marker-end]');await expect(arrow).toBeVisible();expect(await arrow.evaluate(e=>parseFloat(getComputedStyle(e).strokeWidth))).toBeGreaterThan(1);
 await page.getByRole('button',{name:'Invertir sentido',exact:true}).click();await page.getByRole('button',{name:'Activar conteo',exact:true}).click();await expect(page.getByText('El conteo se aplicará al iniciar el análisis.')).toBeVisible();await page.screenshot({path:info.outputPath('touch-direction.png'),fullPage:true});await page.getByRole('button',{name:'Limpiar video',exact:true}).click();
 });
