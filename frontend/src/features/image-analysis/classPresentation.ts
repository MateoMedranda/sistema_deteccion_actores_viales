import registry from "../../../../backend/app/domain/class_presentation.json" with {type:"json"};
/** Presentation only. Eligibility and identities always come from the server. */
export const classRegistry:Record<string,{label:string;color:string}>=registry.classes;
const aliases:Record<string,string>=registry.aliases;
export function classPresentation(name:string){
 const raw=name.trim().toLowerCase(),key=Object.prototype.hasOwnProperty.call(aliases,raw)?aliases[raw]:raw,known=Object.prototype.hasOwnProperty.call(classRegistry,key);
 return {key,label:known?classRegistry[key].label:name+" · Clase no reconocida",color:known?classRegistry[key].color:registry.fallback_color,known};
}
