import schema from './countLinesSchema.json';
import type {CountLine} from './useProgressiveCount';
export type LineWrite={line_id:string;name:string;color:string;segment:CountLine};
export type LineConfig=LineWrite&{geometry_revision:number;origin:'user'|'legacy_import'};
export type Collection={job_id:string;generation:string;protocol:'video-count-lines-v1';policy_version:'finite-center-both-v1';mode:'both';revision:number;admitted_count:number;limits:{max_active_lines:number;max_admitted_lines:number;max_name_graphemes:60;max_name_utf8_bytes:2048;max_name_codepoints:1024};default_colors:string[];lines:LineConfig[];legacy_import:{status:'none'|'offered'|'imported';line_id:string|null};expires_at:string};
export type CountValue={line_id:string;geometry_revision:number;status:'pending'|'ready'|'unavailable';result_scope:'building'|'partial'|'final';covered_until_us:number;valid_until_us:number;total:number|null;error_code:string|null};
export type CountSnapshot={job_id:string;generation:string;protocol:'video-count-lines-v1';policy_version:'finite-center-both-v1';revision:number;at_us:number;available_until_us:number;analysis_state:'queued'|'analyzing'|'complete'|'partial_failed';lines:CountValue[];expires_at:string};
const defs=(schema as any).$defs;
function valid(s:any,v:any):boolean{
 if(s.$ref)return valid(defs[s.$ref.split('/').pop()],v);
 if(s.anyOf)return s.anyOf.some((p:any)=>valid(p,v));
 if('const'in s&&v!==s.const||s.enum&&!s.enum.includes(v))return false;
 if(s.type==='null')return v===null;
 if(s.type==='string')return typeof v==='string'&&(!s.minLength||[...v].length>=s.minLength)&&(!s.maxLength||[...v].length<=s.maxLength)&&(!s.pattern||new RegExp(s.pattern).test(v))&&(!s.format||(s.format==='uuid'?/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i.test(v):/^\d{4}-\d\d-\d\dT/.test(v)&&Number.isFinite(Date.parse(v))));
 if(s.type==='integer'||s.type==='number')return typeof v==='number'&&Number.isFinite(v)&&(s.type!=='integer'||Number.isSafeInteger(v))&&(s.minimum===undefined||v>=s.minimum)&&(s.maximum===undefined||v<=s.maximum);
 if(s.type==='boolean')return typeof v==='boolean';
 if(s.type==='array')return Array.isArray(v)&&(s.minItems===undefined||v.length>=s.minItems)&&(s.maxItems===undefined||v.length<=s.maxItems)&&(!s.uniqueItems||new Set(v.map(x=>JSON.stringify(x))).size===v.length)&&v.every(x=>valid(s.items,x));
 if(s.type==='object')return !!v&&typeof v==='object'&&!Array.isArray(v)&&(s.required??[]).every((k:string)=>k in v)&&Object.keys(v).every(k=>k in s.properties?valid(s.properties[k],v[k]):s.additionalProperties!==false);
 return true;
}
export function normalizeName(value:string){
 if(/[\p{Cc}\p{Cs}\u202a-\u202e\u2066-\u2069]/u.test(value))throw Error('Nombre no válido.');
 const name=value.normalize('NFC').trim().replace(/\s+/gu,' '),Segmenter=(Intl as any).Segmenter;

 if(!name||[...name].length>1024||new TextEncoder().encode(name).length>2048||(Segmenter&&[...new Segmenter('es',{granularity:'grapheme'}).segment(name)].length>60)||!/[\p{L}\p{N}\p{S}\p{P}]/u.test(name))throw Error('Usa un nombre de hasta 60 caracteres visibles.');
 return name;
}
export function parseCountLines<T>(name:string,value:unknown):T{
 if(!defs[name]||!valid(defs[name],value))throw Error('invalid_count_lines_response');
 const v=value as any;
 if(v.lines&&new Set(v.lines.map((l:any)=>l.line_id)).size!==v.lines.length)throw Error('count_line_id_invalid');
 const objects=v.lines??((name==='LineWrite'||name==='LineConfig'||name==='CountValue')?[v]:[]);
 if((name==='CollectionWrite'||name==='Collection')&&(new Set(objects.map((l:any)=>normalizeName(l.name).toLocaleLowerCase())).size!==objects.length||new Set(objects.map((l:any)=>l.color.toUpperCase())).size!==objects.length))throw Error('count_collection_invalid');
 for(const l of objects){
  if(l.segment&&l.segment.point_a.x===l.segment.point_b.x&&l.segment.point_a.y===l.segment.point_b.y)throw Error('count_segment_invalid');
  if(l.name!==undefined&&normalizeName(l.name)!==l.name)throw Error('count_name_invalid');
  if(l.status==='ready'&&(l.total===null||(name==='CountSnapshot'&&!(v.at_us<l.valid_until_us&&l.valid_until_us<=Math.min(l.covered_until_us,v.available_until_us)))))throw Error('count_state_invalid');
  if(l.status&&l.status!=='ready'&&(l.total!==null||(name==='CountSnapshot'&&l.valid_until_us!==v.at_us)))throw Error('count_state_invalid');
 }
 if(name==='Collection'&&(new Set(v.default_colors).size!==32||new Set(v.lines.map((l:any)=>l.name.toLocaleLowerCase())).size!==v.lines.length||new Set(v.lines.map((l:any)=>l.color.toUpperCase())).size!==v.lines.length))throw Error('count_collection_invalid');
 return v;
}
export const lineWrites=(lines:LineWrite[])=>lines.map(({line_id,name,color,segment})=>({line_id,name:normalizeName(name),color:color.toUpperCase(),segment}));
export const sameLines=(a:LineWrite[],b:LineWrite[])=>JSON.stringify([...lineWrites(a)].sort((x,y)=>x.line_id.localeCompare(y.line_id)))===JSON.stringify([...lineWrites(b)].sort((x,y)=>x.line_id.localeCompare(y.line_id)));
