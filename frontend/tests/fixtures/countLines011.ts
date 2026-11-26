import fixtures from './countLines011.json';export default fixtures;
export const VEHICLE_CLASSES=['Car','Bus','Truck','Big Truck','Motorbike','Van'];
export const TEN_LINES=Array.from({length:10},(_,i)=>({line_id:'00000000-0000-4000-8000-'+String(i+1).padStart(12,'0'),name:'VÍA '+(i+1),color:fixtures.valid.find(e=>e.name==='confirmed_collection')!.data.default_colors![i],segment:{point_a:{x:.1,y:.1+i*.07},point_b:{x:.9,y:.1+i*.07}}}));
