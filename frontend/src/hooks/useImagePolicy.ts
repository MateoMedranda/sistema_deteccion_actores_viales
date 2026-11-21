import { useEffect, useState } from "react";
import { ApiClient } from "../services/apiClient";
import type { ImagePolicy } from "../services/apiTypes";
export function useImagePolicy(client?: ApiClient) {
  const [policy, setPolicy] = useState<ImagePolicy>(),
    [failed, setFailed] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    setPolicy(undefined);
    setFailed(false);
    if (!client) return;
    void client
      .imagePolicy({ signal: controller.signal })
      .then((value) => {
        if (!controller.signal.aborted) setPolicy(value);
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [client]);
  return { policy, failed };
}
