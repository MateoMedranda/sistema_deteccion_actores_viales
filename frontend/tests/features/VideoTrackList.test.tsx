import {render,screen,fireEvent} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import {VideoTrackList} from "../../src/features/video-analysis/VideoTrackList";
import {vehicleResult} from "../fixtures/imageAnalysis";
it("shows real IDs, partial state and all page controls",()=>{
 const select=vi.fn(),load=vi.fn();render(<VideoTrackList page={{items:[{...vehicleResult(),track_id:60,attributes_status:"failed"}] as any,total:61,page:2,page_size:25}} onSelect={select} onPage={load}/>);
 fireEvent.click(screen.getByRole("button",{name:/Trayectoria 60/}));expect(select).toHaveBeenCalledWith(60);
 fireEvent.click(screen.getByRole("button",{name:"Siguiente"}));expect(load).toHaveBeenCalledWith(3);expect(screen.getByText(/Resultados parciales/)).toBeInTheDocument();
});
