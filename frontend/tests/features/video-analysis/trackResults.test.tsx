import { useState } from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { ProgressiveTrackList, ProgressiveTrackResults } from "../../../src/features/video-analysis/ProgressiveTrackResults";
import type { Track } from "../../../src/features/video-analysis/progressiveTypes";
import type { ApiClient } from "../../../src/services/apiClient";
const uuid = (i: number) =>
  "00000000-0000-4000-8000-" + String(i).padStart(12, "0");
const track = (i: number, revision = 1): Track => ({
  job_id: "job",
  generation: uuid(99),
  unit_id: uuid(i),
  track_id: i,
  discovery_ordinal: i,
  class_name: "car",
  first_seen_us: 0,
  last_seen_us: 100000,
  state: "ready",
  final: false,
  result_revision: revision,
  evidence_revision: 1,
  attributes: {
    status: "completed",
    items: [
      {
        name: "color",
        value: "value-" + revision + "-" + i,
        confidence: 0.9,
        evidence_id: uuid(i),
      },
    ],
    error_code: null,
  },
  plate: {
    status: "read",
    text: "SYN" + i,
    ocr_confidence: 0.9,
    used_enhancement: false,
    policy_id: "video-legacy-v1",
    evidence_ids: [uuid(i)],
    error_code: null,
  },
  evidence: [
    {
      evidence_id: uuid(i),
      frame_index: i,
      time_us: i * 100000,
      vehicle_bbox: { x_min: 0, y_min: 0, x_max: 10, y_max: 10 },
      provisional: true,
      vehicle_url:
        "/api/v1/video-jobs/job/playback/tracks/" +
        i +
        "/evidence/" +
        uuid(i) +
        "/vehicle",
      plate_url: null,
      expires_at: new Date(Date.now() + 60000).toISOString(),
    },
  ],
  expires_at: new Date(Date.now() + 60000).toISOString(),
});
it("binds ten identities to their own crops and keeps selection across result revisions", async () => {
  const blob = vi.fn().mockResolvedValue(new Blob(["synthetic"]));
  const client = { blob } as unknown as ApiClient;
  function Example({ revision }: { revision: number }) {
    const [selected, choose] = useState<number>();
    return (
      <>
        <p>Posición de reproducción: 0:00</p>
        <ProgressiveTrackList observations={Array.from({length:10},(_,i)=>track(i+1,revision))} selected={selected} onSelect={choose}/>
        <ProgressiveTrackResults
          client={client}
          tracks={Array.from({ length: 10 }, (_, i) => track(i + 1, revision))}
          selected={selected}
          onSelect={choose}
          onUnavailable={() => {}}
        />
      </>
    );
  }
  const view = render(<Example revision={1} />);
  for (let i = 1; i <= 10; i++) {
    fireEvent.click(
      screen.getByRole("button", { name: new RegExp("^#" + i + " ·") }),
    );
    expect(
      screen.getByRole("heading", { name: "Vehículo #" + i }),
    ).toBeInTheDocument();
    expect(screen.getByText("SYN" + i, { exact: true })).toBeInTheDocument();
    await waitFor(() =>
      expect(blob).toHaveBeenLastCalledWith(
        expect.stringContaining("/tracks/" + i + "/evidence/"),
        expect.anything(),
      ),
    );
  }
  view.rerender(<Example revision={2} />);
  expect(
    screen.getByRole("heading", { name: "Vehículo #10" }),
  ).toBeInTheDocument();
  expect(screen.getByText(/value-2-10/)).toBeInTheDocument();
  expect(
    screen.getByText("Posición de reproducción: 0:00"),
  ).toBeInTheDocument();
});

it.each([
 ["failed","failed","failed","No se pudo completar la consulta"],
 ["not_applicable","not_applicable","not_applicable","Enriquecimiento no aplicable"],
 ["partial","completed","failed","Datos parciales"],
 ["queued","pending","pending","Consulta en cola"],
])("distinguishes %s from pending and unavailable branches",(state,attributesStatus,plateStatus,label)=>{
 const value=track(1);value.state=state;value.final=state!=="queued";value.attributes={status:attributesStatus,items:[],error_code:null};value.plate={...value.plate,status:plateStatus,text:null};value.evidence=[];
 render(<ProgressiveTrackResults client={{} as ApiClient} tracks={[value]} selected={1} onSelect={()=>{}} onUnavailable={()=>{}}/>);
 expect(screen.getByRole("status")).toHaveTextContent(label);
 expect(screen.queryByText("Datos finales")).not.toBeInTheDocument();
});
