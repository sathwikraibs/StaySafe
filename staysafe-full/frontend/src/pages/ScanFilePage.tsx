import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { UploadZone } from "@/components/UploadZone";
import { PageHeader, ErrorNotice } from "@/components/PageBits";
import { apiPostForm, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanFileResponse } from "@/types";
import { useI18n } from "@/i18n";
import { IconFile } from "@/icons";

function formatSize(bytes?: number): string {
  if (bytes === undefined) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ScanFilePage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t, ts } = useI18n();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanFileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (!file || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const data = await apiPostForm<ScanFileResponse>(`${API_BASE}/api/scan-file`, fd);
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  const label = "font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600";
  const value = "-mt-1.5 font-body text-sm text-ink-800 sm:mt-0";

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

      {loading && <LoadingSteps tool="file" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="file"
          verdict={result.verdict}
          riskScore={result.risk_score}
          subject={result.filename}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          <div className="rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60 p-5">
            <div className="flex items-center gap-2">
              <IconFile className="h-5 w-5 text-dustyblue-600" />
              <h3 className="font-heading text-lg font-semibold text-ink-900">{t("file.details")}</h3>
            </div>
            <dl className="mt-3 grid gap-2.5 sm:grid-cols-[auto,1fr] sm:gap-x-5">
              <dt className={label}>{t("fileInfo.name")}</dt>
              <dd className={`${value} break-all`}>{result.filename}</dd>
              {result.detected_type && result.detected_type !== "unknown" && (
                <>
                  <dt className={label}>{t("fileInfo.really")}</dt>
                  <dd className={value}>{ts(result.detected_type)}</dd>
                </>
              )}
              {typeof result.size === "number" && (
                <>
                  <dt className={label}>{t("fileInfo.size")}</dt>
                  <dd className={value}>{formatSize(result.size)}</dd>
                </>
              )}
              <dt className={label}>{t("fileInfo.fingerprint")}</dt>
              <dd className="-mt-1.5 break-all font-mono text-[11px] text-ink-700 sm:mt-0">{result.sha256}</dd>
            </dl>
          </div>
        </ResultReport>
      )}
    </div>
  );
}
