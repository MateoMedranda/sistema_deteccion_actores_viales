import { useEffect, useRef, useState } from "react";
import { ClientError, type RequestOptions } from "../services/apiClient";
import type { SessionLifecycle } from "./useSessionLifecycle";
import { terminal } from "../services/apiTypes";
export function useLegacyJob({
  poll,
  cancel,
  idKey,
  lifecycle,
  onExpired,
}: {
  poll: (id: string, options: RequestOptions) => Promise<any>;
  cancel: (id: string) => Promise<unknown>;
  idKey: string;
  lifecycle?: SessionLifecycle;
  onExpired?: () => void;
}) {
  const [job, setJob] = useState<any>(),
    [message, setMessage] = useState("");
  const ref = useRef<{
    alive: boolean;
    job?: any;
    busy: boolean;
    controller: AbortController;
    generation: number;
    cancelledId?: string;
  }>({
    alive: true,
    busy: false,
    controller: new AbortController(),
    generation: 0,
  });
  const callbacks = useRef({ poll, cancel, onExpired });
  callbacks.current = { poll, cancel, onExpired };
  const cancelCurrent = () => {
    const value = ref.current.job;
    if (
      value?.[idKey] &&
      !terminal.has(value.status) &&
      ref.current.cancelledId !== value[idKey]
    ) {
      ref.current.cancelledId = value[idKey];
      return callbacks.current.cancel(value[idKey]);
    }
  };
  const invalidate = (
    reason = "La evidencia ya no está disponible. Inicia un nuevo proceso.",
  ) => {
    void Promise.resolve(cancelCurrent()).catch(() => {});
    ref.current.generation++;
    ref.current.controller.abort();
    ref.current.job = undefined;
    ref.current.busy = false;
    callbacks.current.onExpired?.();
    setJob(undefined);
    setMessage(reason);
  };
  const failure = (error: unknown) => {
    if (error instanceof ClientError && [401, 404, 410].includes(error.status))
      invalidate(
        error.status === 401
          ? "Acceso rechazado. Revisa la credencial de sesión."
          : undefined,
      );
    else setMessage("El trabajo ya no está disponible.");
  };
  useEffect(() => {
    ref.current.alive = true;
    const discard = () => {
      ref.current.alive = false;
      ref.current.generation++;
      ref.current.controller.abort();
      return cancelCurrent();
    };
    const unregister = lifecycle?.register(discard);
    return () => {
      unregister?.();
      void Promise.resolve(discard()).catch(() => {});
    };
  }, [lifecycle, idKey]);
  const requestOptions = (): RequestOptions => ({
    signal: ref.current.controller.signal,
    expiresAt: ref.current.job?.expires_at,
  });
  useEffect(() => {
    if (!job?.[idKey]) return;
    let active = true;
    const generation = ref.current.generation;
    const current = () =>
      active && ref.current.alive && generation === ref.current.generation;
    const expiry = job.expires_at
      ? setTimeout(
          () => {
            if (current())
              invalidate("La evidencia ha vencido. Inicia un nuevo proceso.");
          },
          Math.max(0, Date.parse(job.expires_at) - Date.now()),
        )
      : undefined;
    const timer = !terminal.has(job.status)
      ? setTimeout(async () => {
          try {
            const next = await callbacks.current.poll(
              job[idKey],
              requestOptions(),
            );
            if (current()) {
              ref.current.job = next;
              setJob(next);
            }
          } catch (error) {
            if (current()) {
              if (
                error instanceof ClientError &&
                [401, 404, 410].includes(error.status)
              )
                failure(error);
              else {
                ref.current.job = { ...job, status: "failed" };
                setJob({ ...job, status: "failed" });
                setMessage("El trabajo ya no está disponible.");
              }
            }
          }
        }, 1200)
      : undefined;
    return () => {
      active = false;
      if (timer) clearTimeout(timer);
      if (expiry) clearTimeout(expiry);
    };
  }, [job, idKey]);
  const run = async (create: (options: RequestOptions) => Promise<any>) => {
    if (
      ref.current.busy ||
      (ref.current.job && !terminal.has(ref.current.job.status))
    )
      return;
    ref.current.controller.abort();
    ref.current.controller = new AbortController();
    const generation = ++ref.current.generation;
    ref.current.job = undefined;
    setJob(undefined);
    ref.current.busy = true;
    try {
      const next = await create(requestOptions());
      if (!ref.current.alive || generation !== ref.current.generation) {
        if (next?.[idKey] && !terminal.has(next.status))
          void callbacks.current.cancel(next[idKey]).catch(() => {});
        return;
      }
      ref.current.job = next;
      setJob(next);
      setMessage("Trabajo iniciado.");
      return next;
    } catch (error) {
      if (ref.current.alive && generation === ref.current.generation)
        failure(error);
    } finally {
      if (generation === ref.current.generation) ref.current.busy = false;
    }
  };
  return {
    job,
    message,
    setMessage,
    run,
    alive: ref,
    requestOptions,
    invalidate,
    failure,
  };
}
