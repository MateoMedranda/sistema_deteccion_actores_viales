import {it,expect} from 'vitest';import {classPresentation} from '../../../src/features/image-analysis/classPresentation';
it('recognizes all six checkpoint classes without labeling trucks as cars',()=>{
 for(const name of ['Car','Bus','Truck','Big Truck','Motorbike','Van'])expect(classPresentation(name).known,name).toBe(true);
 expect(classPresentation('Big Truck')).toMatchObject({key:'big_truck',label:'Camión pesado'});
 expect(classPresentation('Big Truck').color).not.toBe(classPresentation('Truck').color);
 expect(classPresentation('Van').label).toBe('Furgoneta');expect(classPresentation('Motorbike')).toEqual(classPresentation('motorcycle'));
});

it('treats inherited object properties as unknown classes',()=>{
 for(const name of ['constructor','__proto__','toString'])expect(classPresentation(name)).toMatchObject({key:name.toLowerCase(),known:false,color:'#64748B'});
});
