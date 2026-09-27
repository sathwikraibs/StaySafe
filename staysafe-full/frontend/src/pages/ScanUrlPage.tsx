import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultReport, useFormatAge } from "@/components/ResultReport";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { apiPostJSON, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanUrlResponse } from "@/types";
import { useI18n } from "@/i18n";
import { HiddenLinkGuide } from "@/components/HiddenLinkGuide";

/** Small "details" card: website name, where it really goes, page title, age. */
export function LinkDetails({ details }: { details?: ScanUrlResponse["details"] }) {
  const { t } = useI18n();
  const formatAge = useFormatAge();
  if (!details) return null;
  const rows: [string, string][] = [];
  if (details.domain) rows.push([t("linkInfo.site"), details.domain]);
  if (details.final_url) rows.push([t("linkInfo.goesTo"), details.final_url]);
  if (details.page_title) rows.push([t("linkInfo.pageTitle"), details.page_title]);
  if (details.age_days !== null && details.age_days !== undefined) rows.push([t("linkInfo.age"), formatAge(details.age_days)]);
  if (details.ip) rows.push([t("linkInfo.server"), details.ip]);
  if (!rows.length) return null;
  return (
    <div className="rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60 p-5 animate-fade-up">
      <h3 className="mb-3 font-heading text-lg font-semibold text-ink-900">{t("linkInfo.title")}</h3>
      <dl className="grid gap-2.5 sm:grid-cols-[auto,1fr] sm:gap-x-5">
        {rows.map(([k, v]) => (
          <div key={k} className="contents">
            <dt className="font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600 sm:pt-0.5">{k}</dt>
            <dd className="-mt-1.5 break-all font-body text-sm text-ink-800 sm:mt-0">{v}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function ScanUrlPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanUrlResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!url.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await apiPostJSON<ScanUrlResponse>(`${API_BASE}/api/scan-url`, { url: url.trim() });
      setResult(data);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <PageHeader title={t("url.title")} subtitle={t("url.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <label className="mb-2 block font-body text-sm font-semibold text-ink-800">{t("url.label")}</label>
        <input
          type="url"
          inputMode="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleCheck(); }}
          placeholder="https://example.com"
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3.5 font-body text-base text-ink-800 outline-none transition-colors focus:border-sage-400"
        />
        <div className="mt-4">
          <Button onClick={handleCheck} disabled={loading || !url.trim()} fullWidth>
            {loading ? t("common.checking") : t("url.button")}
          </Button>
        </div>
      </div>

      {loading && <LoadingSteps tool="link" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="link"
          verdict={result.verdict}
          riskScore={result.risk_score}
          subject={result.url}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          <LinkDetails details={result.details} />
        </ResultReport>
      )}

      <div className="mt-5">
        <HiddenLinkGuide onNavigate={onNavigate} showLinkButton={false} />
      </div>
    </div>
  );
}
