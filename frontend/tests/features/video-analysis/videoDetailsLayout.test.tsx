import {render,screen,fireEvent} from '@testing-library/react';
import {describe,it,expect,vi} from 'vitest';
import {VehicleDetailsCard} from '../../../src/components/vehicle-details/VehicleDetailsCard';
describe('shared vehicle details presentation',()=>{
 it('keeps semantic card and close action available with complete content',()=>{
  const close=vi.fn();render(<VehicleDetailsCard><h3>Vehículo #9</h3><p>Recorte del vehículo</p><h4>Atributos</h4><h4>Placa</h4><button onClick={close}>Cerrar ficha del vehículo</button></VehicleDetailsCard>);
  expect(screen.getByRole('complementary',{name:'Ficha del vehículo'})).toHaveClass('vehicle-details');
  fireEvent.click(screen.getByRole('button'));expect(close).toHaveBeenCalledOnce();
 });
});
