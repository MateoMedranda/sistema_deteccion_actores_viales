import {
  createFile,
  DataStream,
  MP4BoxBuffer,
  type Movie,
  type Sample,
} from "mp4box";
export type IndexedSample = { sample: Sample; displayIndex: number };
export type Mp4Timeline = {
  samples: IndexedSample[];
  byDisplay: IndexedSample[];
  config: VideoDecoderConfig;
  rotation: number;
};
export type ByteReader = (start: number, end: number) => Promise<ArrayBuffer>;
export function indexSamples(movie: Movie, samples: Sample[]): Mp4Timeline {
  const track = movie.videoTracks[0];
  if (
    !track ||
    !track.video ||
    !/^avc[13]\.[a-fA-F0-9]{6}$/.test(track.codec) ||
    movie.isFragmented ||
    samples.length === 0 ||
    samples.length > 100000
  )
    throw Error("media_not_supported");
  const edits = (track.edits ?? []).filter((e) => e.media_time !== -1);
  if (
    edits.length > 1 ||
    edits.some((e) => e.media_rate_integer !== 1 || e.media_rate_fraction !== 0)
  )
    throw Error("timeline_not_supported");
  const start = edits[0]?.media_time ?? Math.min(...samples.map((s) => s.cts));
  const duration = edits[0]
    ? (edits[0].segment_duration * track.timescale) / movie.timescale
    : Infinity;
  const visible = samples
    .filter((s) => s.cts >= start && s.cts < start + duration)
    .sort((a, b) => a.cts - b.cts);
  if (
    !visible.length ||
    visible.some((s, i) => i > 0 && s.cts <= visible[i - 1].cts)
  )
    throw Error("timeline_not_supported");
  const ranks = new Map(visible.map((s, i) => [s.number, i]));
  const indexed = samples.map((s) => {
    if (
      ![s.offset, s.size, s.cts, s.dts, s.duration, s.timescale].every(
        Number.isSafeInteger,
      ) ||
      s.offset < 0 ||
      s.size <= 0 ||
      s.size > 8 * 1024 * 1024 ||
      s.timescale <= 0
    )
      throw Error("sample_invalid");
    return { sample: s, displayIndex: ranks.get(s.number) ?? -1 };
  });
  const box = (
    visible[0].description as unknown as {
      avcC?: { write: (s: DataStream) => void };
    }
  ).avcC;
  if (!box) throw Error("codec_configuration_missing");
  const stream = new DataStream();
  box.write(stream);
  const description = stream.buffer.slice(8, stream.getPosition());
  const matrix = track.matrix.map((v) => (v | 0) / 65536);
  const a = matrix[0],
    b = matrix[1],
    c = matrix[3],
    d = matrix[4];
  // MP4 rotation matrices must be orthogonal. Arbitrary perspective transforms stay blocked.
  let rotation: number;
  if (a === 1 && b === 0 && c === 0 && d === 1) rotation = 0;
  else if (a === 0 && b === 1 && c === -1 && d === 0) rotation = 90;
  else if (a === -1 && b === 0 && c === 0 && d === -1) rotation = 180;
  else if (a === 0 && b === -1 && c === 1 && d === 0) rotation = 270;
  else throw Error("orientation_not_supported");
  const byNumber = new Map(indexed.map((s) => [s.sample.number, s]));
  return {
    samples: indexed,
    byDisplay: visible.map((s) => byNumber.get(s.number)!),
    rotation,
    config: {
      codec: track.codec,
      codedWidth: track.video.width,
      codedHeight: track.video.height,
      description,
      optimizeForLatency: false,
    },
  };
}
export async function readMp4(
  size: number,
  read: ByteReader,
  signal: AbortSignal,
): Promise<Mp4Timeline> {
  const file = createFile(false);
  let movie: Movie | undefined,
    error = false,
    offset = 0,
    total = 0;
  file.onReady = (info) => {
    movie = info;
  };
  file.onError = () => {
    error = true;
  };
  try {
    for (let n = 0; n < 256 && !movie; n++) {
      if (signal.aborted) throw new DOMException("Aborted", "AbortError");
      if (offset < 0 || offset >= size) throw Error("metadata_missing");
      const data = await read(offset, Math.min(size - 1, offset + 65535));
      total += data.byteLength;
      if (total > 16 * 1024 * 1024) throw Error("metadata_too_large");
      const next = file.appendBuffer(
        MP4BoxBuffer.fromArrayBuffer(data, offset),
      );
      if (error) throw Error("metadata_invalid");
      if (!Number.isSafeInteger(next) || next <= offset)
        throw Error("metadata_invalid");
      offset = next;
    }
    if (!movie) throw Error("metadata_missing");
    const timeline = indexSamples(
      movie,
      file.getTrackSamplesInfo(movie.videoTracks[0].id),
    );
    return timeline;
  } finally {
    file.stop();
  }
}
