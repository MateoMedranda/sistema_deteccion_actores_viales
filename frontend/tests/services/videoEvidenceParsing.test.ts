import {it,expect} from "vitest";
import {parseVideoEnrichmentPage} from "../../src/services/apiTypes";
import {vehicleResult} from "../fixtures/imageAnalysis";
const page=(patch:any={})=>({items:[{...vehicleResult(),track_id:42,evidence_frame_indexes:[0,12],attributes:[{name:"color",label:"blue",confidence:.8,evidence_frame_index:12}],...patch}],page:1,page_size:25,total:1});
it("keeps real track identity and temporal evidence with confirmed bounds",()=>{
 const item=parseVideoEnrichmentPage(page(),20).items[0];expect(item.track_id).toBe(42);expect(item.evidence_frame_indexes).toEqual([0,12]);expect(item.attributes[0].evidence_frame_index).toBe(12);expect(item.plate.provenance).toBeUndefined();
 for(const indexes of [[-1],[20],[1,1],Array.from({length:21},(_,i)=>i)])expect(()=>parseVideoEnrichmentPage(page({evidence_frame_indexes:indexes}),20)).toThrow();
 expect(()=>parseVideoEnrichmentPage(page({track_id:null}))).toThrow();
 expect(()=>parseVideoEnrichmentPage(page({track_id:0}))).toThrow();
});
