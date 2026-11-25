import type {ReactNode} from 'react';
import './vehicleDetails.css';
/** Shared semantic shell; image and video own their respective data contracts. */
export function VehicleDetailsCard({children,id,className=''}:{children:ReactNode;id?:string;className?:string}){
 return <aside id={id} className={'vehicle-details '+className} aria-label="Ficha del vehículo">{children}</aside>;
}
