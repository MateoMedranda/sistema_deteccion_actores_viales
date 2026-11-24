import {render,screen,fireEvent,waitFor} from "@testing-library/react";
import {describe,it,expect,vi} from "vitest";
import {VideoExport} from "../../../src/features/video-analysis/VideoExport";

const expires="2040-01-01T00:00:00Z";
const result=(state:string)=>({job_id:"v",state,processed_frames:state==="ready"?12:0,total_frames:12,expires_at:expires,
  url:state==="ready"?"/api/v1/video-jobs/v/annotated-video/content":null,error_code:null});
const props=(client:any)=>({client,id:"v",enabled:true,serverState:"waiting",active:true,expiresAt:expires,onUnavailable:vi.fn()});

describe("explicit video export",()=>{
  it("does not request a video by rendering or reading playback state",()=>{
    const client={json:vi.fn(),nativeVideo:vi.fn()};
    render(<VideoExport {...props(client)} enabled={false}/>);
    expect(screen.getByRole("button",{name:"Exportar video anotado"})).toBeDisabled();
    expect(client.json).not.toHaveBeenCalled();
  });
  it("requests once then polls and offers a protected native download",async()=>{
    const client={json:vi.fn(async(_path:string,options:any)=>result(options?.method==="POST"?"queued":"ready")),nativeVideo:vi.fn(()=>"/web-api/api/v1/video-jobs/v/annotated-video/content")};
    render(<VideoExport {...props(client)}/>);
    fireEvent.click(screen.getByRole("button",{name:"Exportar video anotado"}));
    const link=await screen.findByRole("link",{name:"Descargar MP4"});
    expect(link).toHaveAttribute("href","/web-api/api/v1/video-jobs/v/annotated-video/content");
    expect(client.json.mock.calls.filter(call=>call[1]?.method==="POST")).toHaveLength(1);
  });
  it("retries a failed export without restarting analysis",async()=>{
    const client={json:vi.fn(async(_path:string,options:any)=>result(options?.method==="POST"?"queued":"failed")),nativeVideo:vi.fn()};
    render(<VideoExport {...props(client)} serverState="failed"/>);
    fireEvent.click(await screen.findByRole("button",{name:"Reintentar exportación"}));
    await waitFor(()=>expect(client.json.mock.calls.some(call=>call[1]?.method==="POST")).toBe(true));
    expect(client.json.mock.calls.every(call=>call[0].endsWith("/playback/export"))).toBe(true);
  });
  it("checks an ambiguous request using GET instead of repeating POST",async()=>{
    const client={json:vi.fn(async(_path:string,options:any)=>{if(options?.method==="POST")throw new Error("connection reset");return result("ready");}),nativeVideo:vi.fn(()=>"/protected")};
    render(<VideoExport {...props(client)}/>);
    fireEvent.click(screen.getByRole("button",{name:"Exportar video anotado"}));
    await screen.findByRole("link",{name:"Descargar MP4"});
    expect(client.json.mock.calls.filter(call=>call[1]?.method==="POST")).toHaveLength(1);
  });
});
