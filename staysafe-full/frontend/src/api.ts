import { addHistory, getClientId } from "./history";
import type { ScanHistoryItem } from "./types";

export const NETWORK_ERROR_MSG =
  "We couldn't reach the StaySafe server. Please check your internet and try again. " +
  "(If the site has been idle, the server can take up to a minute to wake up.)";

const TIMEOUT_MS = 90_000; // Render free tier can take ~1 minute to wake up

/** An error the server explained to us — safe to show to the user as-is. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/** Turn any caught error into a friendly message for the page. */
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof DOMException && err.name === "AbortError") {
    return "The server took too long to respond. Please try again in a moment.";
  }
  return NETWORK_ERROR_MSG;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  const headers = new Headers(init.headers);
  headers.set("X-Client-Id", getClientId());

  let res: Response;
  try {
    res = await fetch(path, { ...init, headers, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }

  let body: unknown = null;
  try {
    body = await res.json();
  } catch { /* not JSON */ }

  if (!res.ok) {
    const serverMsg = body && typeof body === "object" && "error" in body ? String((body as { error: unknown }).error) : "";
    const fallback =
      res.status === 413 ? "That file is too big to upload." :
      res.status >= 500 ? "Something went wrong on the server. Please try again." :
      `Request failed (${res.status}).`;
    throw new ApiError(serverMsg || fallback, res.status);
  }

  // Save every completed scan in this browser's history for the dashboard
  if (body && typeof body === "object" && "history_entry" in body) {
    const entry = (body as { history_entry?: ScanHistoryItem }).history_entry;
    if (entry) addHistory(entry);
  }
  return body as T;
}

export function apiPostJSON<T>(path: string, body: Record<string, unknown>): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function apiPostForm<T>(path: string, formData: FormData): Promise<T> {
  return request<T>(path, { method: "POST", body: formData });
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}
