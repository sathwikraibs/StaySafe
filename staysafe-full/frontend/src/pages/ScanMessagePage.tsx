import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { UploadZone } from "@/components/UploadZone";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { Card } from "@/components/Card";
import { apiPostJSON, apiPostForm, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { Check, ScanMessageResponse } from "@/types";
import { verdictTone } from "@/verdict";
import { HiddenLinkGuide } from "@/components/HiddenLinkGuide";
import { CheckedLinks } from "@/components/WebsiteDetails";
import { IconInfo, IconLanguage } from "@/icons";
import { useI18n } from "@/i18n";

/** "Tamil", "ತಮಿಳು", "तमिल"… — the name of a language code, in the website language. */
function languageName(code: string, uiLang: string): string {
  try {
    const names = new Intl.DisplayNames([uiLang === "tcy" ? "kn" : uiLang], { type: "language" });
    return names.of(code) || code;
  } catch {
    return code;
  }
}

/** The "What we checked" list for a message, worked out from the result. */
function messageChecks(r: ScanMessageResponse): Check[] {
  const checks: Check[] = [];
  const signs = r.patterns_detected.filter((p) => !p.startsWith("The link ") && !p.startsWith("This message has "));
  checks.push({ id: "msg_patterns", status: signs.length === 0 ? "pass" : signs.length >= 2 ? "fail" : "warn", value: signs.length });
  const links = r.links_checked ?? [];
  const risky = links.filter((l) => verdictTone(l.verdict) !== "safe").length;
  checks.push(links.length === 0
    ? { id: "msg_links", status: "info" }
    : risky ? { id: "msg_links", status: "fail", value: risky } : { id: "msg_links", status: "pass", value: links.length });
  checks.push({ id: "msg_safe", status: r.safe_signals && r.safe_signals.length ? "pass" : "info" });
  if (r.verdict === "UNCERTAIN") checks.push({ id: "msg_language", status: "warn" });
  else if (r.translation) checks.push({ id: "msg_language", status: "info" });
  return checks;
}

export function ScanMessagePage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t, ts, lang } = useI18n();
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanMessageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fromScreenshot, setFromScreenshot] = useState(false);
  const [pendingTool, setPendingTool] = useState<"message" | "screenshot">("message");

  async function handleCheckText() {
    if (!text.trim() || loading) return;
    setPendingTool("message");
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiPostJSON<ScanMessageResponse>(`${API_BASE}/api/scan-message`, { text: text.trim() });
      setResult(data); setFromScreenshot(false);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  async function handleCheckScreenshot() {
    if (!file || loading) return;
    setPendingTool("screenshot");
    setLoading(true); setError(null); setResult(null);
    try {
      const fd = new FormData();
      fd.append("image", file);
      const data = await apiPostForm<ScanMessageResponse>(`${API_BASE}/api/scan-screenshot`, fd);
      setResult(data); setFromScreenshot(true);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  return (
    <div>
      <ToolHeader path="/scan-message" title={t("message.title")} subtitle={t("message.subtitle")} />

      {/* Text tab */}
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">{t("message.pasteTitle")}</h3>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={5}
          placeholder={t("message.placeholder")}
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400 scrollbar-warm"
        />
        <div className="mt-4">
          <Button onClick={handleCheckText} disabled={loading || !text.trim()} fullWidth>
            {loading ? t("common.checking") : t("message.button")}
          </Button>
        </div>
      </div>

      {/* Divider */}
      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-cream-200" />
        <span className="font-body text-sm text-dustyblue-500">{t("message.or")}</span>
        <div className="h-px flex-1 bg-cream-200" />
      </div>

      {/* Screenshot tab */}
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">{t("message.uploadTitle")}</h3>
        <UploadZone
          accept="image/*"
          label={t("message.uploadLabel")}
          compress
          hint={t("message.uploadHint")}
          onFile={setFile}
          onClear={() => setFile(null)}
          disabled={loading}
        />
        {file && (
          <div className="mt-4">
            <Button onClick={handleCheckScreenshot} disabled={loading} fullWidth>
              {loading ? t("common.checking") : t("message.uploadButton")}
            </Button>
          </div>
        )}
      </div>

      {loading && <LoadingSteps tool={pendingTool} />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="message"
          verdict={result.verdict}
          riskScore={result.risk_score}
          checks={messageChecks(result)}
          findings={result.patterns_detected}
          onNavigate={onNavigate}
        >
          {result.translation && (
            <Card className="border-2 border-sage-200 p-5">
              <p className="flex items-center gap-2 font-heading text-lg font-semibold text-ink-900">
                <IconLanguage className="h-5 w-5 text-sage-600" /> {t("message.meaningTitle")}
              </p>
              <p className="mt-0.5 font-body text-xs text-dustyblue-600">
                {t("message.translatedFrom", { lang: languageName(result.translation.from, lang) })}
                {lang === "tcy" && result.translation.to === "kn" ? `, ${t("message.shownInKannada")}` : ""}
              </p>
              <p className="mt-3 whitespace-pre-wrap break-words rounded-xl bg-sage-100 p-3 font-body text-base text-ink-800">
                {result.translation.text}
              </p>
              <p className="mt-2 font-body text-xs text-dustyblue-500">{t("message.meaningNote", { provider: ({ mymemory: "MyMemory", gemini: "Google Gemini", bhashini: "Bhashini", google: "Google" } as Record<string, string>)[result.translation.provider ?? ""] ?? "MyMemory" })}</p>
            </Card>
          )}
          {result.notes && result.notes.length > 0 && (
            <div className="space-y-2 rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100 p-5">
              <p className="flex items-center gap-2 font-heading text-lg font-semibold text-ink-900">
                <IconInfo className="h-5 w-5 text-dustyblue-500" /> {t("message.notesTitle")}
              </p>
              {result.notes.map((n) => (
                <p key={n} className="font-body text-sm text-ink-700">{ts(n)}</p>
              ))}
            </div>
          )}
          {result.safe_signals && result.safe_signals.length > 0 && (
            <div className="rounded-2xl border-2 border-sage-200 bg-sage-100 p-5">
              <p className="mb-2 font-heading text-lg font-semibold text-sage-700">{t("message.goodSigns")}</p>
              <ul className="space-y-1.5">
                {result.safe_signals.map((g) => (
                  <li key={g} className="flex items-start gap-2 font-body text-sm text-ink-800">
                    <span className="mt-[7px] h-2 w-2 shrink-0 rounded-full bg-sage-500" />{ts(g)}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {result.links_checked && result.links_checked.length > 0 && (
            <CheckedLinks links={result.links_checked} title={t("message.linksTitle")} note={t("message.linksNote")} />
          )}
          {fromScreenshot && result.text_analyzed && (
            <Card className="p-5">
              <p className="font-heading text-lg font-semibold text-ink-900">{t("message.ocrTitle")}</p>
              <p className="mt-2 whitespace-pre-wrap break-words rounded-xl bg-cream-100 p-3 font-body text-sm text-ink-800">{result.text_analyzed}</p>
              <p className="mt-2 font-body text-xs text-dustyblue-600">{t("message.ocrNote")}</p>
            </Card>
          )}
        </ResultReport>
      )}

      {/* Links hidden behind "Click here" can't be checked from a screenshot or copied text */}
      <div className="mt-5">
        <HiddenLinkGuide onNavigate={onNavigate} />
      </div>
    </div>
  );
}
