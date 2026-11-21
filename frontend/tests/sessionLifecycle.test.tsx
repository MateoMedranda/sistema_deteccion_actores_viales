import { render, screen, fireEvent } from "@testing-library/react";
import { it, expect } from "vitest";
import App from "../src/App";
it("reset restores session defaults without persistent credentials", () => {
  render(<App />);
  fireEvent.click(screen.getByText("Configurar sesión"));
  fireEvent.change(screen.getByLabelText("URL backend"), {
    target: { value: "http://localhost:9999" },
  });
  fireEvent.change(screen.getByLabelText("API key"), {
    target: { value: "synthetic-secret" },
  });
  fireEvent.click(screen.getByText("Reiniciar demostración"));
  expect(screen.getByLabelText("API key")).toHaveValue("");
  expect(screen.getByLabelText("URL backend")).toHaveValue(
    "http://127.0.0.1:8000",
  );
});
