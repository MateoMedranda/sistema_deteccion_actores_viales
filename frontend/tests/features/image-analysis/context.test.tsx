import { it, expect } from "vitest";
import { initialState, imageAnalysisReducer, contextualDetectionId, sceneInteraction } from "../../../src/features/image-analysis/imageAnalysisReducer";
import { detectionResponse } from "../../fixtures/imageAnalysis";
it("prioritizes focus, hover, selection and ignores stale leaves and sources",()=>{
 let s:import("../../../src/features/image-analysis/imageAnalysisReducer").ImageState={...initialState,response:detectionResponse() as any,selected:1};
 s=sceneInteraction(s,"hover",2,s.response!.request_id);
 expect(contextualDetectionId(s)).toBe(2);expect(s.selected).toBe(1);
 s=sceneInteraction(s,"focus",1,s.response!.request_id);
 expect(contextualDetectionId(s)).toBe(1);
 s=sceneInteraction(s,"hover",1,s.response!.request_id);
 s=sceneInteraction(s,"leave",2,s.response!.request_id);
 expect(s.hoveredDetectionId).toBe(1);
 s=sceneInteraction(s,"blur",2,s.response!.request_id);
 expect(s.focusedDetectionId).toBe(1);
 expect(sceneInteraction(s,"hover",2,"stale")).toBe(s);
 expect(sceneInteraction(s,"focus",999,s.response!.request_id)).toBe(s);
 s=imageAnalysisReducer(s,{...initialState,generation:2});
 expect(contextualDetectionId(s)).toBeUndefined();
});

it("applies queued context to the latest results without replaying an old snapshot",()=>{
 const before={...initialState,response:detectionResponse() as any,selected:1,phase:"enriching" as const,generation:3};
 const completed=imageAnalysisReducer(before,{phase:"completed",progress:100});
 const after=imageAnalysisReducer(completed,{contextEvent:"hover",detectionId:2,sourceId:before.response.request_id,generation:3} as any);
 expect(contextualDetectionId(after)).toBe(2);
 expect(after.phase).toBe("completed");expect(after.progress).toBe(100);expect(after.selected).toBe(1);
 const reset=imageAnalysisReducer(after,{...initialState,generation:4});
 expect(imageAnalysisReducer(reset,{contextEvent:"focus",detectionId:2,sourceId:before.response.request_id,generation:3} as any)).toBe(reset);
});
