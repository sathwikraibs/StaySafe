import { useEffect, useRef, useState } from "react";
import { useChat } from "@/chat";
import { useI18n } from "@/i18n";
import { IconChat, IconClose, IconLock, IconShield } from "@/icons";
import { HELP_TEXTS, helpTopics, understand, setPrefill, announcePrefill, type HelpAction, type HelpTopic } from "@/helpBot";

type Button = HelpAction | { kind: "check"; what: "url" | "message"; value: string; label: string };
interface Bubble { from: "bot" | "me"; lines: string[]; buttons?: Button[]; topics?: boolean }

/**
 * StaySafe Helper: answers the most common questions straight away, day or night, in the
 * site's language. A pasted link or message is sent to the right check. "Talk to a person"
 * opens the live chat (which takes a message when nobody is online).
 */
export function HelpBot({ onClose, onNavigate, currentPath }: {
  onClose: () => void;
  onNavigate: (p: string) => void;
  currentPath: string;
}) {
  const { lang } = useI18n();
  const chat = useChat();
  const tx = HELP_TEXTS[lang] ?? HELP_TEXTS.en;
  const topics = helpTopics(lang);
  const [bubbles, setBubbles] = useState<Bubble[]>([{ from: "bot", lines: [tx.hello, tx.pick], topics: true }]);
  const [input, setInput] = useState("");
  const list = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLInputElement>(null);

  // new language: start again in that language
  useEffect(() => {
    setBubbles([{ from: "bot", lines: [tx.hello, tx.pick], topics: true }]);
  }, [lang]); // eslint-disable-line react-hooks/exhaustive-deps

  // Show each new answer from its start (long answers shouldn't open at their last line)
  useEffect(() => {
    const el = list.current;
    if (!el) return;
    const mine = el.querySelectorAll<HTMLElement>("[data-me]");
    const from = mine.length ? mine[mine.length - 1] : null;
    el.scrollTo({ top: from ? from.offsetTop - 12 : 0, behavior: "smooth" });
  }, [bubbles]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const say = (...add: Bubble[]) => setBubbles((b) => [...b, ...add]);

  function answer(topic: HelpTopic) {
    say({ from: "me", lines: [topic.q] },
      { from: "bot", lines: topic.a, buttons: [...(topic.actions ?? []), { kind: "person", label: tx.person }] });
  }

  function person() {
    const line = !chat.enabled ? tx.personNotReady : chat.status === "online" ? tx.personOnline : tx.personOffline;
    say({ from: "me", lines: [tx.person] }, { from: "bot", lines: [line], buttons: chat.enabled ? [{ kind: "person", label: tx.person }] : [] });
  }

  function press(b: Button) {
    if (b.kind === "go") {
      onNavigate(b.path);
      onClose();
    } else if (b.kind === "check") {
      setPrefill(b.what, b.value);
      const path = b.what === "url" ? "/scan-url" : "/scan-message";
      if (currentPath === path) announcePrefill();
      onNavigate(path);
      onClose();
    } else if (chat.enabled) {
      chat.openChat();
      onClose();
    } else {
      person();
    }
  }

  function submit(e: { preventDefault(): void }) {
    e.preventDefault();
    const text = input.trim();
    if (!text) return;
    setInput("");
    const r = understand(text, lang);
    const me: Bubble = { from: "me", lines: [text.length > 220 ? text.slice(0, 220) + "..." : text] };
    if (r.kind === "topic") {
      say(me, { from: "bot", lines: r.topic.a, buttons: [...(r.topic.actions ?? []), { kind: "person", label: tx.person }] });
    } else if (r.kind === "link") {
      say(me, { from: "bot", lines: [tx.linkSeen], buttons: [{ kind: "check", what: "url", value: r.link, label: tx.checkThisLink }] });
    } else if (r.kind === "message") {
      say(me, { from: "bot", lines: [tx.messageSeen], buttons: [{ kind: "check", what: "message", value: r.text, label: tx.checkThisMessage }] });
    } else {
      say(me, { from: "bot", lines: [tx.noMatch], topics: true });
    }
  }

  const last = bubbles.length - 1;

  return (
    <div
      role="dialog"
      aria-label={tx.title}
      className="fixed inset-x-2 bottom-[5.25rem] z-50 flex max-h-[min(78vh,640px)] flex-col overflow-hidden rounded-3xl bg-cream-50 shadow-warm-lg ring-1 ring-cream-200 animate-fade-up sm:inset-x-auto sm:right-4 sm:w-[390px] lg:bottom-6 lg:right-6"
      style={{ marginBottom: "env(safe-area-inset-bottom)" }}
    >
      {/* header */}
      <div className="flex items-center gap-3 bg-gradient-to-br from-sage-400 to-sage-600 px-4 py-3.5 text-cream-50">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-cream-50/20"><IconShield className="h-6 w-6" /></span>
        <div className="min-w-0 flex-1">
          <p className="font-heading text-base font-bold leading-tight">{tx.title}</p>
          <p className="font-body text-xs text-cream-50/85">{tx.subtitle}</p>
        </div>
        <button type="button" onClick={onClose} aria-label={tx.close} className="rounded-full p-2 transition-colors hover:bg-cream-50/15">
          <IconClose className="h-5 w-5" />
        </button>
      </div>
      <a href="tel:1930" className="block bg-rust-500 px-4 py-1.5 text-center font-body text-xs font-bold text-cream-50 hover:bg-rust-600">
        {tx.urgent}
      </a>

      {/* conversation */}
      <div ref={list} className="relative flex-1 space-y-3 overflow-y-auto px-3 py-4 scrollbar-warm">
        {bubbles.map((b, i) => (
          <div key={i} data-me={b.from === "me" ? "" : undefined} className={b.from === "me" ? "flex justify-end" : "flex justify-start"}>
            <div className={`max-w-[88%] ${b.from === "me" ? "rounded-2xl rounded-br-md bg-sage-500 px-3.5 py-2.5 text-cream-50" : "rounded-2xl rounded-bl-md bg-cream-100 px-3.5 py-2.5 text-ink-800"}`}>
              {b.lines.map((l, j) => (
                <p key={j} className={`whitespace-pre-wrap break-words font-body text-sm leading-relaxed ${j ? "mt-1.5" : ""}`}>{l}</p>
              ))}
              {b.buttons && b.buttons.length > 0 && (
                <div className="mt-2.5 flex flex-col gap-1.5">
                  {b.buttons.map((btn, k) => (
                    <button key={k} type="button" onClick={() => press(btn)}
                      className={`flex items-center justify-center gap-1.5 rounded-xl px-3 py-2 font-body text-sm font-bold transition-colors ${
                        btn.kind === "person" ? "bg-cream-50 text-sage-700 ring-1 ring-sage-300 hover:bg-sage-100" : "bg-sage-500 text-cream-50 hover:bg-sage-600"}`}>
                      {btn.kind === "person" && <IconChat className="h-4 w-4" />}
                      {btn.label}
                    </button>
                  ))}
                </div>
              )}
              {b.topics && (
                <div className="mt-2.5 flex flex-col gap-1.5">
                  {topics.map((tp) => (
                    <button key={tp.id} type="button" onClick={() => answer(tp)}
                      className="rounded-xl bg-cream-50 px-3 py-2 text-left font-body text-sm font-semibold text-ink-800 ring-1 ring-cream-200 transition-colors hover:bg-sage-100 hover:ring-sage-300">
                      {tp.q}
                    </button>
                  ))}
                  <button type="button" onClick={person}
                    className="flex items-center gap-1.5 rounded-xl bg-cream-50 px-3 py-2 text-left font-body text-sm font-bold text-sage-700 ring-1 ring-sage-300 hover:bg-sage-100">
                    <IconChat className="h-4 w-4" />{tx.person}
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        {!bubbles[last]?.topics && (
          <div className="flex justify-start">
            <button type="button" onClick={() => say({ from: "bot", lines: [tx.pick], topics: true })}
              className="rounded-full bg-cream-200 px-3 py-1.5 font-body text-xs font-bold text-ink-700 hover:bg-cream-300">
              {tx.more}
            </button>
          </div>
        )}
      </div>

      {/* typing box */}
      <form onSubmit={submit} className="border-t border-cream-200 bg-cream-50 p-2.5">
        <div className="flex items-center gap-2">
          <input ref={box} value={input} onChange={(e) => setInput(e.target.value)} placeholder={tx.placeholder}
            maxLength={5000}
            className="min-w-0 flex-1 rounded-2xl border-2 border-cream-200 bg-cream-100 px-3.5 py-2.5 font-body text-base text-ink-800 outline-none focus:border-sage-400" />
          <button type="submit" disabled={!input.trim()}
            className="shrink-0 rounded-2xl bg-sage-500 px-4 py-2.5 font-body text-sm font-bold text-cream-50 transition-colors hover:bg-sage-600 disabled:opacity-50">
            {tx.send}
          </button>
        </div>
        <p className="mt-1.5 flex items-center justify-center gap-1 font-body text-[11px] text-dustyblue-600">
          <IconLock className="h-3 w-3" />{tx.never}
        </p>
      </form>
    </div>
  );
}
