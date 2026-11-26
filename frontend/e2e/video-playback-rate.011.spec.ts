import {test,expect} from '@playwright/test';import {open,stop,seek,API,headers} from './multilineHelpers';import fs from 'node:fs';
test('source playback takes 60/30/15 seconds at 0.5/1/2 rates and preserves paused frame',async({page,request},info)=>{
 test.skip(info.project.name!=='desktop','Timing measured once on desktop; responsive controls covered by the other cases.');const {surface,job}=await open(page,request,2,true);
 await expect.poll(async()=> (await(await request.get(API+'/api/v1/video-jobs/'+job+'/playback',{headers})).json()).analysis_state,{timeout:60000}).toBe('complete');
 const observations=[];for(const rate of [.5,1,2]){
  await page.getByRole('button',{name:'Pausar e inspeccionar'}).click();await seek(page,'Home');await expect.poll(()=>surface.getAttribute('data-frame-index')).toBe('0');const frame=await surface.getAttribute('data-frame-index');await page.getByRole('combobox',{name:'Velocidad de reproducción'}).selectOption(String(rate));expect(await surface.getAttribute('data-frame-index')).toBe(frame);
  await page.getByRole('button',{name:'Reproducir',exact:true}).click();await expect.poll(async()=>Number(await surface.getAttribute('data-time-us'))).toBeGreaterThan(0);const start=Date.now(),sourceStart=Number(await surface.getAttribute('data-time-us'));
  await expect.poll(async()=>Number(await surface.getAttribute('data-time-us')),{timeout:70000,intervals:[100]}).toBeGreaterThanOrEqual(sourceStart+30_000_000);const elapsed=(Date.now()-start)/1000;observations.push({rate,elapsed,expected:30/rate});expect(Math.abs(elapsed/(30/rate)-1)).toBeLessThan(.05);
 }
 fs.writeFileSync(info.outputPath('playback-rate.json'),JSON.stringify(observations,null,2));await stop(page,request);
});
