import { addHistory, getClientId } from "./history";
import type { ScanHistoryItem } from "./types";

export const NETWORK_ERROR_MSG =
  "We couldn't connect right now. Please check your internet and try again.";

const TIMEOUT_MS = 170_000; // careful checks may wait for a free slot on a checking service; the server stops at 180 s

/** An error the server explained to us — safe to show to the user as-is. */
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number, wrongTool?: string, qrData?: string) {
    super(message);
    this.status = status;
    if (wrongTool) WRONG_TOOL.set(message, { tool: wrongTool, qrData });
  }
}

/** Server errors that mean "this belongs in another tool", by message (shown with a button). */
export const WRONG_TOOL = new Map<string, { tool: string; qrData?: string }>();

let lastInput: { text?: string; file?: File } = {};
/** Pages call this before checking, so "Open the right tool" can carry the input over. */
export function rememberInput(input: { text?: string; file?: File }): void { lastInput = input; }
export function getLastInput(): { text?: string; file?: File } { return lastInput; }

/** Turn any caught error into a friendly message for the page. */
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof DOMException && err.name === "AbortError") {
    return "This is taking longer than usual. Please try again in a moment.";
  }
  return NETWORK_ERROR_MSG;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  const headers = new Headers(init.headers);
  headers.set("X-Client-Id", getClientId());
  // The website language, so results and translations come back in the visitor's language
  headers.set("X-Lang", (typeof document !== "undefined" && document.documentElement.lang) || "en");

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
    const b = (body && typeof body === "object" ? body : {}) as { error?: unknown; wrong_tool?: unknown; qr_data?: unknown };
    const serverMsg = b.error ? String(b.error) : "";
    const fallback =
      res.status === 413 ? "That file is too big to upload." :
      res.status >= 500 ? "Something went wrong. Please try again." :
      `Request failed (${res.status}).`;
    throw new ApiError(serverMsg || fallback, res.status, b.wrong_tool ? String(b.wrong_tool) : undefined, b.qr_data ? String(b.qr_data) : undefined);
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
