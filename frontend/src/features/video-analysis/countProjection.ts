import type {Collection,CountSnapshot,CountValue} from './countLinesContracts';
export function projectCount(collection:Collection,snapshot:CountSnapshot|undefined,lineId:string,position:number):CountValue|undefined{
 if(!snapshot||snapshot.generation!==collection.generation||snapshot.job_id!==collection.job_id||snapshot.revision!==collection.revision)return;
 const line=collection.lines.find(l=>l.line_id===lineId),value=snapshot.lines.find(l=>l.line_id===lineId&&l.geometry_revision===line?.geometry_revision);
 if(value?.status==='ready'&&(position<snapshot.at_us||position>=value.valid_until_us))return;
 return value;
}
