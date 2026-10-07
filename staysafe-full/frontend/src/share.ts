// "Share to StaySafe": things people share from other apps (a message, a link, a screenshot,
// a file) arrive through the service worker (public/sw.js) and open the right check, which
// then starts by itself. Also: the "Add StaySafe to your phone" button.
import { useEffect, useState } from "react";
import { setPrefill } from "@/helpBot";

const SHARE_CACHE = "staysafe-share";
const AUTORUN_KEY = "staysafe.autorun.v1";

export type SharedFileKind = "screenshot" | "file";
let pendingFile: { kind: SharedFileKind; file: File } | null = null;
let pendingQr: string | null = null;

/** Start the service worker (needed for sharing and for adding StaySafe to the phone). */
export function registerServiceWorker(): void {
  try {
    if (!("serviceWorker" in navigator) || !window.isSecureContext) return;
    if (location.hostname === "localhost" && !import.meta.env.PROD) return;
    const start = () => { navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => undefined); };
    if (document.readyState === "complete") start(); else window.addEventListener("load", start);
  } catch { /* sharing simply isn't offered */ }
}

const URL_ONLY = /^(https?:\/\/|www\.)\S+$/i;

/** The one link in the shared text, if the text is nothing but a link. */
export function loneLink(s: string): string | null {
  const v = s.trim();
  return v && URL_ONLY.test(v) && !/\s/.test(v) ? v : null;
}

/** Work out which check fits what was shared. Exported for tests. */
export function routeForShared(data: { title?: string; text?: string; url?: string }): { path: string; kind: "url" | "message"; value: string } | null {
  const text = (data.text || "").trim();
  const url = (data.url || "").trim();
  const title = (data.title || "").trim();
  if (!text && !url && !title) return null;
  // Browsers share a page as title = page name, text/url = the address
  const link = loneLink(text) || (!text ? loneLink(url) : null);
  if (link && (!url || url === link || loneLink(url))) return { path: "/scan-url", kind: "url", value: link };
  if (!text && url) return { path: "/scan-url", kind: "url", value: url };
  let message = text || title;
  if (url && !message.includes(url)) message = `${message}\n${url}`;
  return { path: "/scan-message", kind: "message", value: message.slice(0, 5000) };
}

/** Read a QR code in a picture on the phone itself, when the browser can (Android Chrome). */
async function qrInPicture(file: File): Promise<string | null> {
  try {
    const Detector = (window as unknown as { BarcodeDetector?: new (o: { formats: string[] }) => { detect: (s: ImageBitmap) => Promise<{ rawValue: string }[]> } }).BarcodeDetector;
    if (!Detector) return null;
    const bitmap = await createImageBitmap(file);
    const codes = await new Detector({ formats: ["qr_code"] }).detect(bitmap);
    bitmap.close?.();
    const v = codes.find((c) => c.rawValue && c.rawValue.trim())?.rawValue.trim();
    return v || null;
  } catch {
    return null;
  }
}

/** If StaySafe was opened by sharing something to it: which page to open (and get ready to check). */
export async function receiveShare(): Promise<string | null> {
  try {
    const params = new URLSearchParams(location.search);
    if (!params.has("shared")) return null;
    history.replaceState(null, "", location.pathname + location.hash);
    if (!("caches" in window)) return null;
    const cache = await caches.open(SHARE_CACHE);
    const res = await cache.match("/__share/data");
    if (!res) return null;
    const data = await res.json() as { title?: string; text?: string; url?: string; file?: { name: string; type: string } | null };
    const fileRes = data.file ? await cache.match("/__share/file") : undefined;
    await cache.delete("/__share/data");
    await cache.delete("/__share/file");

    if (fileRes && data.file) {
      const blob = await fileRes.blob();
      const type = data.file.type || blob.type || "";
      const file = new File([blob], data.file.name || (type.startsWith("image/") ? "shared-picture.jpg" : "shared-file"), { type });
      if (type.startsWith("image/") && type !== "image/svg+xml") {
        const qr = await qrInPicture(file);
        if (qr) { pendingQr = qr; return "/scan-qr"; }
        pendingFile = { kind: "screenshot", file };
        return "/scan-message";
      }
      pendingFile = { kind: "file", file };
      return "/scan-file";
    }

    const route = routeForShared(data);
    if (!route) return null;
    setPrefill(route.kind, route.value);
    try { sessionStorage.setItem(AUTORUN_KEY, route.kind); } catch { /* ignore */ }
    return route.path;
  } catch {
    return null;
  }
}

/** For the link and message pages: true once, when the shared text should be checked straight away. */
export function takeAutoRun(kind: "url" | "message"): boolean {
  try {
    if (sessionStorage.getItem(AUTORUN_KEY) !== kind) return false;
    sessionStorage.removeItem(AUTORUN_KEY);
    return true;
  } catch {
    return false;
  }
}

/** For the screenshot and file pages: the picture or file shared to StaySafe (given once). */
export function useSharedFile(kind: SharedFileKind, take: (file: File) => void): void {
  useEffect(() => {
    if (pendingFile && pendingFile.kind === kind) {
      const f = pendingFile.file;
      pendingFile = null;
      take(f);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kind]);
}

/** For the QR page: what the QR code in a shared picture says (given once). */
export function useSharedQr(take: (text: string) => void): void {
  useEffect(() => {
    if (pendingQr) {
      const v = pendingQr;
      pendingQr = null;
      take(v);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

// ---- "Add StaySafe to your phone" ----
interface InstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}
let installEvent: InstallPromptEvent | null = null;
const installListeners = new Set<() => void>();

export function listenForInstall(): void {
  try {
    window.addEventListener("beforeinstallprompt", (e) => {
      e.preventDefault();
      installEvent = e as InstallPromptEvent;
      installListeners.forEach((f) => f());
    });
    window.addEventListener("appinstalled", () => {
      installEvent = null;
      installListeners.forEach((f) => f());
    });
  } catch { /* ignore */ }
}

export function isInstalledApp(): boolean {
  try {
    return window.matchMedia("(display-mode: standalone)").matches ||
      (navigator as unknown as { standalone?: boolean }).standalone === true;
  } catch {
    return false;
  }
}

/** Whether the browser offers installing StaySafe, and a function that asks it to. */
export function useInstall(): { canInstall: boolean; install: () => Promise<boolean> } {
  const [, bump] = useState(0);
  useEffect(() => {
    const f = () => bump((n) => n + 1);
    installListeners.add(f);
    return () => { installListeners.delete(f); };
  }, []);
  return {
    canInstall: !!installEvent && !isInstalledApp(),
    install: async () => {
      const e = installEvent;
      if (!e) return false;
      try {
        await e.prompt();
        const choice = await e.userChoice;
        installEvent = null;
        installListeners.forEach((f) => f());
        return choice.outcome === "accepted";
      } catch {
        return false;
      }
    },
  };
}
