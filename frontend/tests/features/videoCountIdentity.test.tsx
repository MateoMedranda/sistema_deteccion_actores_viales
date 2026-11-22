import {render,screen,fireEvent} from "@testing-library/react";
import {it,expect,vi} from "vitest";
import {CountJobPanel} from "../../src/components/CountJobPanel";
it("does not submit a count when source or line is absent",()=>{
 const count=vi.fn();render(<CountJobPanel client={{count} as any}/>);
 fireEvent.click(screen.getByRole("button",{name:"Iniciar conteo"}));expect(count).not.toHaveBeenCalled();
 expect(screen.getByText("Completa video y línea primero.")).toBeVisible();
});
