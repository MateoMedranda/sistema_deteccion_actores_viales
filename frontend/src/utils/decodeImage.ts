export async function decodeImage(
  url: string,
  signal: AbortSignal,
  timeoutMs = 30000,
): Promise<{ width: number; height: number }> {
  const img = new Image();
  let timer: ReturnType<typeof setTimeout> | undefined;
  let abort: () => void = () => {};
  try {
    if (signal.aborted) throw new DOMException("Aborted", "AbortError");
    const stopped = new Promise<never>((_, reject) => {
      abort = () => reject(new DOMException("Aborted", "AbortError"));
      signal.addEventListener("abort", abort, { once: true });
      timer = setTimeout(
        () => reject(new Error("image_decode_timeout")),
        Math.max(0, timeoutMs),
      );
    });
    img.src = url;
    await Promise.race([img.decode(), stopped]);
    return { width: img.naturalWidth, height: img.naturalHeight };
  } finally {
    if (timer) clearTimeout(timer);
    signal.removeEventListener("abort", abort);
    img.src = "";
  }
}
