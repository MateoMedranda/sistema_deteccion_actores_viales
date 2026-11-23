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
