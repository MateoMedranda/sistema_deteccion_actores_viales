import { useEffect, useState } from "react";

export class ObjectUrlRegistry {
  private urls = new Set<string>();
  private closed = false;
  constructor(readonly generation = 0) {}
  create(blob: Blob): string {
    if (this.closed) throw new DOMException("Session discarded", "AbortError");
    const url = URL.createObjectURL(blob);
    this.urls.add(url);
    return url;
  }
  release(url?: string) {
    if (url && this.urls.delete(url)) URL.revokeObjectURL(url);
  }
  clear() {
    for (const url of this.urls) URL.revokeObjectURL(url);
    this.urls.clear();
  }
  dispose() {
    this.closed = true;
    this.clear();
  }
}
export function useObjectUrl(blob?: Blob): string {
  const [url, setUrl] = useState("");
  useEffect(() => {
    if (!blob) {
      setUrl("");
      return;
    }
    const next = URL.createObjectURL(blob);
    setUrl(next);
    return () => URL.revokeObjectURL(next);
  }, [blob]);
  return url;
}
