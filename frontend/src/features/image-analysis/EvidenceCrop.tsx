import { useEffect, useState } from "react";
import type { Box } from "../../services/apiTypes";
import { extractCrop } from "../../utils/imageGeometry";
export function EvidenceCrop({
  original,
  box,
  label,
  identity,
  zoom,
}: {
  original: string;
  box?: Box;
  label: string;
  identity: string;
  zoom?: 1|2|4;
}) {
  const [image, setImage] = useState<{ identity: string; url: string }>(),
    [failed, setFailed] = useState(false);
  const coords = box
    ? [box.x_min, box.y_min, box.x_max, box.y_max].join(",")
    : "";
  useEffect(() => {
    setFailed(false);
    if (!original || !box) return;
    const controller = new AbortController();
    let url: string | undefined;
    void extractCrop(original, box, controller.signal)
      .then((blob) => {
        if (controller.signal.aborted) return;
        url = URL.createObjectURL(blob);
        setImage({ identity, url });
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => {
      controller.abort();
      if (url) URL.revokeObjectURL(url);
    };
  }, [original, coords, identity]);
  return (
    <figure
      className={
        "evidence " + (label.includes("placa") ? "plate-evidence" : "")
      }
    >
      <figcaption>{label}</figcaption>
      {image?.identity === identity && original && box ? (
        <img src={image.url} alt={label} style={zoom?{width:zoom*100+"%",maxWidth:"none",maxHeight:"none",height:"auto"}:undefined} />
      ) : (
        <div className="evidence-empty">
          {failed
            ? "No se pudo generar este recorte."
            : !original
              ? "Original no disponible"
              : !box
                ? "Sin localización disponible"
                : "Preparando recorte…"}
        </div>
      )}
    </figure>
  );
}
