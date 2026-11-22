import {render,screen} from "@testing-library/react";
import {it,expect} from "vitest";
import {VideoProgress} from "../../src/features/video-analysis/VideoProgress";
it("keeps encoding indeterminate after all frames and enrichment independent",()=>{
 render(<VideoProgress video={{status:"processing",processing_phase:"encoding",processed_frames:3,total_frames:3,frame_total_confirmed:true} as any}/>);
 expect(screen.getByText("Preparando video")).toBeVisible();expect(screen.getByText(/Enriquecimiento/)).toBeVisible();
 expect(screen.getAllByRole("progressbar")[0]).not.toHaveAttribute("aria-valuenow","100");
});

it("marks the frame bar complete only when the published video is available",()=>{
 const video={job_id:"v",status:"completed",processing_phase:"ready",processed_frames:10,total_frames:10,frame_total_confirmed:true} as any;
 render(<VideoProgress video={video}/>);
 expect(screen.getByRole("progressbar",{name:"Cuadros procesados"})).toHaveAttribute("aria-valuenow","100");
});
