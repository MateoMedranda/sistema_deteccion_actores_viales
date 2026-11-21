import { useEffect, useMemo } from "react";
export type SessionLifecycle = {
  register: (cancel: () => Promise<unknown> | void) => () => void;
};
export function useSessionLifecycle(identity: unknown): SessionLifecycle {
  const registry = useMemo(
    () => new Set<() => Promise<unknown> | void>(),
    [identity],
  );
  useEffect(
    () => () => {
      const callbacks = [...registry];
      registry.clear();
      void Promise.allSettled(
        callbacks.map((cancel) => Promise.resolve().then(cancel)),
      );
    },
    [registry],
  );
  return useMemo(
    () => ({
      register: (cancel: () => Promise<unknown> | void) => {
        registry.add(cancel);
        return () => {
          registry.delete(cancel);
        };
      },
    }),
    [registry],
  );
}
