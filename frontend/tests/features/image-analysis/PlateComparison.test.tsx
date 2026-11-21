import {render,screen,fireEvent,waitFor} from "@testing-library/react";
import {it,expect,vi} from "vitest";
vi.mock("../../../src/utils/imageGeometry",async original=>({...await original<any>(),extractCrop:vi.fn().mockResolvedValue(new Blob())}));
import {extractCrop} from "../../../src/utils/imageGeometry";
import {PlateComparison} from "../../../src/features/image-analysis/PlateComparison";
import {detectionResponse,vehicleResult} from "../../fixtures/imageAnalysis";
it("keeps original first, exposes accessible modes and zoom without extra calls",async()=>{
 vi.mocked(extractCrop).mockResolvedValue(new Blob());
 const client:any={platePreview:vi.fn().mockResolvedValue({blob:new Blob(),metadata:{expires_at:new Date(Date.now()+60000).toISOString()}})};
 render(<PlateComparison client={client} jobId="j" sourceId="s" detection={detectionResponse().detections[0]} result={vehicleResult() as any} original="blob:original" expiresAt={Date.now()+60000}/>);
 await waitFor(()=>expect(screen.getByRole("button",{name:"Procesada"})).toBeEnabled());
 expect(screen.getByRole("button",{name:"Original"})).toHaveAttribute("aria-pressed","true");
 fireEvent.click(screen.getByRole("button",{name:"Procesada"}));
 fireEvent.click(screen.getByRole("button",{name:"4x"}));
 expect(client.platePreview).toHaveBeenCalledTimes(1);
 expect(screen.getByRole("region",{name:"Inspección de placa"})).toHaveAttribute("tabindex","0");
});
