import { terminal, type Playback } from "./progressiveTypes";
export function playbackDecision(
  state: Playback,
  position: number,
  intent: boolean,
  annotations: boolean,
  ended = false,
) {
  if (!intent) return "pause";
  if (ended) return "ended";
  const margin = state.available_until_us - position;
  return annotations &&
    (margin >= state.buffer_seconds * 1e6 || (terminal(state) && margin > 0))
    ? "play"
    : "wait";
}
