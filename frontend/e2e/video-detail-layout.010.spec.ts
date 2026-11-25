import {test,expect} from '@playwright/test';
test('shared details use page scrolling at each target width',async({page})=>{
 await page.goto('/');
 for(const width of [360,768,1440]){
  await page.setViewportSize({width,height:850});
  await page.evaluate(()=>{const card=document.createElement('aside');card.className='vehicle-details progressive-details';card.id='layout010';card.innerHTML='<h3>Ficha del vehículo</h3>'+Array.from({length:30},(_,i)=>'<p>Detalle '+i+'</p>').join('');document.body.append(card)});
  const metrics=await page.locator('#layout010').evaluate(el=>({max:getComputedStyle(el).maxHeight,overflow:getComputedStyle(el).overflowY,full:el.scrollHeight<=el.clientHeight+2}));
  expect(metrics.max).toBe('none');expect(metrics.overflow).not.toMatch(/auto|scroll/);expect(metrics.full).toBe(true);
  await page.screenshot({path:'test-results/010-artifacts/card-'+width+'.png',fullPage:true});
  await page.locator('#layout010').evaluate(el=>el.remove());
 }
});
