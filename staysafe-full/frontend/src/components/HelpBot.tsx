import { useEffect, useRef, useState } from "react";
import type { HelperMode } from "@/chat";
import { useI18n } from "@/i18n";
import { IconChat, IconClose, IconLock, IconShield } from "@/icons";
import { HELP_TEXTS, TOOL_TEXTS, TOOL_PATHS, helpTopics, understand, setPrefill, setStartTab, TOOL_TABS, announcePrefill, looksLikePastedMessage, type HelpAction, type HelpTopic, type ToolId } from "@/helpBot";
import { apiGet, apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";

type Button = HelpAction
  | { kind: "tool"; path: string; label: string; tab?: [string, string] }
  | { kind: "check"; what: "url" | "message"; value: string; label: string }
  | { kind: "form"; label: string };
interface Bubble {
  from: "bot" | "me"; lines: string[]; buttons?: Button[]; topics?: boolean; ai?: boolean; typing?: boolean;
  team?: boolean;        // show the small "Still need a person? Write to our team" line under it
  langPick?: boolean;    // show language buttons (the AI wasn't sure which language to answer in)
  aiAnyway?: string;     // a question we answered with a tool button: it can still go to the AI
}
type Turn = { role: "user" | "assistant"; text: string };
interface AiAnswer { reply: string; urgent: boolean; actions: string[]; ask_language?: boolean }

/** Languages someone can pick when the AI isn't sure (Tulu and Kannada look alike). */
const LANG_CHOICES: [string, string][] = [["kn", "ಕನ್ನಡ"], ["tcy", "ತುಳು"], ["en", "English"], ["hi", "हिन्दी"]];

/**
 * StaySafe Helper, AI first: people type their problem in any language and StaySafe AI answers
 * straight away. Common questions are one tap. Writing to the team is offered only as the next
 * step, after the AI has answered (or when the AI can't be reached).
 */
export function HelpBot({ onClose, onNavigate, currentPath, startWith = "home", question }: {
  startWith?: HelperMode;
  question?: string;
  onClose: () => void;
  onNavigate: (p: string) => void;
  currentPath: string;
}) {
  const { lang, ts, t } = useI18n();
  const tx = HELP_TEXTS[lang] ?? HELP_TEXTS.en;
  const tt = TOOL_TEXTS[lang] ?? TOOL_TEXTS.en;
  const TOOL_LABEL: Record<ToolId, string> = {
    message: "nav.message", link: "nav.link", email: "nav.email", qr: "nav.qr", file: "nav.file",
    password: "nav.password", leak: "nav.password", network: "nav.network",
  };
  const topics = helpTopics(lang);
  const [bubbles, setBubbles] = useState<Bubble[]>([{ from: "bot", lines: [tx.hello] }]);
  const [input, setInput] = useState("");
  const list = useRef<HTMLDivElement>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const [formReady, setFormReady] = useState<boolean | null>(null);
  const [aiReady, setAiReady] = useState<boolean | null>(null);
  const [form, setForm] = useState(false);
  const [lastTopic, setLastTopic] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [thinking, setThinking] = useState(false);
  const [replyLang, setReplyLang] = useState<string>("");
  const pending = useRef<string>("");          // last question, to answer again in a picked language
  const started = useRef(false);

  // What's available (asked once; the answers never name any service)
  useEffect(() => {
    apiGet<{ available: boolean }>(`${API_BASE}/api/contact/status`)
      .then((r) => setFormReady(!!r.available)).catch(() => setFormReady(false));
    apiGet<{ available: boolean }>(`${API_BASE}/api/assistant/status`)
      .then((r) => setAiReady(!!r.available)).catch(() => setAiReady(false));
  }, []);

  // On computers, the typing box is ready at once (on phones we don't pop the keyboard up uninvited)
  useEffect(() => {
    if (window.matchMedia?.("(pointer: fine)").matches) box.current?.focus();
  }, []);

  // Opened with a question (from the home page box) or straight at "Talk to a person"
  useEffect(() => {
    if (started.current || aiReady === null || formReady === null) return;
    started.current = true;
    if (question) ask(question);
    else if (startWith === "person") person();
  }, [aiReady, formReady]); // eslint-disable-line react-hooks/exhaustive-deps

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

  /** Buttons the AI suggested, as real buttons on our pages. */
  function aiButtons(actions: string[], asked = ""): Button[] {
    const link = asked.match(/\b(?:https?:\/\/|www\.)\S+|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|in|net|org|xyz|top|info|co|app|site|online|link|live|shop|club|io|me|cc|ly)\b(?:\/\S*)?/i)?.[0];
    const map: Record<string, Button> = {
      incident: { kind: "go", path: "/incident", label: tx.actIncident },
      check_message: looksLikePastedMessage(asked)
        ? { kind: "check", what: "message", value: asked, label: tx.actCheckMessage }
        : { kind: "go", path: "/scan-message", label: tx.actCheckMessage },
      check_link: link
        ? { kind: "check", what: "url", value: link, label: tx.actCheckLink }
        : { kind: "go", path: "/scan-url", label: tx.actCheckLink },
      check_password: { kind: "go", path: "/check-password", label: tx.actPassword },
      library: { kind: "go", path: "/scam-library", label: tx.actLibrary },
    };
    return actions.filter((a) => map[a]).map((a) => map[a]);
  }

  /** Ready answer (used when the AI can't be reached). */
  function readyAnswer(topic: HelpTopic) {
    setLastTopic(topic.id);
    say({ from: "bot", lines: topic.a, buttons: topic.actions ?? [], team: true });
  }

  /** Ask StaySafe AI. If it can't answer, fall back to the ready answers. */
  async function askAssistant(text: string, fallback: () => void, pickedLang?: string) {
    setThinking(true);
    pending.current = text;
    say({ from: "bot", lines: [tx.typing], typing: true });
    try {
      const started = Date.now();
      const r = await apiPostJSON<AiAnswer>(`${API_BASE}/api/assistant`, {
        message: text, lang, reply_lang: pickedLang || replyLang || undefined, history: turns.slice(-6),
      });
      const rest = 1800 - (Date.now() - started);   // a careful answer shouldn't pop up instantly
      if (rest > 0) await new Promise((ok) => setTimeout(ok, rest));
      setBubbles((b) => [...b.filter((x) => !x.typing),
        { from: "bot", lines: r.reply.split(/\n+/).filter(Boolean), ai: true, buttons: aiButtons(r.actions, text),
          team: !r.ask_language, langPick: !!r.ask_language }]);
      setTurns((t) => [...t, { role: "user" as const, text }, { role: "assistant" as const, text: r.reply }].slice(-8));
    } catch {
      setBubbles((b) => b.filter((x) => !x.typing));
      fallback();
    } finally {
      setThinking(false);
    }
  }

  /** Anything typed or tapped goes here: links and pasted messages go to the right check, the rest to the AI. */
  function ask(text: string, topic?: HelpTopic) {
    if (thinking) return;
    const r = understand(text, lang);
    say({ from: "me", lines: [text.length > 220 ? text.slice(0, 220) + "..." : text] });
    if (r.kind === "link") {
      say({ from: "bot", lines: [tx.linkSeen], buttons: [{ kind: "check", what: "url", value: r.link, label: tx.checkThisLink }], team: true });
      return;
    }
    if (r.kind === "message") {
      // A pasted SMS/WhatsApp: the full check is one tap away, and the AI explains it meanwhile
      const check: Bubble = { from: "bot", lines: [tx.messageSeen], buttons: [{ kind: "check", what: "message", value: r.text, label: tx.checkThisMessage }] };
      if (aiReady) { say(check); void askAssistant(text, () => undefined); } else say({ ...check, team: true });
      return;
    }
    if (r.kind === "tool" && !topic) {
      // "check this mail / message / QR": the tool does it, so open it (no AI needed)
      say({
        from: "bot",
        lines: [tt.intro, ...r.tools.map((id) => tt.hint[id])],
        buttons: r.tools.map((id) => ({ kind: "tool" as const, path: TOOL_PATHS[id], label: t(TOOL_LABEL[id]), tab: id === "message" && /screen ?shot|ಸ್ಕ್ರೀನ್|स्क्रीन|photo|image|picture|pic\b/i.test(text) ? ["message", "shot"] as [string, string] : TOOL_TABS[id] })),
        aiAnyway: aiReady ? text : undefined,
        team: !aiReady,
      });
      return;
    }
    // Only a sure keyword match may stand in for the AI; otherwise we say we didn't understand
    const known = topic ?? (r.kind === "topic" && r.strong ? r.topic : undefined);
    if (known) setLastTopic(known.id);
    const fallback = () => (known ? readyAnswer(known) : say({ from: "bot", lines: [tx.noMatch], topics: true, team: true }));
    if (aiReady) void askAssistant(text, fallback);
    else fallback();
  }

  /** Someone wants a real person: the short form, which reaches the team's phone at once. */
  function person() {
    const me: Bubble = { from: "me", lines: [tx.writeTeam] };
    if (formReady) say(me, { from: "bot", lines: [tx.formIntro], buttons: [{ kind: "form", label: tx.writeToUs }] });
    else say(me, { from: "bot", lines: [tx.personNotReady] });
  }

  function pickLanguage(code: string) {
    setReplyLang(code);
    const name = LANG_CHOICES.find(([c]) => c === code)?.[1] ?? code;
    say({ from: "me", lines: [name] });
    if (pending.current) void askAssistant(pending.current, () => say({ from: "bot", lines: [tx.noMatch], topics: true }), code);
  }

  function sent(ref: string, lost: string) {
    setForm(false);
    say({ from: "bot", lines: [tx.sent.replace("{ref}", ref), ...(lost === "yes" ? [tx.sentUrgent] : [])] });
  }

  function press(b: Button) {
    if (b.kind === "go") {
      onNavigate(b.path);
      onClose();
    } else if (b.kind === "tool") {
      if (b.tab) setStartTab(b.tab[0], b.tab[1]);
      if (currentPath === b.path) announcePrefill();
      onNavigate(b.path);
      onClose();
    } else if (b.kind === "check") {
      setPrefill(b.what, b.value);
      const path = b.what === "url" ? "/scan-url" : "/scan-message";
      if (currentPath === path) announcePrefill();
      onNavigate(path);
      onClose();
    } else if (b.kind === "form") {
      setForm(true);
    } else {
      person();
    }
  }

  function submit(e: { preventDefault(): void }) {
    e.preventDefault();
    const text = input.trim();
    if (!text || thinking) return;
    setInput("");
    ask(text);
  }

  const noAnswerYet = bubbles.length === 1;
  const teamOnly = aiReady === false;   // AI can't be reached: offer the team up front

  return (
    <div
      role="dialog"
      aria-label={tx.title}
      className="fixed inset-x-2 bottom-[5.25rem] z-50 flex max-h-[min(80vh,660px)] flex-col overflow-hidden rounded-3xl bg-cream-50 shadow-warm-lg ring-1 ring-cream-200 animate-fade-up sm:inset-x-auto sm:right-4 sm:w-[400px] lg:bottom-6 lg:right-6"
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

      {form && (
        <ContactForm
          tx={tx}
          onBack={() => setForm(false)}
          onSent={sent}
          initialMessage={turns.filter((t) => t.role === "user").map((t) => t.text).join("\n").slice(0, 1500)}
          send={(body) => apiPostJSON<{ ok: boolean; ref: string }>(`${API_BASE}/api/contact`,
            { ...body, lang, topic: lastTopic, page: currentPath })}
          errorText={(e) => ts(errorMessage(e))}
        />
      )}

      {/* conversation */}
      <div ref={list} hidden={form} className="relative flex-1 space-y-3 overflow-y-auto px-3 py-4 scrollbar-warm">
        {bubbles.map((b, i) => (
          <div key={i} data-me={b.from === "me" ? "" : undefined} className={b.from === "me" ? "flex justify-end" : "flex flex-col items-start"}>
            <div className={`max-w-[88%] ${b.from === "me" ? "rounded-2xl rounded-br-md bg-sage-500 px-3.5 py-2.5 text-cream-50" : "rounded-2xl rounded-bl-md bg-cream-100 px-3.5 py-2.5 text-ink-800"}`}>
              {b.ai && (
                <p className="mb-1.5 flex items-center gap-1.5 font-body text-[11px] font-bold uppercase tracking-wide text-sage-700">
                  <IconShield className="h-3.5 w-3.5" />{tx.aiName}
                </p>
              )}
              {b.typing ? (
                <p className="flex items-center gap-2 font-body text-sm text-dustyblue-600">
                  <span className="flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-dustyblue-400" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-dustyblue-400 [animation-delay:150ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-dustyblue-400 [animation-delay:300ms]" />
                  </span>
                  {b.lines[0]}
                </p>
              ) : b.lines.map((l, j) => (
                <p key={j} className={`whitespace-pre-wrap break-words font-body text-sm leading-relaxed ${j ? "mt-1.5" : ""}`}>{l}</p>
              ))}
              {b.ai && (
                <p className="mt-2 border-t border-cream-200 pt-2 font-body text-[11px] leading-snug text-dustyblue-600">{tx.aiLabel}</p>
              )}
              {b.langPick && (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {LANG_CHOICES.map(([code, name]) => (
                    <button key={code} type="button" onClick={() => pickLanguage(code)} disabled={thinking}
                      className="rounded-full bg-sage-500 px-3.5 py-1.5 font-body text-sm font-bold text-cream-50 hover:bg-sage-600 disabled:opacity-50">
                      {name}
                    </button>
                  ))}
                </div>
              )}
              {b.buttons && b.buttons.length > 0 && (
                <div className="mt-2.5 flex flex-col gap-1.5">
                  {b.buttons.map((btn, k) => (
                    <button key={k} type="button" onClick={() => press(btn)}
                      className={`flex items-center justify-center gap-1.5 rounded-xl px-3 py-2 font-body text-sm font-bold transition-colors ${
                        btn.kind === "person" || btn.kind === "form" ? "bg-cream-50 text-sage-700 ring-1 ring-sage-300 hover:bg-sage-100" : "bg-sage-500 text-cream-50 hover:bg-sage-600"}`}>
                      {(btn.kind === "person" || btn.kind === "form") && <IconChat className="h-4 w-4" />}
                      {btn.label}
                    </button>
                  ))}
                </div>
              )}
              {b.topics && (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {topics.map((tp) => (
                    <button key={tp.id} type="button" onClick={() => ask(tp.q, tp)} disabled={thinking}
                      className="rounded-full bg-cream-50 px-3 py-1.5 text-left font-body text-[13px] font-semibold text-ink-800 ring-1 ring-cream-200 transition-colors hover:bg-sage-100 hover:ring-sage-300 disabled:opacity-50">
                      {tp.q}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {b.aiAnyway && i === bubbles.length - 1 && !thinking && (
              <button type="button" onClick={() => { const q = b.aiAnyway!; setBubbles((all) => all.map((x) => x === b ? { ...x, aiAnyway: undefined } : x)); void askAssistant(q, () => say({ from: "bot", lines: [tx.noMatch], topics: true, team: true })); }}
                className="mt-1.5 flex items-center gap-1.5 px-1 font-body text-xs font-semibold text-sage-700 underline underline-offset-2 hover:text-sage-800">
                <IconShield className="h-3.5 w-3.5" />{tt.askAi}
              </button>
            )}
            {/* writing to the team: a quiet second option, after an answer */}
            {b.team && i === bubbles.length - 1 && !thinking && (
              <button type="button" onClick={person}
                className="mt-1.5 flex items-center gap-1.5 px-1 font-body text-xs font-semibold text-dustyblue-600 hover:text-sage-700">
                <IconChat className="h-3.5 w-3.5" />{tx.stillNeed} <span className="underline underline-offset-2">{tx.writeTeam}</span>
              </button>
            )}
          </div>
        ))}

        {/* first screen: common questions (they go to the AI too) */}
        {noAnswerYet && (
          <div className="pt-1">
            <p className="mb-2 px-1 font-body text-xs font-bold uppercase tracking-wide text-dustyblue-500">{tx.commonTitle}</p>
            <div className="flex flex-wrap gap-1.5">
              {topics.map((tp) => (
                <button key={tp.id} type="button" onClick={() => ask(tp.q, tp)} disabled={thinking}
                  className="rounded-full bg-cream-100 px-3 py-1.5 text-left font-body text-[13px] font-semibold text-ink-800 ring-1 ring-cream-200 transition-colors hover:bg-sage-100 hover:ring-sage-300 disabled:opacity-50">
                  {tp.q}
                </button>
              ))}
            </div>
            {teamOnly && (
              <button type="button" onClick={person}
                className="mt-3 flex items-center gap-1.5 px-1 font-body text-sm font-bold text-sage-700 underline underline-offset-2">
                <IconChat className="h-4 w-4" />{tx.writeTeam}
              </button>
            )}
          </div>
        )}
      </div>

      {/* typing box: the main way to use the Helper */}
      <form onSubmit={submit} hidden={form} className="border-t border-cream-200 bg-cream-50 p-2.5">
        <div className="flex items-end gap-2">
          <textarea ref={box} value={input} onChange={(e) => setInput(e.target.value)} placeholder={tx.placeholder}
            rows={2} maxLength={5000}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(e); } }}
            className={`min-w-0 flex-1 resize-none rounded-2xl border-2 bg-cream-100 px-3.5 py-2.5 font-body text-base text-ink-800 outline-none focus:border-sage-500 ${
              noAnswerYet ? "border-sage-400 ring-4 ring-sage-200/60" : "border-cream-200"}`} />
          <button type="submit" disabled={!input.trim() || thinking}
            className="shrink-0 rounded-2xl bg-sage-500 px-4 py-3 font-body text-sm font-bold text-cream-50 transition-colors hover:bg-sage-600 disabled:opacity-50">
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

type Texts = (typeof HELP_TEXTS)["en"];

/** The short "write to us" form: reply address, did you lose money, what happened. */
function ContactForm({ tx, onBack, onSent, send, errorText, initialMessage = "" }: {
  tx: Texts;
  initialMessage?: string;
  onBack: () => void;
  onSent: (ref: string, lost: string) => void;
  send: (body: Record<string, string>) => Promise<{ ok: boolean; ref: string }>;
  errorText: (e: unknown) => string;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [lost, setLost] = useState("");
  const [message, setMessage] = useState(initialMessage);
  const [trap, setTrap] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const canSend = message.trim().length >= 5 && (email.trim() || phone.trim()) && !busy;

  async function go(e: { preventDefault(): void }) {
    e.preventDefault();
    if (!canSend) return;
    setBusy(true); setError("");
    try {
      const r = await send({ name, email, phone, lost, message, website: trap });
      onSent(r.ref, lost);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  const field = "mt-1 w-full rounded-xl border-2 border-cream-200 bg-cream-100 px-3 py-2 font-body text-base text-ink-800 outline-none focus:border-sage-400";
  const label = "block font-body text-xs font-bold text-ink-800";
  return (
    <form onSubmit={go} className="flex-1 space-y-3 overflow-y-auto px-4 py-4 scrollbar-warm">
      <div className="flex items-center justify-between gap-2">
        <p className="font-heading text-base font-bold text-ink-900">{tx.formTitle}</p>
        <button type="button" onClick={onBack} className="rounded-full bg-cream-200 px-3 py-1 font-body text-xs font-bold text-ink-700 hover:bg-cream-300">{tx.formBack}</button>
      </div>
      <label className={label}>{tx.formName}
        <input value={name} onChange={(e) => setName(e.target.value)} maxLength={80} autoComplete="name" className={field} />
      </label>
      <div>
        <div className="grid grid-cols-2 gap-2">
          <label className={label}>{tx.formEmail}
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" inputMode="email" maxLength={120} autoComplete="email" className={field} />
          </label>
          <label className={label}>{tx.formPhone}
            <input value={phone} onChange={(e) => setPhone(e.target.value)} type="tel" inputMode="tel" maxLength={16} autoComplete="tel" className={field} />
          </label>
        </div>
        <p className="mt-1 font-body text-[11px] text-dustyblue-600">{tx.formEither}</p>
      </div>
      <div>
        <p className={label}>{tx.formLost}</p>
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {([["yes", tx.lostYes], ["no", tx.lostNo], ["unsure", tx.lostUnsure]] as const).map(([v, t]) => (
            <button key={v} type="button" onClick={() => setLost(lost === v ? "" : v)} aria-pressed={lost === v}
              className={`rounded-full px-3.5 py-1.5 font-body text-sm font-bold transition-colors ${
                lost === v ? (v === "yes" ? "bg-rust-500 text-cream-50" : "bg-sage-500 text-cream-50") : "bg-cream-200 text-ink-800 hover:bg-cream-300"}`}>
              {t}
            </button>
          ))}
        </div>
      </div>
      <label className={label}>{tx.formMessage}
        <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={4} maxLength={1500}
          placeholder={tx.formMessagePh} className={`${field} resize-none`} />
      </label>
      {/* hidden from people; only spam bots fill it in */}
      <input value={trap} onChange={(e) => setTrap(e.target.value)} name="website" tabIndex={-1} autoComplete="off"
        aria-hidden="true" className="absolute left-[-9999px] h-0 w-0 opacity-0" />
      <p className="flex items-start gap-1.5 rounded-xl bg-terracotta-300/20 p-2.5 font-body text-xs text-terracotta-700">
        <IconLock className="mt-0.5 h-3.5 w-3.5 shrink-0" />{tx.never}
      </p>
      {error && <p className="rounded-xl bg-rust-400/15 p-2.5 font-body text-sm text-rust-600">{error}</p>}
      <button type="submit" disabled={!canSend}
        className="w-full rounded-2xl bg-sage-500 px-4 py-3 font-body text-base font-bold text-cream-50 transition-colors hover:bg-sage-600 disabled:opacity-50">
        {busy ? tx.formSending : tx.formSend}
      </button>
    </form>
  );
}
