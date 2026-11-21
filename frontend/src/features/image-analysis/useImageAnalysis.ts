import { decodeImage } from "../../utils/decodeImage";
import { useEffect, useReducer, useRef } from "react";
import {
  ApiClient,
  ClientError,
  imageTimeouts,
} from "../../services/apiClient";
import type { DetectionResponse, VehicleResult } from "../../services/apiTypes";
import { ObjectUrlRegistry } from "../../hooks/useObjectUrl";
import { imageAnalysisReducer, initialState } from "./imageAnalysisReducer";
import { analysisMessage } from "./imageAnalysisMessages";
import { joinResults } from "./vehicleView";
type Operation = {
  generation: number;
  controller: AbortController;
  urls: ObjectUrlRegistry;
  client?: ApiClient;
  jobId?: string;
  sourceId?:string;
  terminal: boolean;
  expiry: number;
  timer?: ReturnType<typeof setTimeout>;
  busy: boolean;
  cancelled: boolean;
  mediaBusy: Set<string>;
};
export function useImageAnalysis(client?: ApiClient) {
  const [state, dispatch] = useReducer(imageAnalysisReducer, initialState);
  const stateRef = useRef(state);
  stateRef.current = state;
  const generation = useRef(0),
    opRef = useRef<Operation>();
  const active = (op: Operation) =>
    opRef.current === op && !op.controller.signal.aborted;
  const cancel = (op: Operation) => {
    if (op.jobId && !op.terminal && !op.cancelled) {
      op.cancelled = true;
      void op.client
        ?.cancelEnrichment(op.jobId, { timeoutMs: 5000 })
        .catch(() => {});
    }
  };
  const dispose = (op?: Operation) => {
    if (!op) return;
    op.controller.abort();
    clearTimeout(op.timer);
    op.urls.dispose();
    cancel(op);
  };
  const fresh = () => {
    dispose(opRef.current);
    const op: Operation = {
      generation: ++generation.current,
      controller: new AbortController(),
      urls: new ObjectUrlRegistry(generation.current),
      client,
      terminal: false,
      expiry: Infinity,
      busy: false,
      cancelled: false,
      mediaBusy: new Set(),
    };
    opRef.current = op;
    return op;
  };
  const expire = (op: Operation) => {
    if (!active(op)) return;
    dispose(op);
    dispatch({
      ...initialState,
      phase: "expired",
      generation: op.generation,
      message:
        "La evidencia temporal venció. Selecciona una imagen para analizar de nuevo.",
    });
  };
  const restrict = (op: Operation, ...dates: (string | undefined)[]) => {
    op.expiry = Math.min(
      op.expiry,
      ...dates.filter(Boolean).map((d) => Date.parse(d!)),
    );
    clearTimeout(op.timer);
    dispatch({ expiresAt: op.expiry });
    if (Number.isFinite(op.expiry)) {
      if (op.expiry <= Date.now()) expire(op);
      else op.timer = setTimeout(() => expire(op), op.expiry - Date.now());
    }
  };
  const handle = (op: Operation, error: unknown) => {
    if (!active(op)) return;
    if (error instanceof ClientError && error.status === 401) {
      dispose(op);
      dispatch({
        ...initialState,
        generation: op.generation,
        phase: "failed",
        message: analysisMessage(error),
      });
      return;
    }
    if (error instanceof ClientError && [404, 410].includes(error.status)) {
      expire(op);
      return;
    }
    dispatch({
      phase: op.jobId ? "interrupted" : "failed",
      message:
        !op.jobId &&
        op.sourceId &&
        error instanceof ClientError &&
        error.status === 0
          ? "No pudimos confirmar si se creó el trabajo. No se repetirá automáticamente; iniciar otro intento puede crear un trabajo adicional."
          : analysisMessage(error),
    });
  };
  const delay = (op: Operation, ms: number) =>
    new Promise<void>((resolve, reject) => {
      const abort = () => {
        clearTimeout(t);
        reject(new DOMException("Aborted", "AbortError"));
      };
      const t = setTimeout(() => {
        op.controller.signal.removeEventListener("abort", abort);
        resolve();
      }, ms);
      op.controller.signal.addEventListener("abort", abort, { once: true });
    });
  const observe = async (op: Operation, source: DetectionResponse) => {
    const deadline = performance.now() + imageTimeouts.cycle;
    while (active(op)) {
      const options = {
        signal: op.controller.signal,
        deadline,
        expiresAt: op.expiry,
        timeoutMs: imageTimeouts.status,
      };
      const job = await op.client!.enrichment(op.jobId!, options);
      if (!active(op)) return;
      if (
        job.enrichment_job_id !== op.jobId ||
        job.source.kind !== "image" ||
        job.source.source_id !== source.request_id
      )
        throw new Error("invalid_association");
      restrict(op, job.expires_at);
      if (!active(op)) return;
      dispatch({
        progress: job.progress_percent,
        enrichmentStage: job.status as
          | "queued"
          | "processing"
          | "completed"
          | "failed"
          | "cancelled",
      });
      if (job.status === "completed") {
        const items: VehicleResult[] = [];
        let page = 1,
          total: number | undefined;
        while (active(op)) {
          const next = await op.client!.enrichmentResults(op.jobId!, page, 50, {
            ...options,
            timeoutMs: imageTimeouts.evidence,
          });
          if (!active(op)) return;
          if (
            next.page !== page ||
            (total !== undefined && total !== next.total) ||
            (!next.items.length && items.length < next.total)
          )
            throw new Error("invalid_page");
          total = next.total;
          items.push(...next.items);
          if (items.length >= total) break;
          page++;
        }
        if (!active(op)) return;
        const results = joinResults(source, items),
          eligible = source.detections.filter((d) => d.enrichment_eligible);
        if (items.length !== eligible.length)
          throw new Error("incomplete_results");
        op.terminal = true;
        dispatch({
          results,
          phase: items.some(
            (r) =>
              r.attributes_status === "failed" || r.plate.status === "failed",
          )
            ? "partial"
            : "completed",
          progress: 100,
          message:
            "Análisis finalizado. Selecciona un vehículo para consultar su ficha.",
        });
        return;
      }
      if (["failed", "cancelled", "expired"].includes(job.status)) {
        op.terminal = true;
        if (job.status === "expired") expire(op);
        else
          dispatch({
            phase: job.status === "cancelled" ? "cancelled" : "failed",
            message:
              job.status === "cancelled"
                ? "El enriquecimiento se canceló. Puedes iniciarlo de nuevo."
                : "El enriquecimiento falló. Las detecciones siguen disponibles.",
          });
        return;
      }
      if (performance.now() + 1200 >= deadline)
        throw new ClientError(0, {
          code: "request_timeout",
          message: "timeout",
        });
      await delay(op, Math.min(1200, op.expiry - Date.now()));
    }
  };
  const enrich = async (op: Operation, source: DetectionResponse) => {
    op.jobId = undefined;
    op.terminal = false;
    op.cancelled = false;
    dispatch({
      jobId: undefined,
      progress: 0,
      results: {},
      enrichmentStage: "submitting",
    });
    const job = await op.client!.enrich("image", source.request_id, {
      signal: op.controller.signal,
      expiresAt: op.expiry,
    });
    op.jobId = job.enrichment_job_id;
    if (!active(op)) {
      cancel(op);
      return;
    }
    restrict(op, job.expires_at);
    if (!active(op)) return;
    dispatch({
      jobId: op.jobId,
      phase: "enriching",
      message: "Consultando atributos y placas…",
    });
    await observe(op, source);
  };
  const mediaFailed = (op: Operation, kind: "annotated" | "original") => {
    if (!active(op)) return;
    op.urls.release(stateRef.current[kind]);
    dispatch({ [kind]: "", [kind + "State"]: "failed" });
  };
  const loadMedia = async (
    op: Operation,
    source: DetectionResponse,
    kind: "annotated" | "original",
  ) => {
    if (!active(op) || op.mediaBusy.has(kind)) return;
    op.mediaBusy.add(kind);
    dispatch({ [kind + "State"]: "loading" });
    let url: string | undefined;
    try {
      const deadline = performance.now() + imageTimeouts.evidence;
      const options = {
        signal: op.controller.signal,
        expiresAt: op.expiry,
        deadline,
      };
      const blob =
        kind === "annotated"
          ? await op.client!.annotatedImage(source.request_id, options)
          : await op.client!.originalImage(source.original_image!.url, options);
      if (!active(op)) return;
      url = op.urls.create(blob);
      const size = await decodeImage(
        url,
        op.controller.signal,
        Math.min(deadline - performance.now(), op.expiry - Date.now()),
      );
      if (
        size.width !== source.image.width ||
        size.height !== source.image.height
      )
        throw new Error("inconsistent_image_dimensions");
      if (active(op)) {
        op.urls.release(stateRef.current[kind]);
        dispatch({ [kind]: url, [kind + "State"]: "ready" });
      }
    } catch (error) {
      if (url) op.urls.release(url);
      if (!active(op)) return;
      if (
        error instanceof ClientError &&
        [401, 404, 410].includes(error.status)
      )
        handle(op, error);
      else mediaFailed(op, kind);
    } finally {
      op.mediaBusy.delete(kind);
    }
  };
  const selectFile = (file?: File) => {
    const op = fresh();
    if (!file) {
      dispatch({ ...initialState, generation: op.generation });
      return;
    }
    if (!["image/jpeg", "image/png"].includes(file.type) || file.size === 0) {
      dispatch({
        ...initialState,
        generation: op.generation,
        phase: "failed",
        message: "Selecciona una imagen JPEG o PNG válida.",
      });
      return;
    }
    dispatch({
      ...initialState,
      generation: op.generation,
      file,
      preview: op.urls.create(file),
      phase: "ready",
    });
  };
  const analyze = async () => {
    const op = opRef.current,
      previous = stateRef.current;
    if (!op || op.busy || !op.client || !previous.file || !active(op)) return;
    op.busy = true;
    dispatch({
      phase: "detecting",
      message: "Detectando actores en la imagen…",
      results: {},
      selected: undefined,
    });
    try {
      const source = await op.client.uploadImage(previous.file, {
        signal: op.controller.signal,
      });
      if (!active(op)) return;
      restrict(
        op,
        source.source_expires_at,
        source.original_image?.expires_at,

      );
      if (!active(op)) return;
      op.sourceId=source.request_id;
      dispatch({
        response: source,
        selected: source.detections.find((d) => d.enrichment_eligible)
          ?.detection_id,
        phase: "enriching",
      });

      if (source.original_image) void loadMedia(op, source, "original");
      if (!source.original_image)
        dispatch({
          warning:
            "Este servicio no entrega el original canónico. La escena y los recortes no están disponibles.",
          originalState: "failed",
        });
      if (!source.detections.some((d) => d.enrichment_eligible === true)) {
        dispatch({
          phase: "empty",
          message: source.detections.length
            ? "No hay vehículos elegibles para enriquecimiento."
            : "No se detectaron actores en esta imagen.",
        });
        return;
      }
      await enrich(op, source);
    } catch (error) {
      handle(op, error);
    } finally {
      op.busy = false;
    }
  };
  const retryEnrichment = async () => {
    const op = opRef.current,
      source = stateRef.current.response;
    if (!op || !source || !active(op) || op.busy) return;
    op.busy = true;
    op.terminal = false;
    op.cancelled = false;
    dispatch({ phase: "enriching", message: "Iniciando enriquecimiento…" });
    try {
      await enrich(op, source);
    } catch (error) {
      handle(op, error);
    } finally {
      op.busy = false;
    }
  };
  const resume = async () => {
    const op = opRef.current,
      source = stateRef.current.response;
    if (!op || !source || !op.jobId || !active(op) || op.busy) return;
    op.busy = true;
    dispatch({
      phase: "enriching",
      message: "Reanudando consulta del mismo trabajo…",
    });
    try {
      await observe(op, source);
    } catch (error) {
      handle(op, error);
    } finally {
      op.busy = false;
    }
  };
  useEffect(
    () => () => {
      dispose(opRef.current);
      opRef.current = undefined;
    },
    [client],
  );
  return {
    state,
    selectFile,
    analyze,
    retryEnrichment,
    retryMedia: (kind: "annotated" | "original") => {
      const op = opRef.current,
        source = stateRef.current.response;
      if (op && source) return loadMedia(op, source, kind);
    },
    reportMediaFailure: (kind: "annotated" | "original") => {
      const op = opRef.current;
      if (op) mediaFailed(op, kind);
    },
    resume,
    selectDetection: (selected?: number) => {
      if(selected===undefined || stateRef.current.response?.detections.some(d=>d.detection_id===selected&&d.enrichment_eligible===true)) dispatch({selected});
    },
    sceneContext: (event:"hover"|"leave"|"focus"|"blur",id:number,sourceId:string) => {
      dispatch({contextEvent:event,detectionId:id,sourceId,generation:opRef.current?.generation??-1});
    },
    rejectEvidence: (error:unknown) => {const op=opRef.current;if(op)handle(op,error);},
    reset: () => {
      const op = fresh();
      dispatch({ ...initialState, generation: op.generation });
    },
  };
}
