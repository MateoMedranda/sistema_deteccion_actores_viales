import { renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ObjectUrlRegistry, useObjectUrl } from "../../src/hooks/useObjectUrl";

describe("temporary resources", () => {
  it("revokes resources and refuses allocation after invalidation", () => {
    const create = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:owned");
    const revoke = vi.spyOn(URL, "revokeObjectURL");
    const resources = new ObjectUrlRegistry(2);
    expect(resources.create(new Blob(["source"]))).toBe("blob:owned");
    resources.dispose();
    resources.dispose();
    expect(revoke).toHaveBeenCalledTimes(1);
    expect(() => resources.create(new Blob())).toThrow();
    expect(create).toHaveBeenCalledTimes(1);
  });

  it("releases previews on replacement and unmount", () => {
    let next = 0;
    vi.spyOn(URL, "createObjectURL").mockImplementation(() => "blob:" + ++next);
    const revoke = vi.spyOn(URL, "revokeObjectURL");
    const first = new Blob(["A"]),
      second = new Blob(["B"]);
    const { result, rerender, unmount } = renderHook(
      ({ blob }) => useObjectUrl(blob),
      { initialProps: { blob: first } },
    );
    expect(result.current).toBe("blob:1");
    rerender({ blob: second });
    expect(revoke).toHaveBeenCalledWith("blob:1");
    expect(result.current).toBe("blob:2");
    unmount();
    expect(revoke).toHaveBeenCalledWith("blob:2");
  });
});
