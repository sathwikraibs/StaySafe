import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { UploadZone } from "@/components/UploadZone";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { apiPostForm, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanQrResponse } from "@/types";
import { useI18n } from "@/i18n";
import { LinkDetails } from "@/pages/ScanUrlPage";
import { IconQr } from "@/icons";

export function ScanQrPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t } = useI18n();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanQrResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!file || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const fd = new FormData();
      fd.append("image", file);
      const data = await apiPostForm<ScanQrResponse>(`${API_BASE}/api/scan-qr`, fd);
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  const typeLabel = (type: string) => {
    const key = `qr.types.${type}`;
    return t(key) === key ? type : t(key);
  };

  return (
    <div>
      <PageHeader title={t("qr.title")} subtitle={t("qr.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <UploadZone
          accept="image/*"
          label={t("qr.uploadLabel")}
          hint={t("qr.uploadHint")}
          onFile={setFile}
          onClear={() => setFile(null)}
          disabled={loading}
        />
        {file && (
          <div className="mt-4">
            <Button onClick={handleCheck} disabled={loading} fullWidth>
              {loading ? t("common.checking") : t("qr.button")}
            </Button>
          </div>
        )}
      </div>

      {loading && <LoadingSteps tool="qr" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="qr"
          verdict={result.verdict}
          riskScore={result.risk_score}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          {result.raw_data && (
            <div className="rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60 p-5">
              <div className="flex items-center gap-2">
                <IconQr className="h-5 w-5 text-dustyblue-600" />
                <h3 className="font-heading text-lg font-semibold text-ink-900">{t("qr.contains")}</h3>
                {result.qr_type && (
                  <span className="ml-auto rounded-full bg-cream-50 px-2.5 py-1 font-body text-xs font-bold text-dustyblue-600">
                    {typeLabel(result.qr_type)}
                  </span>
                )}
              </div>
              <p className="mt-3 break-all rounded-xl bg-cream-50 p-3 font-mono text-xs text-ink-800 sm:text-sm">{result.raw_data}</p>
            </div>
          )}
          {result.qr_type === "url" && <LinkDetails details={result.details} />}
        </ResultReport>
      )}
    </div>
  );
}
