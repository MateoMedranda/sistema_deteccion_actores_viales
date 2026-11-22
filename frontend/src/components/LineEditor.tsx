import { useEffect, useState } from "react";
import type { Point } from "../services/apiTypes";
import { normalizedPoint, validLine } from "../utils/lineCoordinates";
export function LineEditor({
  onLine,
  videoUrl,
  onClear,
  dimensions,
}: {
  onLine: (a: Point, b: Point) => void;
  videoUrl: string;
  onClear?: () => void;
  dimensions?: {width:number;height:number};
}) {
  const [aspect,setAspect]=useState(16/9);
  const [points, setPoints] = useState<Point[]>([]);
  const [dragging, setDragging] = useState<number | null>(null);
  useEffect(() => {
    setPoints([]);
    setDragging(null);
    onClear?.();
  }, [videoUrl]);
  const p = (e: React.PointerEvent<HTMLDivElement>) =>
    normalizedPoint(e.nativeEvent, e.currentTarget.getBoundingClientRect());
  const publish = (next: Point[]) => {
    setPoints(next);
    if (next.length === 2 && validLine(next[0], next[1]))
      onLine(next[0], next[1]);
    else onClear?.();
  };
  const down = (e: React.PointerEvent<HTMLDivElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    const next = [p(e), p(e)];
    setDragging(1);
    publish(next);
  };
  const move = (e: React.PointerEvent<HTMLDivElement>) => {
    if (dragging !== null) {
      const next = [...points];
      next[dragging] = p(e);
      publish(next);
    }
  };
  return (
    <section>
      <h2>Línea de conteo</h2>
      <p>
        En el primer fotograma, haga clic y arrastre. Arrastre los extremos
        amarillos para ajustar.
      </p>
      <div
        className="line-editor"
        style={{height:"auto",aspectRatio:dimensions?dimensions.width/dimensions.height:aspect}}
        onPointerDown={down}
        onPointerMove={move}
        onPointerUp={() => setDragging(null)}
        onPointerCancel={() => setDragging(null)}
      >
        <video muted preload="metadata" src={videoUrl} onLoadedMetadata={e=>{const v=e.currentTarget;if(v.videoWidth&&v.videoHeight)setAspect(v.videoWidth/v.videoHeight);}} />
        {points.length === 2 && (
          <svg viewBox="0 0 1 1" preserveAspectRatio="none">
            <line
              x1={points[0].x}
              y1={points[0].y}
              x2={points[1].x}
              y2={points[1].y}
            />
          </svg>
        )}
        {points.map((point, index) => (
          <button
            key={index}
            className="line-handle"
            style={{ left: `${point.x * 100}%`, top: `${point.y * 100}%` }}
            onPointerDown={(e) => {
              e.stopPropagation();
              onClear?.();
              e.currentTarget.parentElement?.setPointerCapture(e.pointerId);
              setDragging(index);
            }}
            onKeyDown={e=>{
              const changes:Record<string,[number,number]>={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]};
              const delta=changes[e.key];if(!delta)return;e.preventDefault();e.stopPropagation();
              const next=[...points],step=e.shiftKey?.05:.01;
              next[index]={x:Math.max(0,Math.min(1,point.x+delta[0]*step)),y:Math.max(0,Math.min(1,point.y+delta[1]*step))};publish(next);
            }}
            aria-label={`Extremo ${index + 1}`}
          />
        ))}
      </div>
      <button
        onClick={() => {
          setPoints([]);
          setDragging(null);
          onClear?.();
        }}
      >
        Borrar línea
      </button>
    </section>
  );
}
