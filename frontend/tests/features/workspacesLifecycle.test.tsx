import {render,screen,fireEvent,act} from "@testing-library/react";
import {useState} from "react";
import {it,expect,vi} from "vitest";
import {WorkspaceTabs} from "../../src/components/WorkspaceTabs";
import {useLegacyJob} from "../../src/hooks/useLegacyJob";
it("retains jobs and lets hidden evidence expire without navigation POST or cancellation",async()=>{
 vi.useFakeTimers();
 const cancel=vi.fn(async()=>{}),create=vi.fn(async()=>({job_id:"video-a",status:"completed",expires_at:new Date(Date.now()+3000).toISOString()}));
 function Panel(){const {job,run,message}=useLegacyJob({idKey:"job_id",poll:vi.fn(),cancel});return <><button onClick={()=>void run(create)}>Iniciar</button><p>{job?.job_id??message}</p></>}
 function Harness(){const [mode,setMode]=useState<"image"|"video">("image");return <><WorkspaceTabs active={mode} onChange={setMode}/><section hidden={mode!=="image"}><Panel/></section><section hidden={mode!=="video"}>Otro espacio</section></>}
 try{
 render(<Harness/>);await act(async()=>fireEvent.click(screen.getByRole("button",{name:"Iniciar"})));
 expect(screen.getByText("video-a")).toBeVisible();
 fireEvent.click(screen.getByRole("tab",{name:"Video"}));expect(create).toHaveBeenCalledTimes(1);expect(cancel).not.toHaveBeenCalled();
 await act(async()=>{vi.advanceTimersByTime(3001);});
 fireEvent.click(screen.getByRole("tab",{name:"Imagen"}));expect(screen.queryByText("video-a")).toBeNull();expect(screen.getByText(/ha vencido/)).toBeVisible();expect(create).toHaveBeenCalledTimes(1);
 }finally{vi.useRealTimers();}
});
