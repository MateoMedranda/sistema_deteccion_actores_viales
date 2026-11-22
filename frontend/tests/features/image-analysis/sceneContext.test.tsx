import {render,screen} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import {AnnotatedImageViewer} from "../../../src/features/image-analysis/AnnotatedImageViewer";
import {sceneContextualState,initialState} from "../../../src/features/image-analysis/imageAnalysisReducer";
import {detectionResponse} from "../../fixtures/imageAnalysis";
it("describes the visual context with priority independent of selection",()=>{
 const state={...initialState,response:detectionResponse() as any,selected:1,hoveredDetectionId:2,focusedDetectionId:1};
 expect(sceneContextualState(state)).toEqual({id:1,state:"focus"});
 expect(sceneContextualState({...state,focusedDetectionId:undefined})).toEqual({id:2,state:"hover"});
 expect(sceneContextualState({...state,focusedDetectionId:undefined,hoveredDetectionId:undefined})).toEqual({id:1,state:"selected"});
 expect(sceneContextualState({...initialState})).toBeUndefined();
});
it("highlights a contextual box without changing selection or moving focus",()=>{
 const select=vi.fn(),props:any={source:detectionResponse(),url:"blob:scene",selected:1,onSelect:select,contextual:{id:2,state:"focus"}};
 const {rerender}=render(<AnnotatedImageViewer {...props}/>);
 const buttons=screen.getAllByRole("button").filter(b=>b.classList.contains("scene-contour"));
 expect(buttons[0]).toHaveAttribute("aria-pressed","true");
 expect(buttons[1]).toHaveAttribute("data-context","focus");
 expect(buttons[1]).not.toHaveFocus();expect(select).not.toHaveBeenCalled();
 rerender(<AnnotatedImageViewer {...props} contextual={{id:1,state:"hover"}}/>);
 expect(buttons[1]).not.toHaveAttribute("data-context");
 expect(buttons[0]).toHaveAttribute("data-context","hover");
 expect(buttons.every(b=>b.textContent==="")).toBe(true);
});
