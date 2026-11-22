export type Anchor={x:number;y:number};
const clamp=(n:number,min:number,max:number)=>Math.max(min,Math.min(max,n));
export function validScale(n:number){return Number.isFinite(n)&&n>0&&n<=4;}
export function fitScale(w:number,h:number,vw:number,vh:number){return w>0&&h>0&&vw>0&&vh>0?Math.min(1,vw/w,vh/h):1;}
export function normalizedAnchor(left:number,top:number,vw:number,vh:number,w:number,h:number):Anchor{
 return {x:w>0?clamp((left+vw/2)/w,0,1):.5,y:h>0?clamp((top+vh/2)/h,0,1):.5};
}
export function scrollForAnchor(a:Anchor,vw:number,vh:number,w:number,h:number){
 return {left:clamp(a.x*w-vw/2,0,Math.max(0,w-vw)),top:clamp(a.y*h-vh/2,0,Math.max(0,h-vh))};
}
