import {createRef} from "react";
import {render,fireEvent,screen,act} from "@testing-library/react";
import {afterEach,it,expect,vi} from "vitest";
import {ProgressiveCountTools} from "../../../src/features/video-analysis/ProgressiveCountTools";
afterEach(()=>vi.unstubAllGlobals());
it("automatically shows frame zero and supports drawing, whole-line dragging and endpoint adjustment",async()=>{
 vi.stubGlobal("PointerEvent",MouseEvent);const draw=vi.fn();vi.spyOn(HTMLCanvasElement.prototype,"getContext").mockReturnValue({drawImage:draw} as unknown as CanvasRenderingContext2D);
 const first=document.createElement("canvas");first.width=1000;first.height=500;const apply=vi.fn().mockResolvedValue(undefined);
 const {container}=render(<ProgressiveCountTools firstFrame={first} source={createRef<HTMLCanvasElement>()} pause={()=>{}} enabled={false} onApply={apply} onDisable={async()=>{}} message="" position="0:18"/>);
 expect(draw).toHaveBeenCalledWith(first,0,0);expect(screen.getByText(/Fotograma de 0:00/)).toBeVisible();
 const area=container.querySelector(".count-frame-editor") as HTMLElement;area.getBoundingClientRect=()=>({left:0,top:0,width:1000,height:500}) as DOMRect;area.setPointerCapture=vi.fn();
 fireEvent.pointerDown(area,{clientX:100,clientY:100,button:0});fireEvent.pointerMove(area,{clientX:800,clientY:200});fireEvent.pointerUp(area);
 fireEvent.keyDown(screen.getByRole("button",{name:"Extremo 1"}),{key:"ArrowRight"});
 fireEvent.pointerDown(area,{clientX:455,clientY:150,button:0});fireEvent.pointerMove(area,{clientX:555,clientY:200});fireEvent.pointerUp(area);
 fireEvent.pointerDown(screen.getByRole("button",{name:"Extremo 2"}),{clientX:900,clientY:250,button:0});fireEvent.pointerMove(area,{clientX:900,clientY:350});fireEvent.pointerUp(area);
 await act(async()=>{fireEvent.click(screen.getByRole("button",{name:"Activar conteo"}))});
 const line=apply.mock.calls[0][0];expect(line.point_a.x).toBeCloseTo(.21);expect(line.point_a.y).toBeCloseTo(.3);expect(line.point_b.x).toBeCloseTo(.9);expect(line.point_b.y).toBeCloseTo(.7);
 fireEvent.click(screen.getByRole("button",{name:"Borrar línea"}));expect(container.querySelectorAll(".count-line-handle")).toHaveLength(0);
});
