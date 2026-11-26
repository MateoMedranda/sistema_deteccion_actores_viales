import {test,expect} from '@playwright/test';import {open,stop,seek,headers} from './multilineHelpers';
test('counts match painted source time across ten rewinds and reject twenty future requests',async({page,request})=>{
 const {path,generation,surface}=await open(page,request,2);
 const collection=await(await request.get(path+'?generation='+generation,{headers})).json();
 for(let i=0;i<10;i++){
  await seek(page,'Home');await expect.poll(()=>surface.getAttribute('data-frame-index')).toBe('0');await expect(page.locator('.count-line-card strong').first()).toHaveText('0');
  await seek(page,'End');await expect.poll(async()=>Number(await surface.getAttribute('data-frame-index'))).toBeGreaterThan(100);
  const at=await surface.getAttribute('data-time-us');const snapshot=await(await request.get(path+'/counts?generation='+generation+'&revision='+collection.revision+'&at_us='+at,{headers})).json();expect(snapshot.lines.map((l:any)=>l.total)).toEqual([5,5]);await expect.poll(()=>page.locator('.count-line-card strong').first().textContent()).toBe(String(snapshot.lines[0].total));
 }
 const limit=Number(await surface.getAttribute('data-admitted-until-us'));for(let i=0;i<20;i++){const slider=page.getByRole('slider',{name:/Posición del video/});await slider.focus();await page.keyboard.press('ArrowRight');expect(Number(await surface.getAttribute('data-time-us'))).toBeLessThan(limit)}
 for(let i=0;i<20;i++)expect((await request.get(path+'/counts?generation='+generation+'&revision='+collection.revision+'&at_us=39000000',{headers})).status()).toBe(409);
 await stop(page,request);
});
