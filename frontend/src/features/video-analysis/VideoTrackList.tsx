import type {EnrichmentPage} from "../../services/apiTypes";
import {classPresentation} from "../image-analysis/classPresentation";
export const plateStateLabel={read:"Placa leída",unreadable:"Placa ilegible",not_detected:"Placa no detectada",failed:"Lectura no disponible"};
export function VideoTrackList({page,selected,onSelect,onPage}:{page:EnrichmentPage;selected?:number|null;onSelect:(id:number)=>void;onPage:(page:number)=>void}){
 const totalPages=Math.max(1,Math.ceil(page.total/page.page_size));
 const partial=page.items.some(v=>v.attributes_status==="failed"||v.plate_status==="failed");
 return <section aria-label="Trayectorias del video"><div className="scene-heading"><h3>Vehículos analizados</h3><span>{page.total} trayectorias</span></div>
 <p className="muted">{partial?"Esta página contiene resultados parciales.":"Consulta las evidencias disponibles de cada trayectoria."}</p>
 {!page.items.length?<p>No hay resultados disponibles.</p>:<ul className="video-track-list">{page.items.map(item=><li key={item.track_id!}><button aria-pressed={selected===item.track_id} aria-controls="video-track-details" onClick={()=>onSelect(item.track_id!)}><i className="class-swatch" style={{backgroundColor:classPresentation(item.class_name).color}} aria-hidden="true"/><span><strong>Trayectoria {item.track_id}</strong><small>{classPresentation(item.class_name).label} · {plateStateLabel[item.plate_status]}</small></span><span aria-hidden="true">→</span></button></li>)}</ul>}
 {page.items.some(i=>i.attributes_status==="failed"||i.plate_status==="failed")&&<p role="status" className="notice">Resultados parciales en esta página: algunos datos no están disponibles.</p>}
 <nav aria-label="Páginas de trayectorias" className="video-pagination"><button disabled={page.page<=1} onClick={()=>onPage(page.page-1)}>Anterior</button><span>Página {page.page} de {totalPages}</span><button disabled={page.page>=totalPages} onClick={()=>onPage(page.page+1)}>Siguiente</button></nav></section>;
}
