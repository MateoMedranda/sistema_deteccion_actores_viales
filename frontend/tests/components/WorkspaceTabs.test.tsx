import {render,screen,fireEvent} from "@testing-library/react";
import {describe,it,expect,vi} from "vitest";
import {WorkspaceTabs} from "../../src/components/WorkspaceTabs";
describe("WorkspaceTabs",()=>{
 it("supports manual keyboard activation and named panels",()=>{
  const change=vi.fn();render(<WorkspaceTabs active="image" onChange={change}/>);
  const image=screen.getByRole("tab",{name:"Imagen"}),video=screen.getByRole("tab",{name:"Video"});
  image.focus();fireEvent.keyDown(image,{key:"ArrowRight"});expect(document.activeElement).toBe(video);
  expect(change).not.toHaveBeenCalled();fireEvent.keyDown(video,{key:"Enter"});expect(change).toHaveBeenCalledWith("video");
  expect(image).toHaveAttribute("aria-selected","true");expect(video).toHaveAttribute("aria-controls","panel-video");
 });
});
