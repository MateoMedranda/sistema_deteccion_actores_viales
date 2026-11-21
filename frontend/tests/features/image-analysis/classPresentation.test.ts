import { expect,it } from "vitest";
import { classPresentation, classRegistry } from "../../../src/features/image-analysis/classPresentation";
it("has 13 explicit unique stable tokens, with safe unknown presentation",()=>{
 expect(Object.keys(classRegistry)).toHaveLength(13);
 for(const name of "car,truck,bus,van,pickup,suv,sedan,hatchback,mpv,estate".split(","))expect(classPresentation(name).known).toBe(true);
 expect(new Set(Object.values(classRegistry).map(v=>v.color)).size).toBe(13);
 expect(classPresentation(" CAR ")).toEqual(classPresentation("car"));
 expect(classPresentation("car").color).toBe("#2563EB");
 expect(classPresentation("<script>")).toEqual({key:"<script>",label:"<script> · Clase no reconocida",color:"#64748B",known:false});
 expect(classPresentation("person").color).toBe("#C2410C");
});

it("keeps every class token under reordered analyses and subsets",()=>{
 const names=[...Object.keys(classRegistry),"unrecognized"];
 const original=new Map(names.map(n=>[n,classPresentation(n)]));
 for(const order of [[...names].reverse(),names.filter((_,i)=>i%2),names.slice(2,7)]){
  for(const name of order)expect(classPresentation(" "+name.toUpperCase()+" ")).toMatchObject({key:original.get(name)!.key,color:original.get(name)!.color,known:original.get(name)!.known});
 }
});
