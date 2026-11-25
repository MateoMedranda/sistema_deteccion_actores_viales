import {it,expect} from 'vitest';import {directionArrow} from '../../../src/features/video-analysis/directionArrow';
it('normal arrow is perpendicular in source pixels, including non-square scenes',()=>{
 const line={point_a:{x:.1,y:.2},point_b:{x:.8,y:.6}};const a=directionArrow(line,1920,1080,'negative_to_positive');
 const b=directionArrow(line,1920,1080,'positive_to_negative');
 const dx=(line.point_b.x-line.point_a.x)*1920,dy=(line.point_b.y-line.point_a.y)*1080;
 expect(dx*(a.x2-a.x1)+dy*(a.y2-a.y1)).toBeCloseTo(0,5);expect(a.x1).toBeCloseTo(b.x2);expect(a.y1).toBeCloseTo(b.y2);
});
