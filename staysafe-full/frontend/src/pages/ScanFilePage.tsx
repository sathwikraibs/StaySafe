import { useEffect, useState } from "react";
import { useSharedFile } from "@/share";
import { Button } from "@/components/Button";
import { LoadingSteps, usePace } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { UploadZone } from "@/components/UploadZone";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { apiPostForm, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { ScanFileResponse } from "@/types";
import { useI18n } from "@/i18n";
import { IconFile, IconKey } from "@/icons";
import { Section } from "@/components/Section";
import { CheckedLinks } from "@/components/WebsiteDetails";
import { VirusTotalPanel } from "@/components/VirusTotalPanel";

function formatSize(bytes?: number): string {
  if (bytes === undefined) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function ScanFilePage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t, ts } = useI18n();
  const pace = usePace();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScanFileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fullScan, setFullScan] = useState(false);
  const [incoming, setIncoming] = useState<File | null>(null);
  const [auto, setAuto] = useState(false);
  useSharedFile("file", (f) => { setIncoming(f); setAuto(true); });

  async function handleCheck() {
    if (!file || loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      if (fullScan) fd.append("vt_upload", "1");
      const data = await pace("file", apiPostForm<ScanFileResponse>(`${API_BASE}/api/scan-file`, fd));
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }
  // shared to TrustLight from another app: check it straight away
  useEffect(() => {
    if (auto && file) { setAuto(false); handleCheck(); }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto, file]);


  const label = "font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600";
  const value = "-mt-1.5 font-body text-sm text-ink-800 sm:mt-0";

  return (
    <div>
      <ToolHeader path="/scan-file" title={t("file.title")} subtitle={t("file.subtitle")} />
      <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
        <UploadZone
          label={t("file.uploadLabel")}
          hint={t("file.uploadHint")}
          onFile={setFile}
          onClear={() => setFile(null)}
          disabled={loading}
          camera={false}
          incoming={incoming}
        />
        <label className="mt-4 flex cursor-pointer items-start gap-3 rounded-xl bg-cream-100 p-3">
          <input type="checkbox" checked={fullScan} onChange={(e) => setFullScan(e.target.checked)} className="mt-1 h-4 w-4 shrink-0 accent-[#647A4F]" />
          <span className="font-body text-sm text-ink-800">
            <b>{t("vt.uploadTitle")}</b>
            <span className="mt-0.5 block text-xs text-dustyblue-600">{t("vt.uploadNote")}</span>
          </span>
        </label>
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
          parts={result.score_parts}
          subject={result.filename}
          checks={result.checks}
          findings={result.findings}
          onNavigate={onNavigate}
        >
          <VirusTotalPanel vt={result.virustotal} />
          {result.links_checked && result.links_checked.length > 0 && (
            <CheckedLinks links={result.links_checked} title={t("fileX.linksTitle")} />
          )}
          {result.apk && result.apk.permissions.length > 0 && (
            <Section icon={<IconKey className="h-5 w-5" />} title={t("fileX.permissions", { n: result.apk.permissions.length })}
              tone={result.checks?.some((c) => c.id === "file_apk" && c.status === "fail") ? "bad" : "info"}>
              <ul className="flex flex-wrap gap-1.5">
                {result.apk.permissions.map((p) => (
                  <li key={p} className="rounded-md bg-cream-100 px-2 py-0.5 font-mono text-[11px] text-ink-700">{p.replace("android.permission.", "")}</li>
                ))}
              </ul>
            </Section>
          )}
          <Section icon={<IconFile className="h-5 w-5" />} title={t("file.details")} summary={typeof result.size === "number" ? formatSize(result.size) : undefined}>
            <dl className="grid gap-2.5 sm:grid-cols-[auto,1fr] sm:gap-x-5">
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
              <dt className={label}>SHA-256</dt>
              <dd className="-mt-1.5 break-all font-mono text-[11px] text-ink-700 sm:mt-0">{result.sha256}</dd>
              {result.sha1 && (<><dt className={label}>SHA-1</dt><dd className="-mt-1.5 break-all font-mono text-[11px] text-ink-700 sm:mt-0">{result.sha1}</dd></>)}
              {result.md5 && (<><dt className={label}>MD5</dt><dd className="-mt-1.5 break-all font-mono text-[11px] text-ink-700 sm:mt-0">{result.md5}</dd></>)}
              {result.apk?.package && (
                <>
                  <dt className={label}>{t("fileX.appId")}</dt>
                  <dd className="break-all font-mono text-xs text-ink-800">{result.apk.package}</dd>
                </>
              )}
            </dl>
          </Section>
        </ResultReport>
      )}
    </div>
  );
}
