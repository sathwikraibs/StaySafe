/**
 * Keeps the installed app and open tabs on the newest TrustLight.
 *
 * Every build writes its version into the code and into /version.json. The app asks for
 * /version.json when it opens, whenever it comes back to the screen, and every 10 minutes.
 * - New version found while the app was in the background: it reloads itself (auto update).
 * - Found while someone is using it, or the reload didn't bring the new version, or a part of
 *   the page can no longer be downloaded: a full-screen "Update now" window that must be used.
 */
import { useEffect, useState } from "react";

declare const __APP_VERSION__: string;
export const APP_VERSION: string = typeof __APP_VERSION__ !== "undefined" ? __APP_VERSION__ : "dev";

const TRIED_KEY = "trustlight.update.tried";
const CHECK_EVERY_MS = 10 * 60 * 1000;

let needed = false;
const listeners = new Set<(v: boolean) => void>();

/** Show the update window (used when a page part fails to download after an update). */
export function markUpdateNeeded(): void {
  if (needed) return;
  needed = true;
  listeners.forEach((fn) => fn(true));
}

async function latestVersion(): Promise<string | null> {
  try {
    const r = await fetch(`/version.json?t=${Date.now()}`, { cache: "no-store" });
    if (!r.ok) return null;
    const data = (await r.json()) as { version?: unknown };
    return typeof data.version === "string" && data.version ? data.version : null;
  } catch {
    return null; // offline or the server is busy: try again later
  }
}

/** Reload into the newest version (with a fresh address so no stored copy is used). */
export function updateNow(version?: string): void {
  try { sessionStorage.setItem(TRIED_KEY, version || "?"); } catch { /* ignore */ }
  const url = new URL(window.location.href);
  url.searchParams.set("v", (version || String(Date.now())).slice(0, 12));
  window.location.replace(url.toString());
}

async function check(autoReload: boolean): Promise<void> {
  if (APP_VERSION === "dev" || needed) return;
  const latest = await latestVersion();
  if (!latest || latest === APP_VERSION) {
    try { sessionStorage.removeItem(TRIED_KEY); } catch { /* ignore */ }
    return;
  }
  let alreadyTried = false;
  try { alreadyTried = sessionStorage.getItem(TRIED_KEY) === latest; } catch { /* ignore */ }
  if (autoReload && !alreadyTried) updateNow(latest);   // the quiet way first
  else markUpdateNeeded();                               // the quiet way didn't work, or they're busy
}

/** True when the update window must be shown. */
export function useUpdateNeeded(): boolean {
  const [show, setShow] = useState(needed);
  useEffect(() => {
    listeners.add(setShow);
    void check(true);                                    // just opened: safe to reload at once
    const onVisible = () => { if (document.visibilityState === "visible") void check(true); };
    document.addEventListener("visibilitychange", onVisible);
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void check(false);
    }, CHECK_EVERY_MS);
    return () => {
      listeners.delete(setShow);
      document.removeEventListener("visibilitychange", onVisible);
      window.clearInterval(timer);
    };
  }, []);
  return show;
}

/** Wraps a page download so a missing old file (after an update) opens the update window. */
export function orUpdate<T>(load: () => Promise<T>): () => Promise<T> {
  return () => load().catch(async (err: unknown) => {
    const latest = await latestVersion();
    if (latest && latest !== APP_VERSION && APP_VERSION !== "dev") {
      markUpdateNeeded();
      return new Promise<T>(() => { /* the update window takes over */ });
    }
    throw err;   // not an update (e.g. offline): let the page handle it as before
  });
}
