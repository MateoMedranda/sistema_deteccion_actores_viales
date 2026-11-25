import type {CountLine} from './useProgressiveCount';
export type CountDirection='negative_to_positive'|'positive_to_negative';
export function directionArrow(line:CountLine,width:number,height:number,direction:CountDirection){
 const a=line.point_a,b=line.point_b,dx=(b.x-a.x)*width,dy=(b.y-a.y)*height,len=Math.hypot(dx,dy)||1,sign=direction==='negative_to_positive'?1:-1;
 const mx=(a.x+b.x)*width/2,my=(a.y+b.y)*height/2,length=Math.min(width,height)*.09;
 const nx=-dy/len*length*sign,ny=dx/len*length*sign;
 return {x1:mx-nx,y1:my-ny,x2:mx+nx,y2:my+ny};
}
