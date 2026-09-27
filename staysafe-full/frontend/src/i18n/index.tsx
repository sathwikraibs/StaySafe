// Language system: pick a language, translate website text (t) and
// server results (ts), and supply translated recovery plans / scam library.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { en, type Dict } from "./en";
import { hi } from "./hi";
import { kn } from "./kn";
import { tcy } from "./tcy";
import type { LangContent } from "./content-types";
import { hiContent } from "./content-hi";
import { knContent } from "./content-kn";
import { tcyContent } from "./content-tcy";

export type Lang = "en" | "hi" | "kn" | "tcy";

type DeepPartial<T> = { [K in keyof T]?: T[K] extends readonly unknown[] ? T[K] : T[K] extends object ? DeepPartial<T[K]> : T[K] };

export const LANGUAGES: { code: Lang; native: string; english: string; short: string; beta?: boolean }[] = [
  { code: "en", native: "English", english: "English", short: "EN" },
  { code: "hi", native: "हिन्दी", english: "Hindi", short: "हि" },
  { code: "kn", native: "ಕನ್ನಡ", english: "Kannada", short: "ಕ" },
  { code: "tcy", native: "ತುಳು", english: "Tulu", short: "ತು", beta: true },
];

const DICTS: Record<Lang, DeepPartial<Dict>> = { en, hi, kn, tcy };
const CONTENT: Partial<Record<Lang, LangContent>> = { hi: hiContent, kn: knContent, tcy: tcyContent };

const STORAGE_KEY = "staysafe.lang.v1";

function detectLanguage(): Lang {
  try {
    const saved = localStorage.getItem(STORAGE_KEY) as Lang | null;
    if (saved && saved in DICTS) return saved;
  } catch { /* ignore */ }
  const prefs = (typeof navigator !== "undefined" && (navigator.languages || [navigator.language])) || [];
  for (const p of prefs) {
    const code = (p || "").toLowerCase().split("-")[0];
    if (code === "tcy") return "tcy";
    if (code === "kn") return "kn";
    if (code === "hi") return "hi";
  }
  return "en";
}

function lookup(dict: unknown, path: string): unknown {
  return path.split(".").reduce<unknown>((obj, key) => (obj && typeof obj === "object" ? (obj as Record<string, unknown>)[key] : undefined), dict);
}

function fill(text: string, vars?: Record<string, string | number>): string {
  if (!vars) return text;
  return text.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m));
}

// ---------------------------------------------------------------------------
// Server-text translation: English templates like "Website is fairly new ({days} days old)"
// are turned into regexes; captured values are re-inserted into the translated template.
// A placeholder called {reason} is itself translated (used for nested messages).
// ---------------------------------------------------------------------------
interface CompiledTemplate { re: RegExp; names: string[]; target: string }
const compiledCache = new Map<Lang, CompiledTemplate[]>();

function compile(lang: Lang): CompiledTemplate[] {
  const cached = compiledCache.get(lang);
  if (cached) return cached;
  const table = CONTENT[lang]?.server ?? {};
  const list = Object.entries(table).map(([source, target]) => {
    const names: string[] = [];
    const pattern = source
      .split(/(\{\w+\})/)
      .map((part) => {
        const m = part.match(/^\{(\w+)\}$/);
        if (m) { names.push(m[1]); return "([\\s\\S]+?)"; }
        return part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      })
      .join("");
    return { re: new RegExp(`^${pattern}$`), names, target };
  });
  // Longer templates first so specific ones win
  list.sort((a, b) => b.re.source.length - a.re.source.length);
  compiledCache.set(lang, list);
  return list;
}

export function translateServerText(text: string, lang: Lang, depth = 0): string {
  if (lang === "en" || !text || depth > 2) return text;
  for (const tpl of compile(lang)) {
    const m = text.match(tpl.re);
    if (!m) continue;
    const vars: Record<string, string> = {};
    tpl.names.forEach((name, i) => {
      const raw = m[i + 1];
      if (name === "reason") vars[name] = translateServerText(raw, lang, depth + 1);
      else if (name.startsWith("list")) vars[name] = raw.split(", ").map((x) => translateServerText(x, lang, depth + 1)).join(", ");
      else vars[name] = raw;
    });
    return fill(tpl.target, vars);
  }
  return text; // unknown message: show the original English rather than nothing
}

// ---------------------------------------------------------------------------
// React context
// ---------------------------------------------------------------------------
interface I18nValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  tl: (key: string) => string[];
  ts: (serverText: string) => string;
  content?: LangContent;
}

const I18nContext = createContext<I18nValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(detectLanguage);

  useEffect(() => {
    document.documentElement.lang = lang === "tcy" ? "tcy" : lang;
  }, [lang]);

  const setLang = useCallback((l: Lang) => {
    setLangState(l);
    try { localStorage.setItem(STORAGE_KEY, l); } catch { /* ignore */ }
  }, []);

  const value = useMemo<I18nValue>(() => {
    const dict = DICTS[lang];
    const t = (key: string, vars?: Record<string, string | number>) => {
      const v = lookup(dict, key) ?? lookup(en, key);
      return typeof v === "string" ? fill(v, vars) : key;
    };
    const tl = (key: string) => {
      const v = lookup(dict, key) ?? lookup(en, key);
      return Array.isArray(v) ? (v as string[]) : [];
    };
    return { lang, setLang, t, tl, ts: (s: string) => translateServerText(s, lang), content: CONTENT[lang] };
  }, [lang, setLang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used inside LanguageProvider");
  return ctx;
}
