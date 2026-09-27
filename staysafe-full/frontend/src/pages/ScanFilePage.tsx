import { useState } from "react";
import { Button } from "@/components/Button";
import { VerdictBanner } from "@/components/VerdictBanner";
import { LoadingBreath } from "@/components/LoadingBreath";
import { UploadZone } from "@/components/UploadZone";
import { PageHeader, FindingsList, ErrorNotice } from "@/components/PageBits";
import { Card } from "@/components/Card";
import { apiPostForm, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanFileResponse } from "@/types";
import { useI18n } from "@/i18n";

export function ScanFilePage() {
  const { t, ts } = useI18n();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanFileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!file) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const data = await apiPostForm<ScanFileResponse>(`${API_BASE}/api/scan-file`, fd);
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  return (
    <div>
      <PageHeader title={t("file.title")} subtitle={t("file.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <UploadZone
          label={t("file.uploadLabel")}
          hint={t("file.uploadHint")}
          onFile={setFile}
          onClear={() => setFile(null)}
          disabled={loading}
        />
        {file && (
          <div className="mt-4">
            <Button onClick={handleCheck} disabled={loading} fullWidth>
              {loading ? t("common.checking") : t("file.button")}
            </Button>
          </div>
        )}
      </div>

      {loading && <LoadingBreath label={t("file.loading")} />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <div className="mt-4 space-y-4">
          <VerdictBanner verdict={result.verdict} riskScore={result.risk_score} />
          <Card className="p-4">
            <p className="font-body text-xs font-semibold uppercase tracking-wide text-dustyblue-500">{t("file.details")}</p>
            <p className="mt-1 font-body text-sm text-ink-800">{result.filename}</p>
            {result.detected_type && result.detected_type !== "unknown" && (
              <p className="mt-1 font-body text-xs text-dustyblue-600">{t("file.realType", { type: ts(result.detected_type) })}</p>
            )}
            <p className="mt-1 break-all font-body text-xs text-dustyblue-600">{t("file.id", { id: result.sha256 })}</p>
          </Card>
          <FindingsList items={result.findings} />
        </div>
      )}
    </div>
  );
}
