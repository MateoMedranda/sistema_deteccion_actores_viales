import {it,expect} from "vitest";
import {parseEnrichmentPage,parsePlateProvenance} from "../../../src/services/apiTypes";
import {vehicleResult} from "../../fixtures/imageAnalysis";
it("does not infer historical origin from attempted enhancement",()=>{
 const item=vehicleResult();item.plate.used_enhancement=true;
 const result=parseEnrichmentPage({items:[item],page:1,page_size:50,total:1}).items[0];
 expect(result.plate.provenance).toBeUndefined();
 expect(parsePlateProvenance({version:1,policy_id:"baseline-v1",attempted_variants:["raw","legacy-retry-v1"],selected_variant:"raw"},"read")?.selected_variant).toBe("raw");
 expect(()=>parsePlateProvenance({version:1,policy_id:"baseline-v1",attempted_variants:["raw"],selected_variant:"bilateral-clahe-v1"},"read")).toThrow();
});
