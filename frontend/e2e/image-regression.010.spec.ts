import {test,expect} from '@playwright/test';import path from 'node:path';
test('image analysis retains the shared detail card and canonical evidence',async({page})=>{
 await page.goto('/');await expect(page.locator('main')).toHaveAttribute('data-session-state','ready');await page.getByLabel('Seleccionar imagen',{exact:true}).setInputFiles(path.resolve('e2e/fixtures/scene.jpg'));await page.getByRole('button',{name:'Analizar imagen',exact:true}).click();
 await expect(page.getByText('Análisis completo',{exact:true})).toBeVisible({timeout:20000});await page.locator('.detection-list button').first().click();await expect(page.getByRole('img',{name:'Recorte del vehículo',exact:true})).toBeVisible();
 const card=page.getByRole('complementary',{name:'Ficha del vehículo'});expect(await card.evaluate(e=>getComputedStyle(e).overflowY)).not.toMatch(/auto|scroll/);await page.screenshot({path:'test-results/010-artifacts/image-card.png',fullPage:true});
});
