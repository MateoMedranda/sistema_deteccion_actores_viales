import { render, fireEvent, screen } from "@testing-library/react";
import { it, expect, vi } from "vitest";
import { LineEditor } from "../src/components/LineEditor";
it("clears the parent configuration and resets points when the source changes", () => {
  vi.stubGlobal("PointerEvent", MouseEvent);
  const onLine = vi.fn(),
    onClear = vi.fn();
  const { container, rerender } = render(
    <LineEditor videoUrl="blob:a" onLine={onLine} onClear={onClear} />,
  );
  const editor = container.querySelector(".line-editor") as HTMLElement;
  editor.getBoundingClientRect = () =>
    ({ left: 0, top: 0, width: 100, height: 100 }) as DOMRect;
  editor.setPointerCapture = vi.fn();
  fireEvent.pointerDown(editor, { clientX: 10, clientY: 20 });
  fireEvent.pointerMove(editor, { clientX: 80, clientY: 70 });
  fireEvent.pointerUp(editor);
  expect(onLine).toHaveBeenCalled();
  fireEvent.click(screen.getByText("Borrar línea"));
  expect(onClear).toHaveBeenCalled();
  fireEvent.pointerDown(editor, { clientX: 10, clientY: 20 });
  fireEvent.pointerMove(editor, { clientX: 80, clientY: 70 });
  rerender(<LineEditor videoUrl="blob:b" onLine={onLine} onClear={onClear} />);
  expect(container.querySelectorAll(".line-handle")).toHaveLength(0);
  vi.unstubAllGlobals();
});
