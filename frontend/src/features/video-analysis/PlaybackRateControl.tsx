import {PLAYBACK_RATES} from './playbackClock';
export function PlaybackRateControl({value,onChange}:{value:number;onChange:(rate:number)=>void}){
 return <label className="playback-rate">Velocidad de reproducción<select aria-label="Velocidad de reproducción" value={value} onChange={e=>onChange(Number(e.target.value))}>{PLAYBACK_RATES.map(rate=><option key={rate} value={rate}>{rate}×</option>)}</select><small>Solo reproducción · el análisis continúa a su ritmo.</small></label>;
}
