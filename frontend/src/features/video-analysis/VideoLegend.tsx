import {classPresentation} from "../image-analysis/classPresentation";
export function VideoLegend({classes,eligible}:{classes:string[]|null;eligible:number|null}){
 return <aside className="video-legend"><h3>Clases detectadas</h3>{classes===null?<p>Clases todavía no confirmadas</p>:classes.length===0?<p>Sin clases detectadas</p>:<><ul>{classes.map(name=><li key={name} style={{borderColor:classPresentation(name).color}}>{classPresentation(name).label}</li>)}</ul><p>El enriquecimiento se aplica a vehículos elegibles según la configuración del servicio; otras detecciones pueden aparecer sin ficha.</p></>}{eligible===0&&<p>No se encontraron vehículos elegibles para enriquecimiento.</p>}</aside>;
}
