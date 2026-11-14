import type { Point } from "../services/apiTypes";
export const validLine = (a: Point, b: Point) => [a.x,a.y,b.x,b.y].every(n => Number.isFinite(n) && n >= 0 && n <= 1) && (a.x !== b.x || a.y !== b.y);
export const normalizedPoint = (event: { clientX:number; clientY:number }, rect: DOMRect): Point => ({ x: Math.min(1, Math.max(0, (event.clientX-rect.left)/rect.width)), y: Math.min(1, Math.max(0, (event.clientY-rect.top)/rect.height)) });

