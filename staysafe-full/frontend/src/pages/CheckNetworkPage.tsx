import { useState } from "react";
import { Button } from "@/components/Button";
import { LoadingSteps } from "@/components/LoadingSteps";
import { ResultReport } from "@/components/ResultReport";
import { ErrorNotice } from "@/components/PageBits";
import { ToolHeader } from "@/components/ToolHeader";
import { apiGet, errorMessage } from "@/api";
import { API_BASE } from "@/config";
import type { Check, CheckNetworkResponse } from "@/types";
import { IconNetwork, IconArrowRight, IconWarning } from "@/icons";
import { useI18n } from "@/i18n";

const SAFEHOP_URL = "https://safehop.vercel.app/";

interface BrowserInfo { name: string; version: number; outdated: boolean }

/** Which browser, and is it older than about a year? */
function browserInfo(): BrowserInfo | null {
  const ua = navigator.userAgent;
  const pick = (re: RegExp) => { const m = ua.match(re); return m ? parseInt(m[1], 10) : 0; };
  // Minimum versions released around 2025; anything older is missing security fixes
  const table: [string, RegExp, number][] = [
    ["Edge", /Edg\/(\d+)/, 130],
    ["Samsung Internet", /SamsungBrowser\/(\d+)/, 25],
    ["Opera", /OPR\/(\d+)/, 115],
    ["Firefox", /Firefox\/(\d+)/, 130],
    ["Chrome", /Chrome\/(\d+)/, 130],
    ["Safari", /Version\/(\d+)[.\d]* .*Safari/, 17],
  ];
  for (const [name, re, min] of table) {
    const v = pick(re);
    if (v) return { name, version: v, outdated: v < min };
  }
  return null;
}

interface NavConnection { type?: string; effectiveType?: string; downlink?: number }

/** Checks the browser can do by itself, added to the server's checks. */
function deviceChecks(): { checks: Check[]; browser: string; netType: string } {
  const checks: Check[] = [];
  checks.push({ id: "net_https", status: window.location.protocol === "https:" || window.location.hostname === "localhost" ? "pass" : "warn" });
  const b = browserInfo();
  if (b) checks.push({ id: "net_browser", status: b.outdated ? "warn" : "pass", value: `${b.name} ${b.version}` });
  const conn = (navigator as Navigator & { connection?: NavConnection }).connection;
  let netType = "";
  if (conn) {
    if (conn.type) netType = conn.type;
    if (typeof conn.downlink === "number" && conn.downlink > 0) {
      const mbps = Math.round(conn.downlink * 10) / 10;
      checks.push({ id: "net_speed", status: mbps < 1 ? "warn" : "info", value: mbps });
    }
  }
  return { checks, browser: b ? `${b.name} ${b.version}` : "", netType };
}

export function CheckNetworkPage({ onNavigate }: { onNavigate?: (path: string) => void }) {
  const { t, tl } = useI18n();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckNetworkResponse | null>(null);
  const [device, setDevice] = useState<ReturnType<typeof deviceChecks> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCheck() {
    if (loading) return;
    setLoading(true); setError(null); setResult(null);
    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
      const data = await apiGet<CheckNetworkResponse>(`${API_BASE}/api/check-network?tz=${encodeURIComponent(tz)}`);
      setDevice(deviceChecks());
      setResult(data);
    } catch (e) { setError(errorMessage(e)); } finally { setLoading(false); }
  }

  const allChecks = [...(result?.checks ?? []), ...(device?.checks ?? [])];
  const outdatedBrowser = device?.checks.some((c) => c.id === "net_browser" && c.status === "warn");
  const netTypeLabel = device?.netType === "wifi" ? "Wi-Fi" : device?.netType === "cellular" ? t("networkMore.mobile") : "";

  const rows: [string, string][] = result ? ([
    [t("networkMore.provider"), result.isp],
    [t("networkMore.location"), result.location],
    [t("networkMore.address"), result.ip],
    [t("networkMore.version"), result.ip_version ?? ""],
    [t("networkMore.timezone"), result.timezone ?? ""],
    [t("networkMore.netType"), netTypeLabel],
    [t("networkMore.browser"), device?.browser ?? ""],
  ] as [string, string][]).filter(([, v]) => v) : [];

  return (
    <div>
      <ToolHeader path="/check-network" title={t("network.title")} subtitle={t("network.subtitle")} />
      <div className="rounded-2xl bg-gradient-to-br from-dustyblue-100 to-cream-100 p-8 text-center shadow-warm">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-dustyblue-200 text-dustyblue-600">
          <IconNetwork className="h-8 w-8" />
        </div>
        <p className="mb-5 font-body text-base text-ink-700/80">
          {t("network.intro")}
        </p>
        <Button onClick={handleCheck} disabled={loading} variant="secondary">
          {loading ? t("common.checking") : t("network.button")}
        </Button>
      </div>

      {loading && <LoadingSteps tool="network" />}

      {error && <div className="mt-4"><ErrorNotice>{error}</ErrorNotice></div>}

      {result && (
        <ResultReport
          tool="network"
          verdict={outdatedBrowser && result.verdict === "SAFE" ? "CAUTION" : result.verdict}
          riskScore={outdatedBrowser ? Math.max(result.risk_score, 20) : result.risk_score}
          parts={result.score_parts}
          checks={allChecks}
          findings={result.findings.filter((f) => !f.startsWith("Approximate location"))}
          onNavigate={onNavigate}
        >
          {rows.length > 0 && (
            <div className="rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60 p-5">
              <h3 className="mb-3 font-heading text-lg font-semibold text-ink-900">{t("networkMore.detailsTitle")}</h3>
              <dl className="grid gap-2.5 sm:grid-cols-[auto,1fr] sm:gap-x-5">
                {rows.map(([k, v]) => (
                  <div key={k} className="contents">
                    <dt className="font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600 sm:pt-0.5">{k}</dt>
                    <dd className="-mt-1.5 break-all font-body text-sm text-ink-800 sm:mt-0">{v}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          <div className="rounded-2xl border-2 border-terracotta-300 bg-terracotta-300/20 p-5">
            <p className="flex items-center gap-2 font-heading text-lg font-semibold text-terracotta-700">
              <IconWarning className="h-5 w-5" /> {t("networkMore.publicWifiTitle")}
            </p>
            <ul className="mt-3 space-y-2">
              {tl("networkMore.publicWifi").map((tip) => (
                <li key={tip} className="flex items-start gap-2.5 font-body text-sm text-ink-800">
                  <span className="mt-[7px] h-2 w-2 shrink-0 rounded-full bg-terracotta-400" />
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </ResultReport>
      )}

      {/* Deeper Wi-Fi check on SafeHop */}
      <div className="mt-5 overflow-hidden rounded-2xl bg-gradient-to-br from-dustyblue-500 to-dustyblue-600 p-5 text-cream-50 shadow-warm sm:p-6">
        <p className="font-heading text-lg font-bold">{t("networkMore.safehopTitle")}</p>
        <p className="mt-1.5 font-body text-sm text-cream-50/90">{t("networkMore.safehopText")}</p>
        <a
          href={SAFEHOP_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-press mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-cream-50 px-5 py-3.5 font-body text-base font-bold text-dustyblue-600 shadow-warm hover:bg-cream-100 sm:w-auto sm:inline-flex"
        >
          {t("networkMore.safehopButton")} <IconArrowRight className="h-5 w-5" />
        </a>
        <p className="mt-2 break-all font-mono text-xs text-cream-50/80">safehop.vercel.app</p>
      </div>
    </div>
  );
}
