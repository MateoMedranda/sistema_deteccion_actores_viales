import {readFileSync} from "node:fs";
import path from "node:path";
import {afterEach,it,expect,vi} from "vitest";
import {SourceDecoder} from "../../../src/features/video-analysis/sourceDecoder";
let open=0;
class Frame{
 codedWidth=640;codedHeight=360;closed=false;
 constructor(public timestamp:number){open++;}
 clone(){if(this.closed)throw Error("closed");return new Frame(this.timestamp);}
 close(){if(!this.closed){this.closed=true;open--;}}
}
class Chunk{timestamp:number;constructor(init:{timestamp:number}){this.timestamp=init.timestamp;}}
class Decoder{
 static isConfigSupported=async(config:unknown)=>({supported:true,config});
 decodeQueueSize=0;
 constructor(private init:{output:(f:Frame)=>void}){}
 configure(){}
 decode(chunk:Chunk){this.init.output(new Frame(chunk.timestamp));}
 async flush(){}
 close(){}
}
afterEach(()=>{vi.unstubAllGlobals();expect(open).toBe(0);});
it("keeps exact frame identity across cached seeks and closes every immutable frame",async()=>{
 vi.stubGlobal("VideoDecoder",Decoder);vi.stubGlobal("EncodedVideoChunk",Chunk);
 const bytes=readFileSync(path.resolve("e2e/fixtures/controlled.mp4"));let requests=0;
 const decoder=new SourceDecoder(async(start,end)=>{requests++;return Uint8Array.from(bytes.subarray(start,end+1)).buffer;},bytes.byteLength,new AbortController().signal);
 try{
  await decoder.initialize();await decoder.fill(0);
  expect(decoder.frame(0)?.timestamp).toBe(0);
  await decoder.seek(3);expect(decoder.frame(3)?.timestamp).toBe(3000);
  const before=requests;
  await decoder.seek(0);expect(decoder.frame(0)?.timestamp).toBe(0);
  await decoder.seek(3);expect(decoder.frame(3)?.timestamp).toBe(3000);
  expect(requests).toBe(before);
 }finally{decoder.close();}
});

it('bounds decoded frames, encoded blocks and posters while reading a long source',async()=>{
 const items=Array.from({length:64},(_,i)=>({displayIndex:i,sample:{offset:i*1024*1024,size:1,is_sync:true,cts:i,timescale:10}}));
 vi.doMock('../../../src/features/video-analysis/mp4Timeline',()=>({readMp4:async()=>({rotation:0,config:{codedWidth:640,codedHeight:360},samples:items,byDisplay:items})}));
 vi.resetModules();const {SourceDecoder:Actual}=await import('../../../src/features/video-analysis/sourceDecoder');vi.stubGlobal('VideoDecoder',Decoder);vi.stubGlobal('EncodedVideoChunk',Chunk);
 const d=new Actual(async(start,end)=>new ArrayBuffer(end-start+1),64*1024*1024,new AbortController().signal);
 try{
  await d.initialize();
  for(let i=0;i<64;i++){
   await d.fill(i);expect(d.frame(i)?.timestamp).toBe(i*1000);d.consume(i);
   expect(Array.from({length:64},(_,n)=>d.frame(n)).filter(Boolean).length).toBeLessThanOrEqual(28);
   expect(d.encodedBytes).toBeLessThanOrEqual(8*1024*1024);
  }
  for(const i of [0,16,32,48,0,16]){await d.seek(i);expect(d.frame(i)?.timestamp).toBe(i*1000);expect(d.posterBytes).toBeLessThanOrEqual(16*1024*1024)}
 }finally{d.close();vi.doUnmock('../../../src/features/video-analysis/mp4Timeline');vi.resetModules()}
});
it('closes overflowing decoded output instead of widening the 28-frame queue',async()=>{
 const item={displayIndex:0,sample:{offset:0,size:1,is_sync:true}};
 vi.doMock('../../../src/features/video-analysis/mp4Timeline',()=>({readMp4:async()=>({rotation:0,config:{codedWidth:640,codedHeight:360},samples:[item],byDisplay:[item]})}));vi.resetModules();const {SourceDecoder:Actual}=await import('../../../src/features/video-analysis/sourceDecoder');
 class BurstDecoder extends Decoder{constructor(private callbacks:{output:(f:Frame)=>void}){super(callbacks)}decode(){for(let i=0;i<30;i++)this.callbacks.output(new Frame(i*1000))}}
 vi.stubGlobal('VideoDecoder',BurstDecoder);vi.stubGlobal('EncodedVideoChunk',Chunk);
 const d=new Actual(async()=>new ArrayBuffer(1),1,new AbortController().signal);
 try{await d.initialize();await d.fill(0);expect(d.frame(27)).toBeDefined();expect(d.frame(28)).toBeUndefined();expect(open).toBe(28);await expect(d.fill(0)).rejects.toThrow('decoded_queue_overflow')}
 finally{d.close();vi.doUnmock('../../../src/features/video-analysis/mp4Timeline');vi.resetModules()}
});
