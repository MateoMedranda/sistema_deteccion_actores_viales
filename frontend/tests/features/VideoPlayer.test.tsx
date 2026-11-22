import {StrictMode} from "react";
import {render,screen,fireEvent} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import {VideoPlayer} from "../../src/features/video-analysis/VideoPlayer";
it("uses native cookie URL, pauses when hidden and never creates a job on media error",async()=>{
 const pause=vi.spyOn(HTMLMediaElement.prototype,"pause").mockImplementation(()=>{});
 vi.spyOn(HTMLMediaElement.prototype,"load").mockImplementation(()=>{});
 const client={nativeVideo:()=>"/web-api/api/v1/video-jobs/v/annotated-video/content",video:vi.fn(async()=>({status:"completed"}))};
 const job={job_id:"v",expires_at:new Date(Date.now()+60000).toISOString()} as any;
 const {rerender}=render(<VideoPlayer client={client as any} job={job} active/>);
 expect(document.querySelector("video")?.src).toContain("/web-api/");
 rerender(<VideoPlayer client={client as any} job={job} active={false}/>);expect(pause).toHaveBeenCalled();
 fireEvent.error(document.querySelector("video")!);
 await screen.findByText(/No se pudo reproducir/);expect(client.video).toHaveBeenCalledTimes(1);
});

it("restores the native source after StrictMode cleanup",()=>{
 vi.spyOn(HTMLMediaElement.prototype,"pause").mockImplementation(()=>{});vi.spyOn(HTMLMediaElement.prototype,"load").mockImplementation(()=>{});
 const client={nativeVideo:()=>"/web-api/api/v1/video-jobs/v/annotated-video/content",video:vi.fn()} as any;
 const job={job_id:"v",status:"completed",expires_at:"2040-01-01T00:00:00Z"} as any;
 const {container}=render(<StrictMode><VideoPlayer client={client} job={job}/></StrictMode>);
 expect(container.querySelector("video")?.getAttribute("src")).toBe(client.nativeVideo());
});
