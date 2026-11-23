import { clampSeek, type Playback } from "./progressiveTypes";
export const clock = (us: number) => {
  const s = Math.floor(us / 1e6);
  return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
};
export function VideoTimeline({
  state,
  position,
  onSeek,
  disabled = false,
}: {
  disabled?: boolean;
  state: Playback;
  position: number;
  onSeek: (us: number) => void;
}) {
  const duration = Math.max(
    state.timeline.duration_us ?? state.available_until_us,
    1,
  );
  return (
    <div className="progressive-timeline">
      <label htmlFor={"timeline-" + state.job_id}>
        Posición del video · {clock(position)} de {clock(duration)}
        {state.timeline.duration_confirmed ? "" : " (estimado)"}
      </label>
      <input
        id={"timeline-" + state.job_id}
        disabled={disabled}
        type="range"
        min={0}
        max={duration}
        step={1000}
        value={Math.min(position, duration)}
        aria-valuetext={
          clock(position) +
          ". Analizado hasta " +
          clock(state.available_until_us)
        }
        onChange={(e) => onSeek(clampSeek(Number(e.target.value), state))}
        onKeyDown={(e) => {
          const target =
            e.key === "Home"
              ? 0
              : e.key === "End"
                ? (state.last_frame_start_us ?? 0)
                : e.key === "ArrowLeft"
                  ? position - 1_000_000
                  : e.key === "ArrowRight"
                    ? position + 1_000_000
                    : e.key === "PageDown"
                      ? position - 5_000_000
                      : e.key === "PageUp"
                        ? position + 5_000_000
                        : undefined;
          if (target !== undefined) {
            e.preventDefault();
            onSeek(clampSeek(target, state));
          }
        }}
      />
      <div className="progressive-coverage" aria-hidden="true">
        <span
          style={{
            width:
              Math.min(100, (state.available_until_us / duration) * 100) + "%",
          }}
        />
        <span />
      </div>
      <div className="progressive-limit">
        <span>Analizado hasta {clock(state.available_until_us)}</span>
        <span>El resto estará disponible al analizarse</span>
      </div>
    </div>
  );
}
