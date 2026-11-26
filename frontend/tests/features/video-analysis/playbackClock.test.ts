import {it,expect} from 'vitest';
import {sourceTime,reanchor,PLAYBACK_RATES} from '../../../src/features/video-analysis/playbackClock';
it('reanchors at the same source instant using the old rate',()=>{
 const anchor={wall:1000,us:2000000,rate:1};const next=reanchor(anchor,1500,2);
 expect(next.us).toBe(2500000);expect(sourceTime(next,2000)).toBe(3500000);
 expect(PLAYBACK_RATES).toEqual([.25,.5,.75,1,1.25,1.5,2]);
});

it('rejects unsupported playback rates',()=>expect(()=>reanchor({wall:0,us:0,rate:1},100,3)).toThrow());

it('supports consecutive changes and starts a fresh anchor after wait or seek',()=>{let a={wall:0,us:0,rate:1};a=reanchor(a,1000,.5);a=reanchor(a,3000,2);expect(sourceTime(a,3500)).toBe(3000000);const resumed={wall:9000,us:1500000,rate:2};expect(sourceTime(resumed,9500)).toBe(2500000);expect(()=>reanchor(a,4000,3)).toThrow()});
