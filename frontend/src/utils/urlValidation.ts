export function normalizeApiUrl(value: string): string {
  const parsed = new URL(value.trim());
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") throw new Error("Use an HTTP(S) backend URL.");
  return parsed.href.replace(/\/$/, "");
}

