import {render,screen} from "@testing-library/react";
import {it,expect} from "vitest";
import {VideoTrackDetails} from "../../src/features/video-analysis/VideoTrackDetails";
import {vehicleResult} from "../fixtures/imageAnalysis";
it("labels evidence rather than claiming the current playback frame or inferred provenance",()=>{
 const item={...vehicleResult(),track_id:91,evidence_frame_indexes:[30],plate:{...vehicleResult().plate,used_enhancement:true}} as any;
 const view=render(<VideoTrackDetails item={item} metadata={{width:640,height:360,fps:30,frame_count:60,duration_seconds:2,timebase:"processed-cfr"}}/>);
 expect(screen.getByText("Trayectoria 91")).toBeInTheDocument();expect(screen.getByText(/Cuadro 30 · 1.00 s del video procesado/)).toBeInTheDocument();expect(screen.getByText(/Procedencia no informada/)).toBeInTheDocument();
 view.rerender(<VideoTrackDetails item={item} metadata={null}/>);expect(screen.getByText("Cuadro 30")).toBeInTheDocument();expect(screen.queryByText(/1.00 s/)).toBeNull();
});
