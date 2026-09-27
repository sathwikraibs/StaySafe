// Live chat (tawk.to) — loaded once, controlled from React.
//
// We hide tawk.to's own floating bubble and use our own StaySafe-styled
// "Need help?" button instead, so it sits in the right place on phones
// (above the bottom menu) and matches the site's look.
//
// Set these in Vercel → Settings → Environment Variables, then redeploy:
//   VITE_TAWK_PROPERTY_ID  and  VITE_TAWK_WIDGET_ID
// (from the tawk.to embed code: https://embed.tawk.to/PROPERTY_ID/WIDGET_ID)
import { useEffect, useState } from "react";

type ChatStatus = "online" | "away" | "offline" | "unknown";

interface TawkApi {
  onLoad?: () => void;
  onStatusChange?: (status: string) => void;
  onChatMaximized?: () => void;
  onChatMinimized?: () => void;
  onChatStarted?: () => void;
  onChatEnded?: () => void;
  onUnreadCountChanged?: (count: number) => void;
  hideWidget?: () => void;
  showWidget?: () => void;
  maximize?: () => void;
  minimize?: () => void;
  getStatus?: () => string;
  customStyle?: Record<string, unknown>;
}

declare global {
  interface Window {
    Tawk_API?: TawkApi;
    Tawk_LoadStart?: Date;
  }
}

const PROPERTY_ID = import.meta.env.VITE_TAWK_PROPERTY_ID;
const WIDGET_ID = import.meta.env.VITE_TAWK_WIDGET_ID;

export const CHAT_ENABLED = Boolean(PROPERTY_ID && WIDGET_ID);
const USED_KEY = "staysafe.chatUsed.v1";

/** Has this visitor chatted before? Then load chat early so replies reach them. */
export function hasChattedBefore(): boolean {
  try { return localStorage.getItem(USED_KEY) === "1"; } catch { return false; }
}

interface ChatState {
  ready: boolean;
  open: boolean;
  status: ChatStatus;
  unread: number;
}

let state: ChatState = { ready: false, open: false, status: "unknown", unread: 0 };
let requested = false;
let openWhenReady = false;
const listeners = new Set<(s: ChatState) => void>();

function setState(patch: Partial<ChatState>) {
  state = { ...state, ...patch };
  listeners.forEach((l) => l(state));
}

function normaliseStatus(s: string | undefined): ChatStatus {
  return s === "online" || s === "away" || s === "offline" ? s : "unknown";
}

/** Inject the tawk.to script (once). Safe to call many times. */
export function loadChat(): void {
  if (!CHAT_ENABLED || requested || typeof window === "undefined") return;
  requested = true;

  const api: TawkApi = (window.Tawk_API = window.Tawk_API || {});
  window.Tawk_LoadStart = new Date();
  api.customStyle = { zIndex: 1000 };

  api.onLoad = () => {
    api.hideWidget?.(); // we show our own button instead
    setState({ ready: true, status: normaliseStatus(api.getStatus?.()) });
    if (openWhenReady) {
      openWhenReady = false;
      openChat();
    }
  };
  api.onStatusChange = (s) => setState({ status: normaliseStatus(s) });
  api.onChatMaximized = () => setState({ open: true, unread: 0 });
  api.onChatMinimized = () => {
    api.hideWidget?.();
    setState({ open: false });
  };
  api.onUnreadCountChanged = (count) => setState({ unread: state.open ? 0 : count });
  api.onChatStarted = () => {
    try { localStorage.setItem(USED_KEY, "1"); } catch { /* ignore */ }
  };

  const script = document.createElement("script");
  script.async = true;
  script.src = `https://embed.tawk.to/${PROPERTY_ID}/${WIDGET_ID}`;
  script.charset = "UTF-8";
  script.setAttribute("crossorigin", "*");
  document.body.appendChild(script);
}

/** Open the chat window (loads it first if needed). */
export function openChat(): void {
  if (!CHAT_ENABLED) return;
  if (!state.ready) {
    openWhenReady = true;
    loadChat();
    return;
  }
  const api = window.Tawk_API;
  api?.showWidget?.();
  api?.maximize?.();
  setState({ open: true, unread: 0 });
}

/** React hook: current chat state + an `open` function. */
export function useChat() {
  const [snapshot, setSnapshot] = useState<ChatState>(state);
  useEffect(() => {
    listeners.add(setSnapshot);
    setSnapshot(state);
    return () => {
      listeners.delete(setSnapshot);
    };
  }, []);
  return { enabled: CHAT_ENABLED, ...snapshot, openChat };
}

export function statusText(status: ChatStatus): string {
  if (status === "online") return "We're online now";
  if (status === "away") return "We'll reply shortly";
  if (status === "offline") return "Leave a message — we'll reply soon";
  return "Usually replies within a few hours";
}
