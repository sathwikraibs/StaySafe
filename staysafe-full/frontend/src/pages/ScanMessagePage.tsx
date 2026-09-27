import { useState } from "react";
import { Button } from "@/components/Button";
import { VerdictBanner } from "@/components/VerdictBanner";
import { LoadingBreath } from "@/components/LoadingBreath";
import { UploadZone } from "@/components/UploadZone";
import { PageHeader, FindingsList, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiPostJSON, apiPostForm, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanMessageResponse } from "@/types";
import { verdictTone, toneClasses, toneTagKey } from "@/verdict";
import { HiddenLinkGuide } from "@/components/HiddenLinkGuide";
import { IconInfo } from "@/icons";
import { useI18n } from "@/i18n";

export function ScanMessagePage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t, ts } = useI18n();
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanMessageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fromScreenshot, setFromScreenshot] = useState(false);

  async function handleCheckText() {
    if (!text.trim()) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const data = await apiPostJSON<ScanMessageResponse>(`${API_BASE}/api/scan-message`, { text: text.trim() });
      setResult(data); setFromScreenshot(false);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  async function handleCheckScreenshot() {
    if (!file) return;
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
      <PageHeader title={t("message.title")} subtitle={t("message.subtitle")} />

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

      {/* Links hidden behind "Click here" can't be checked from a screenshot or copied text */}
      <div className="mt-4">
        <HiddenLinkGuide onNavigate={onNavigate} />
      </div>

      {loading && <LoadingBreath label={t("message.loading")} />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className="mt-4 space-y-4">
          <VerdictBanner verdict={result.verdict} riskScore={result.risk_score} />
          {result.notes && result.notes.length > 0 && (
            <div className="space-y-2 rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100 p-4">
              <p className="flex items-center gap-2 font-heading text-base font-semibold text-ink-800">
                <IconInfo className="h-5 w-5 text-dustyblue-500" /> {t("message.notesTitle")}
              </p>
              {result.notes.map((n) => (
                <p key={n} className="font-body text-sm text-ink-700">{ts(n)}</p>
              ))}
            </div>
          )}
          {result.patterns_detected.length > 0 ? (
            <FindingsList items={result.patterns_detected} title={t("message.warningSigns")} />
          ) : (
            <FindingsList items={[t("message.noPatterns")]} />
          )}
          {result.safe_signals && result.safe_signals.length > 0 && (
            <FindingsList items={result.safe_signals} title={t("message.goodSigns")} />
          )}
          {result.links_checked && result.links_checked.length > 0 && (
            <Card className="p-4">
              <p className="font-body text-xs font-semibold uppercase tracking-wide text-dustyblue-500">{t("message.linksTitle")}</p>
              <ul className="mt-2 space-y-2">
                {result.links_checked.map((link) => {
                  const tone = verdictTone(link.verdict);
                  const cls = toneClasses(tone);
                  return (
                    <li key={link.url} className="flex items-start gap-2">
                      <span className={`shrink-0 rounded-lg px-2 py-0.5 font-body text-xs font-semibold ${cls.bg} ${cls.text}`}>
                        {t(toneTagKey(tone))}
                      </span>
                      <span className="break-all font-body text-sm text-ink-800">{link.url}</span>
                    </li>
                  );
                })}
              </ul>
              <p className="mt-2 font-body text-xs text-dustyblue-600">
                {t("message.linksNote")}
              </p>
            </Card>
          )}
          {fromScreenshot && result.text_analyzed && (
            <Card className="p-4">
              <p className="font-body text-xs font-semibold uppercase tracking-wide text-dustyblue-500">{t("message.ocrTitle")}</p>
              <p className="mt-2 whitespace-pre-wrap break-words font-body text-sm text-ink-800">{result.text_analyzed}</p>
              <p className="mt-2 font-body text-xs text-dustyblue-600">{t("message.ocrNote")}</p>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
