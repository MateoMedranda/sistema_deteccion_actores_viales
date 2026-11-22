import registry from "../../../../app/domain/class_presentation.json";
/** Presentation only. Eligibility and identities always come from the server. */
export const classRegistry:Record<string,{label:string;color:string}>=registry.classes;
export function classPresentation(name:string){
 const key=name.trim().toLowerCase(),known=Object.prototype.hasOwnProperty.call(classRegistry,key);
 return {key,label:known?classRegistry[key].label:name+" · Clase no reconocida",color:known?classRegistry[key].color:registry.fallback_color,known};
}
