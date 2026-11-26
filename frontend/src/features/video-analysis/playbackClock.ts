export const PLAYBACK_RATES=[.25,.5,.75,1,1.25,1.5,2] as const;
export type ClockAnchor={wall:number;us:number;rate:number};
export const sourceTime=(anchor:ClockAnchor,now:number)=>anchor.us+Math.max(0,now-anchor.wall)*1000*anchor.rate;
export const reanchor=(anchor:ClockAnchor,now:number,rate:number):ClockAnchor=>{if(!(PLAYBACK_RATES as readonly number[]).includes(rate))throw Error("invalid_playback_rate");return {wall:now,us:sourceTime(anchor,now),rate}};
