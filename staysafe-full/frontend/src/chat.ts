// "Talk to a person" everywhere on the site opens the StaySafe Helper (its AI answers, and a
// form that reaches the StaySafe team). No outside chat service is loaded.

export type HelperMode = "home" | "person";
const EVENT = "staysafe:helper";

/** Open the StaySafe Helper, optionally straight at "Talk to a person". */
export function openHelper(mode: HelperMode = "person"): void {
  try {
    window.dispatchEvent(new CustomEvent<HelperMode>(EVENT, { detail: mode }));
  } catch { /* ignore */ }
}

/** For the floating button: run `fn` whenever some page asks for the Helper. */
export function onHelperRequest(fn: (mode: HelperMode) => void): () => void {
  const handler = (e: Event) => fn(((e as CustomEvent<HelperMode>).detail) || "home");
  window.addEventListener(EVENT, handler);
  return () => window.removeEventListener(EVENT, handler);
}
