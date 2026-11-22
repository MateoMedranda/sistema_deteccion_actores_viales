import { render, fireEvent, screen } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { LineEditor } from "../src/components/LineEditor";
it("clears the parent configuration and resets points when the source changes", () => {
  vi.stubGlobal("PointerEvent", MouseEvent);
  const onLine = vi.fn(),
    onClear = vi.fn();
  const { container, rerender } = render(
    <LineEditor videoUrl="blob:a" onLine={onLine} onClear={onClear} />,
  );
  const editor = container.querySelector(".line-editor") as HTMLElement;
  editor.getBoundingClientRect = () =>
    ({ left: 0, top: 0, width: 100, height: 100 }) as DOMRect;
  editor.setPointerCapture = vi.fn();
  fireEvent.pointerDown(editor, { clientX: 10, clientY: 20 });
  fireEvent.pointerMove(editor, { clientX: 80, clientY: 70 });
  fireEvent.pointerUp(editor);
  expect(onLine).toHaveBeenCalled();
  fireEvent.click(screen.getByText("Borrar línea"));
  expect(onClear).toHaveBeenCalled();
  fireEvent.pointerDown(editor, { clientX: 10, clientY: 20 });
  fireEvent.pointerMove(editor, { clientX: 80, clientY: 70 });
  rerender(<LineEditor videoUrl="blob:b" onLine={onLine} onClear={onClear} />);
  expect(container.querySelectorAll(".line-handle")).toHaveLength(0);
  vi.unstubAllGlobals();
});

it("uses processed-video proportions and supports keyboard adjustment without keeping a cleared line",()=>{
 vi.stubGlobal("PointerEvent",MouseEvent);const onLine=vi.fn(),onClear=vi.fn();
 const {container}=render(<LineEditor videoUrl="/processed" dimensions={{width:640,height:360}} onLine={onLine} onClear={onClear}/>);
 const editor=container.querySelector(".line-editor") as HTMLElement;expect(editor.style.aspectRatio).toBe(String(640/360));
 editor.getBoundingClientRect=()=>({left:0,top:0,width:640,height:360}) as DOMRect;editor.setPointerCapture=vi.fn();
 fireEvent.pointerDown(editor,{clientX:64,clientY:72});fireEvent.pointerMove(editor,{clientX:512,clientY:288});fireEvent.pointerUp(editor);
 expect(onLine).toHaveBeenLastCalledWith({x:.1,y:.2},{x:.8,y:.8});
 fireEvent.keyDown(screen.getByRole("button",{name:"Extremo 1"}),{key:"ArrowRight"});
 expect(onLine).toHaveBeenLastCalledWith({x:.11,y:.2},{x:.8,y:.8});
 const before=onClear.mock.calls.length;fireEvent.pointerDown(editor,{clientX:32,clientY:32});expect(onClear.mock.calls.length).toBeGreaterThan(before);
 vi.unstubAllGlobals();
});
