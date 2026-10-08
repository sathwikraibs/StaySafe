import { useEffect, useState } from "react";
import { takeAutoRun } from "@/share";
import { usePrefill } from "@/helpBot";
import { Button } from "@/components/Button";
import { LoadingSteps, usePace } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { LinkDetails } from "@/components/WebsiteDetails";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { apiPostJSON, errorMessage, rememberInput } from "@/api";
import { API_BASE } from "@/config";
import type { ScanUrlResponse } from "@/types";
import { useI18n } from "@/i18n";
import { ReportButton } from "@/components/ReportButton";
import { HiddenLinkGuide } from "@/components/HiddenLinkGuide";

export function ScanUrlPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const pace = usePace();
  const [url, setUrl] = useState("");
  const [auto, setAuto] = useState(false);
  usePrefill("url", (v) => { setUrl(v); if (takeAutoRun("url")) setAuto(true); });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanUrlResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [asked, setAsked] = useState("");

  async function handleCheck() {
    if (!url.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setAsked(url.trim());
      rememberInput({ text: url.trim() });
      const data = await pace("link", apiPostJSON<ScanUrlResponse>(`${API_BASE}/api/scan-url`, { url: url.trim() }));
      setResult(data);
      // show the tidied address in the box so the person sees exactly what was checked
      if (data.url && data.url !== url.trim()) setUrl(data.url);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }
  // shared to TrustLight from another app: check it straight away
  useEffect(() => {
    if (auto && url.trim()) { setAuto(false); handleCheck(); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto, url]);


  return (
    <div>
      <ToolHeader path="/scan-url" title={t("url.title")} subtitle={t("url.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <label className="mb-2 block font-body text-sm font-semibold text-ink-800">{t("url.label")}</label>
        <input
          type="text"
          inputMode="url"
          autoCapitalize="off"
          autoCorrect="off"
          spellCheck={false}
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleCheck(); }}
          placeholder="https://example.com"
          className="w-full rounded-2xl border-2 border-cream-200 bg-cream-100 px-4 py-3.5 font-body text-base text-ink-800 outline-none transition-colors focus:border-brand-400"
        />
        <div className="mt-4">
          <Button onClick={handleCheck} disabled={loading || !url.trim()} fullWidth>
            {loading ? t("common.checking") : t("url.button")}
          </Button>
        </div>
      </div>

      {loading && <LoadingSteps tool="link" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && asked && !result.url.replace(/^https?:\/\//i, "").startsWith(asked.replace(/^https?:\/\//i, "").replace(/\/$/, "")) && (
        <p className="mt-4 break-all rounded-xl bg-brand-100 px-4 py-2.5 font-body text-sm text-brand-700">{t("urlX.cleaned", { url: result.url })}</p>
      )}

      {result && (
        <ResultReport
          tool="link"
          verdict={result.verdict}
          riskScore={result.risk_score}
          parts={result.score_parts}
          subject={result.url}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          <LinkDetails details={result.details} />
          <ReportButton key={result.url} kind="link" value={result.url} />
        </ResultReport>
      )}

      <div className="mt-5">
        <HiddenLinkGuide onNavigate={onNavigate} showLinkButton={false} />
      </div>
    </div>
  );
}
