/** Presentation only. Eligibility and identities always come from the server. */
export const classRegistry: Record<string,{label:string;color:string}> = {
 car:{label:"Automóvil",color:"#2563EB"},truck:{label:"Camión",color:"#D97706"},
 bus:{label:"Autobús",color:"#9333EA"},van:{label:"Furgoneta",color:"#0D9488"},
 pickup:{label:"Pickup",color:"#DC2626"},suv:{label:"SUV",color:"#65A30D"},
 sedan:{label:"Sedán",color:"#DB2777"},hatchback:{label:"Hatchback",color:"#0891B2"},
 mpv:{label:"Monovolumen",color:"#4F46E5"},estate:{label:"Familiar",color:"#78716C"},
 person:{label:"Persona",color:"#C2410C"},bicycle:{label:"Bicicleta",color:"#0F766E"},
 motorcycle:{label:"Motocicleta",color:"#A16207"},
};
export function classPresentation(name:string){
 const key=name.trim().toLowerCase(),known=Object.prototype.hasOwnProperty.call(classRegistry,key);
 return {key,label:known?classRegistry[key].label:name+" · Clase no reconocida",color:known?classRegistry[key].color:"#64748B",known};
}
