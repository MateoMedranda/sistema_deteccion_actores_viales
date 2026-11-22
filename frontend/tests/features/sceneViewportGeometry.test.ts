import {it,expect} from "vitest";
import {fitScale,scrollForAnchor,normalizedAnchor,validScale} from "../../src/features/image-analysis/sceneViewportGeometry";
it("uses intrinsic pixels, fits without upscaling and preserves a bounded center",()=>{
 expect(fitScale(4000,2000,800,600)).toBe(.2);
 expect(fitScale(100,80,800,600)).toBe(1);
 expect(validScale(Infinity)).toBe(false);expect(validScale(8)).toBe(false);expect(validScale(4)).toBe(true);
 const scroll=scrollForAnchor({x:.75,y:.6},800,600,8000,4000);
 expect(normalizedAnchor(scroll.left,scroll.top,800,600,8000,4000)).toEqual({x:.75,y:.6});
 expect(scrollForAnchor({x:0,y:1},800,600,4000,2000)).toEqual({left:0,top:1400});
});
