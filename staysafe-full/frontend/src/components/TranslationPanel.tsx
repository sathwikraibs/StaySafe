import { useEffect, useState } from "react";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import { IconLanguage } from "@/icons";
import { Section } from "@/components/Section";
import { useI18n } from "@/i18n";

/** Languages a message can be shown in, with their own names so anyone can find theirs. */
const TARGETS: [string, string][] = [["en", "English"], ["kn", "ಕನ್ನಡ"], ["tcy", "ತುಳು"], ["hi", "हिन्दी"]];

/** Browsers often don't know Tulu's name, so we give it ourselves. */
const TULU: Record<string, string> = { en: "Tulu", kn: "ತುಳು", tcy: "ತುಳು", hi: "तुलु" };

type Done = { text: string; from: string; to: string };
type Slot = Done | "busy" | { error: string };

/** "Kannada", "ಕನ್ನಡ", "कन्नड़"… the name of a language code, in the website language. */
export function languageName(code: string, uiLang: string): string {
  if (code === "tcy") return TULU[uiLang] ?? "Tulu";
  try {
    const names = new Intl.DisplayNames([uiLang === "tcy" ? "kn" : uiLang], { type: "language" });
    return names.of(code) || code;
  } catch {
    return code;
  }
}

/**
 * The message as it was received next to a translation. Opens by itself when the message is
 * in a different language from the website (for example a Kannada screenshot on the English
 * site, or an English message on the Kannada site). The visitor can switch the translation to
 * English, Kannada or Hindi.
 */
export function TranslationPanel({ original, sourceLang, initial, fromScreenshot }: {
  original: string;
  sourceLang?: string;
  initial?: Done;
  fromScreenshot?: boolean;
}) {
  const { t, lang } = useI18n();
  const uiTarget = lang;
  const source = (initial?.from || sourceLang || "").split("-")[0];
  const [slots, setSlots] = useState<Record<string, Slot>>(initial ? { [initial.to]: initial } : {});
  const [picked, setPicked] = useState<string | null>(initial ? initial.to : null);

  const options = TARGETS.filter(([code]) => code !== source);
  const differs = !!initial || (!!source && source !== uiTarget);

  async function show(code: string) {
    setPicked(code);
    const have = slots[code];
    if (have && have !== "busy" && !("error" in have)) return;
    setSlots((s) => ({ ...s, [code]: "busy" }));
    try {
      const out = await apiPostJSON<Done>(`${API_BASE}/api/translate`, { text: original, to: code });
      setSlots((s) => ({ ...s, [code]: out }));
    } catch (e) {
      setSlots((s) => ({ ...s, [code]: { error: errorMessage(e) } }));
    }
  }

  // Message in another language but no translation came with the result: fetch one now
  useEffect(() => {
    if (!initial && source && source !== uiTarget && TARGETS.some(([c]) => c === uiTarget)) void show(uiTarget);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const slot = picked ? slots[picked] : undefined;
  const got = slot && slot !== "busy" && !("error" in slot) ? slot : null;
  // Tulu asked for while only Kannada was available, and the message is already Kannada
  const same = !!got && got.to === source && got.to !== picked;
  const done = same ? null : got;
  const sourceName = source ? languageName(source, lang) : "";
  const summary = done && sourceName ? `${sourceName} → ${languageName(done.to, lang)}` : sourceName || undefined;

  return (
    <Section icon={<IconLanguage className="h-5 w-5" />} title={t("message.trTitle")} tone="info" defaultOpen={differs} summary={summary}>
      <div className="grid gap-3 sm:grid-cols-2">
        {/* as received */}
        <div className="min-w-0">
          <p className="mb-1.5 font-body text-xs font-bold uppercase tracking-wide text-dustyblue-500">
            {fromScreenshot ? t("message.ocrTitle") : t("message.trOriginal")}{sourceName ? ` · ${sourceName}` : ""}
          </p>
          <p className="max-h-72 overflow-y-auto whitespace-pre-wrap break-words rounded-xl bg-cream-100 p-3 font-body text-sm text-ink-800 scrollbar-warm">
            {original}
          </p>
        </div>

        {/* translated */}
        <div className="min-w-0">
          <p className="mb-1.5 font-body text-xs font-bold uppercase tracking-wide text-dustyblue-500">
            {done ? languageName(done.to, lang) : t("message.trShowIn")}
          </p>
          {done ? (
            <p className="max-h-72 overflow-y-auto whitespace-pre-wrap break-words rounded-xl bg-brand-100 p-3 font-body text-sm text-ink-800 scrollbar-warm">
              {done.text}
            </p>
          ) : same ? (
            <p className="rounded-xl border-2 border-dashed border-cream-200 p-3 font-body text-sm text-dustyblue-600">{t("message.tuluSame")}</p>
          ) : slot === "busy" ? (
            <p className="flex items-center gap-2 rounded-xl bg-cream-100 p-3 font-body text-sm text-dustyblue-600">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-dustyblue-300 border-t-transparent" />
              {t("message.trBusy")}
            </p>
          ) : slot && "error" in slot ? (
            <p className="rounded-xl bg-terracotta-300/20 p-3 font-body text-sm text-terracotta-700">{t("message.trFailed")}</p>
          ) : (
            <p className="rounded-xl border-2 border-dashed border-cream-200 p-3 font-body text-sm text-dustyblue-600">{t("message.trPick")}</p>
          )}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <span className="font-body text-xs font-semibold text-dustyblue-600">{t("message.trShowIn")}:</span>
        {options.map(([code, name]) => (
          <button
            key={code}
            type="button"
            onClick={() => show(code)}
            aria-pressed={picked === code}
            className={`rounded-full px-3 py-1 font-body text-sm font-bold transition-colors ${
              picked === code ? "bg-dustyblue-600 text-cream-50" : "bg-cream-200 text-ink-800 hover:bg-cream-300"
            }`}
          >
            {name}
          </button>
        ))}
      </div>

      <p className="mt-2 font-body text-xs text-dustyblue-500">
        {done ? t("message.meaningNoteSimple") : ""}
        {done && picked === "tcy" && done.to !== "tcy" ? ` ${t("message.tuluAsKannada")}` : ""}
        {fromScreenshot ? `${done ? " " : ""}${t("message.ocrNote")}` : ""}
      </p>
    </Section>
  );
}
