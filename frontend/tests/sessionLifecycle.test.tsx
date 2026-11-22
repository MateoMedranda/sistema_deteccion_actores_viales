import {render,screen,fireEvent,waitFor} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import App from "../src/App";
it("bootstraps from managed configuration and reset replaces the epoch without manual secrets",async()=>{
 let sessions=0;const calls:string[]=[];
 const image={media_types:["image/jpeg","image/png"],max_upload_bytes:10485760,max_image_pixels:16000000};
 vi.stubGlobal("fetch",vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
  const path=String(input);calls.push((init?.method??"GET")+" "+path);
  const value=path==="/web/session"&&init?.method==="POST"?{status:"ready",epoch:"00000000-0000-4000-8000-"+String(++sessions).padStart(12,"0"),csrf_token:"c".repeat(43),expires_at:new Date(Date.now()+60000).toISOString(),policy:{image,video:{media_types:["video/mp4"],max_upload_bytes:100000,max_duration_seconds:120,max_width:1920,max_height:1080,max_fps:30,max_frames:3600},capabilities:{image_detection:true,video_analysis:true,attributes:true,plates:true}}}:image;
  return new Response(init?.method==="DELETE"?null:JSON.stringify(value),{status:init?.method==="DELETE"?204:200,headers:{"Content-Type":"application/json"}});
 }));
 try{
 render(<App/>);await screen.findByText("Servicio conectado");
 expect(screen.queryByLabelText("API key")).toBeNull();expect(screen.queryByLabelText("URL backend")).toBeNull();
 fireEvent.click(screen.getByRole("button",{name:"Reiniciar sesión"}));
 await waitFor(()=>expect(sessions).toBe(2));
 expect(calls.some(x=>x==="DELETE /web/session")).toBeTruthy();
 expect(screen.queryByLabelText("API key")).toBeNull();
 }finally{vi.unstubAllGlobals();}
});
