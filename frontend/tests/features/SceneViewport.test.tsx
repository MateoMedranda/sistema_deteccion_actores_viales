import {render,screen,fireEvent} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import {SceneViewport} from "../../src/features/image-analysis/SceneViewport";
it("keeps one stage, resets a new source and never captures button keyboard input",()=>{
 const selected=vi.fn(),view=render(<SceneViewport sourceId="a" width={1200} height={600}><button onClick={selected}>Vehicle</button></SceneViewport>);
 fireEvent.click(screen.getByRole("button",{name:"200%"}));
 expect(screen.getByTestId("scene-stage").style.width).toBe("2400px");
 fireEvent.keyDown(screen.getByText("Vehicle"),{key:"Home"});fireEvent.click(screen.getByText("Vehicle"));expect(selected).toHaveBeenCalledOnce();
 view.rerender(<SceneViewport sourceId="b" width={1200} height={600}><span>New</span></SceneViewport>);
 expect(screen.getByRole("button",{name:"Ajustar"})).toHaveAttribute("aria-pressed","true");
});

it("captures only a drag, suppresses its click and releases on cancel or blur",()=>{
 vi.stubGlobal("PointerEvent",MouseEvent);
 const selected=vi.fn();render(<SceneViewport sourceId="drag" width={1200} height={600}><button onClick={selected}>Target</button></SceneViewport>);
 fireEvent.click(screen.getByRole("button",{name:"200%"}));
 const port=screen.getByRole("region",{name:"Explorar escena original"}),button=screen.getByText("Target"),capture=vi.fn(),release=vi.fn();
 port.setPointerCapture=capture;port.releasePointerCapture=release;port.hasPointerCapture=()=>true;
 fireEvent.pointerDown(button,{button:0,clientX:100,clientY:100});
 fireEvent.pointerMove(button,{clientX:103,clientY:100});expect(capture).not.toHaveBeenCalled();
 fireEvent.pointerMove(button,{clientX:112,clientY:100});expect(capture).toHaveBeenCalledOnce();
 fireEvent.pointerUp(button);fireEvent.click(button);expect(selected).not.toHaveBeenCalled();fireEvent.click(button);expect(selected).toHaveBeenCalledOnce();expect(release).toHaveBeenCalled();
 fireEvent.pointerDown(button,{button:0,clientX:100,clientY:100});fireEvent.pointerMove(button,{clientX:120,clientY:100});fireEvent.pointerCancel(port);
 fireEvent.keyDown(port,{key:"ArrowRight"});expect(port.scrollLeft).toBe(8);
 vi.unstubAllGlobals();
});
