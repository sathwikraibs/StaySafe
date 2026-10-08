// "Ask TrustLight AI" / "Talk to a person" everywhere on the site opens the TrustLight Helper
// (AI answers first, and a form that reaches the TrustLight team). No outside chat service is used.

export type HelperMode = "home" | "person";
export interface HelperRequest { mode: HelperMode; question?: string }
const EVENT = "staysafe:helper";

/** Open the TrustLight Helper; with `question`, the AI starts answering it straight away. */
export function openHelper(mode: HelperMode = "home", question?: string): void {
  try {
    window.dispatchEvent(new CustomEvent<HelperRequest>(EVENT, { detail: { mode, question } }));
  } catch { /* ignore */ }
}

/** For the floating button: run `fn` whenever some page asks for the Helper. */
export function onHelperRequest(fn: (req: HelperRequest) => void): () => void {
  const handler = (e: Event) => fn((e as CustomEvent<HelperRequest>).detail || { mode: "home" });
  window.addEventListener(EVENT, handler);
  return () => window.removeEventListener(EVENT, handler);
}
