import { readMp4, type ByteReader, type Mp4Timeline } from "./mp4Timeline";
export class SourceDecoder {
  timeline?: Mp4Timeline;
  private decoder?: VideoDecoder;
  private epoch = 0;
  private closed = false;
  private cursor = 0;
  private floor = 0;
  private ended = false;
  private frames = new Map<number, VideoFrame>();
  private posters = new Map<number, VideoFrame>();
  private blocks = new Map<number, Uint8Array>();
  get encodedBytes() {
    return [...this.blocks.values()].reduce((n, b) => n + b.byteLength, 0);
  }
  get posterBytes() {
    return [...this.posters.values()].reduce(
      (n, f) => n + f.codedWidth * f.codedHeight * 4,
      0,
    );
  }
  private async bytes(start: number, end: number) {
    const result = new Uint8Array(end - start + 1),
      blockSize = 1024 * 1024;
    for (
      let number = Math.floor(start / blockSize);
      number <= Math.floor(end / blockSize);
      number++
    ) {
      let block = this.blocks.get(number);
      if (!block) {
        const offset = number * blockSize;
        block = new Uint8Array(
          await this.read(
            offset,
            Math.min(this.size - 1, offset + blockSize - 1),
          ),
        );
        if (this.closed || this.signal.aborted)
          throw new DOMException("Aborted", "AbortError");
      }
      this.blocks.delete(number);
      this.blocks.set(number, block);
      while (this.encodedBytes > 8 * 1024 * 1024)
        this.blocks.delete(this.blocks.keys().next().value!);
      const left = Math.max(start, number * blockSize),
        right = Math.min(end, number * blockSize + block.byteLength - 1);
      result.set(
        block.subarray(
          left - number * blockSize,
          right - number * blockSize + 1,
        ),
        left - start,
      );
    }
    return result.buffer;
  }
  private remember(index: number, frame: VideoFrame) {
    this.posters.get(index)?.close();
    this.posters.delete(index);
    this.posters.set(index, frame.clone());
    while (this.posters.size > 4 || this.posterBytes > 16 * 1024 * 1024) {
      const key = this.posters.keys().next().value!;
      this.posters.get(key)!.close();
      this.posters.delete(key);
    }
  }
  private filling?: Promise<void>;
  private failure?: Error;
  constructor(
    private read: ByteReader,
    private size: number,
    private signal: AbortSignal,
  ) {}
  async initialize() {
    if (typeof VideoDecoder !== "function") throw Error("decoder_unavailable");
    this.timeline = await readMp4(
      this.size,
      (a, b) => this.bytes(a, b),
      this.signal,
    );
    const support = await VideoDecoder.isConfigSupported(this.timeline.config);
    if (!support.supported) throw Error("decoder_unavailable");
    this.reset(0);
  }
  private reset(index: number) {
    this.epoch++;
    if (this.decoder && this.decoder.state !== "closed") this.decoder.close();
    for (const f of this.frames.values()) f.close();
    this.frames.clear();
    this.failure = undefined;
    this.floor = index;
    this.ended = false;
    const samples = this.timeline!.samples,
      target = this.timeline!.byDisplay[index];
    if (!target) throw Error("frame_not_available");
    let position = samples.indexOf(target);
    while (position > 0 && !samples[position].sample.is_sync) position--;
    if (!samples[position].sample.is_sync) throw Error("keyframe_missing");
    this.cursor = position;
    const epoch = this.epoch;
    this.decoder = new VideoDecoder({
      output: (frame) => {
        const id = frame.timestamp / 1000;
        if (
          this.closed ||
          epoch !== this.epoch ||
          !Number.isInteger(id) ||
          id < this.floor ||
          id < 0
        ) {
          frame.close();
          return;
        }
        if (this.frames.size >= 28) {
          frame.close();
          this.failure = Error("decoded_queue_overflow");
          return;
        }
        this.frames.get(id)?.close();
        this.frames.set(id, frame);
      },
      error: () => {
        this.failure = Error("decode_failed");
      },
    });
    this.decoder.configure(this.timeline!.config);
  }
  async seek(index: number) {
    if (this.closed || !this.timeline) return;
    const previous = this.frames.get(this.floor);
    if (previous) this.remember(this.floor, previous);
    const cached = this.posters.get(index)?.clone(),
      old = this.filling;
    this.reset(index);
    const epoch = this.epoch;
    if (cached) {
      this.frames.set(index, cached);
      return;
    }
    if (old) await old.catch(() => {});
    if (epoch === this.epoch) await this.fill(index);
  }

  frame(index: number) {
    return this.frames.get(index);
  }
  consume(index: number) {
    this.floor = index;
    for (const [id, frame] of this.frames)
      if (id < index) {
        frame.close();
        this.frames.delete(id);
      }
  }
  async fill(index: number) {
    if (this.closed || this.signal.aborted)
      throw new DOMException("Aborted", "AbortError");
    if (this.failure) throw this.failure;
    if (this.filling) return this.filling;
    if (!this.timeline || !this.decoder) throw Error("decoder_not_ready");
    if (index < this.floor || index > this.floor + 60) {
      this.reset(index);
    }
    const epoch = this.epoch,
      decoder = this.decoder,
      timeline = this.timeline;
    const operation = (async () => {
      while (
        !this.closed &&
        !this.signal.aborted &&
        epoch === this.epoch &&
        !this.ended &&
        this.frames.size < 8
      ) {
        if (this.failure) throw this.failure;
        if (decoder.decodeQueueSize >= 4) {
          await new Promise<void>((resolve) => setTimeout(resolve, 2));
          continue;
        }
        if (this.cursor >= timeline.samples.length) {
          await decoder.flush();
          this.ended = true;
          break;
        }
        const first = timeline.samples[this.cursor].sample;
        let last = this.cursor;
        while (last + 1 < timeline.samples.length && last - this.cursor < 15) {
          const next = timeline.samples[last + 1].sample;
          if (
            next.offset < first.offset ||
            next.offset + next.size - first.offset > 1024 * 1024
          )
            break;
          last++;
        }
        const end =
          timeline.samples[last].sample.offset +
          timeline.samples[last].sample.size -
          1;
        const data = new Uint8Array(await this.bytes(first.offset, end));
        if (this.closed || epoch !== this.epoch || this.signal.aborted) return;
        while (this.cursor <= last && decoder.decodeQueueSize < 4) {
          const item = timeline.samples[this.cursor++],
            sample = item.sample;
          decoder.decode(
            new EncodedVideoChunk({
              type: sample.is_sync ? "key" : "delta",
              timestamp:
                item.displayIndex < 0 ? -1000 : item.displayIndex * 1000,
              duration: 1000,
              data: data.subarray(
                sample.offset - first.offset,
                sample.offset - first.offset + sample.size,
              ),
            }),
          );
        }
        // Yield so decoded VideoFrames can reach the bounded queue.
        await new Promise<void>((resolve) => setTimeout(resolve, 0));
        if (this.frames.has(index) && this.frames.size >= 8) break;
      }
    })();
    this.filling = operation.finally(() => {
      this.filling = undefined;
    });
    return this.filling;
  }
  close() {
    for (const f of this.posters.values()) f.close();
    this.posters.clear();
    this.blocks.clear();
    this.closed = true;
    this.epoch++;
    if (this.decoder && this.decoder.state !== "closed") this.decoder.close();
    for (const f of this.frames.values()) f.close();
    this.frames.clear();
  }
}
