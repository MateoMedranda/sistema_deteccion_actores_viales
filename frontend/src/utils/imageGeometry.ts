import type { Box } from "../services/apiTypes";
export function vehicleCrop(box: Box, w: number, h: number): Box | undefined {
  if (
    ![box.x_min, box.y_min, box.x_max, box.y_max, w, h].every(
      Number.isFinite,
    ) ||
    w <= 0 ||
    h <= 0
  )
    return;
  const b = {
    x_min: Math.max(0, Math.trunc(box.x_min)),
    y_min: Math.max(0, Math.trunc(box.y_min)),
    x_max: Math.min(w, Math.trunc(box.x_max)),
    y_max: Math.min(h, Math.trunc(box.y_max)),
  };
  return b.x_min < b.x_max && b.y_min < b.y_max ? b : undefined;
}
export function projectBox(b: Box, w: number, h: number) {
  const box = vehicleCrop(b, w, h);
  if (!box) return;
  return {
    left: (box.x_min / w) * 100 + "%",
    top: (box.y_min / h) * 100 + "%",
    width: ((box.x_max - box.x_min) / w) * 100 + "%",
    height: ((box.y_max - box.y_min) / h) * 100 + "%",
  };
}
export function plateCrop(v: Box, p?: Box): Box | undefined {
  if (
    !p ||
    ![p.x_min, p.y_min, p.x_max, p.y_max].every(
      (n) => Number.isFinite(n) && n >= 0 && n <= 1,
    ) ||
    p.x_min >= p.x_max ||
    p.y_min >= p.y_max
  )
    return;
  const w = v.x_max - v.x_min,
    h = v.y_max - v.y_min;
  // Undo only IEEE-754 roundoff from integer / dimension normalization.
  const pixel = (ratio: number, size: number) => {
    const value = ratio * size,
      nearest = Math.round(value);
    return Math.trunc(
      Math.abs(value - nearest) <= Number.EPSILON * Math.max(1, size) * 2
        ? nearest
        : value,
    );
  };
  return vehicleCrop(
    {
      x_min: v.x_min + pixel(p.x_min, w),
      y_min: v.y_min + pixel(p.y_min, h),
      x_max: v.x_min + pixel(p.x_max, w),
      y_max: v.y_min + pixel(p.y_max, h),
    },
    v.x_max,
    v.y_max,
  );
}
export async function extractCrop(
  url: string,
  box: Box,
  signal: AbortSignal,
): Promise<Blob> {
  const img = new Image();
  img.src = url;
  await img.decode();
  if (signal.aborted) throw new DOMException("Aborted", "AbortError");
  const b = vehicleCrop(box, img.naturalWidth, img.naturalHeight);
  if (!b) throw new Error("invalid_crop");
  const canvas = document.createElement("canvas");
  canvas.width = b.x_max - b.x_min;
  canvas.height = b.y_max - b.y_min;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("canvas_unavailable");
  ctx.drawImage(
    img,
    b.x_min,
    b.y_min,
    canvas.width,
    canvas.height,
    0,
    0,
    canvas.width,
    canvas.height,
  );
  return new Promise((resolve, reject) =>
    canvas.toBlob((blob) => {
      canvas.width = canvas.height = 0;
      if (signal.aborted) reject(new DOMException("Aborted", "AbortError"));
      else if (blob) resolve(blob);
      else reject(new Error("crop_failed"));
    }, "image/png"),
  );
}
