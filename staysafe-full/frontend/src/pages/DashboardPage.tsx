import { useState } from "react";
import { Button } from "@/components/Button";
import { PageHeader } from "@/components/PageBits";
import { Card } from "@/components/Card";
import type { ScanHistoryItem } from "@/types";
import { verdictTone, toneClasses, riskBarColor, toneTagKey } from "@/verdict";
import { IconHistory } from "@/icons";
import { loadHistory, clearHistory, computeDashboard } from "@/history";
import { useI18n } from "@/i18n";

export function DashboardPage({ onNavigate }: { onNavigate: (path: string) => void }) {
  // History lives in this browser, so it's private to you and survives server restarts.
  const { t } = useI18n();
  const [history, setHistory] = useState<ScanHistoryItem[]>(() => loadHistory());
  const [tab, setTab] = useState<"overview" | "history">("overview");
  const data = computeDashboard(history);

  function handleClear() {
    if (window.confirm(t("dashboard.clearConfirm"))) {
      clearHistory();
      setHistory([]);
    }
  }

  if (history.length === 0) {
    return (
      <div>
        <PageHeader title={t("dashboard.title")} subtitle={t("dashboard.subtitleEmpty")} />
        <div className="rounded-2xl bg-gradient-to-br from-sage-100 to-cream-100 p-8 text-center shadow-warm">
          <IconHistory className="mx-auto mb-3 h-10 w-10 text-dustyblue-400" />
          <p className="mb-5 font-body text-base text-ink-700/80">
            {t("dashboard.empty")}
          </p>
          <Button onClick={() => onNavigate("/")} variant="secondary">{t("dashboard.start")}</Button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={t("dashboard.title")} subtitle={t("dashboard.subtitle")} />

      <div>
          {/* Tabs */}
          <div className="mb-5 flex gap-2">
            <button
              onClick={() => setTab("overview")}
              className={`btn-press rounded-xl px-4 py-2 font-body text-sm font-semibold ${tab === "overview" ? "bg-sage-200 text-sage-700" : "bg-cream-100 text-dustyblue-600"}`}
            >{t("dashboard.overview")}</button>
            <button
              onClick={() => setTab("history")}
              className={`btn-press rounded-xl px-4 py-2 font-body text-sm font-semibold ${tab === "history" ? "bg-sage-200 text-sage-700" : "bg-cream-100 text-dustyblue-600"}`}
            >{t("dashboard.history")}</button>
          </div>

          {tab === "overview" && (
            <div className="space-y-4">
              {/* Score circle */}
              <Card className="p-6 text-center">
                <p className="font-body text-sm text-dustyblue-600">{t("dashboard.yourScore")}</p>
                <div className="relative mx-auto my-4 flex h-32 w-32 items-center justify-center">
                  <svg className="absolute h-full w-full -rotate-90" viewBox="0 0 120 120">
                    <circle cx="60" cy="60" r="52" fill="none" stroke="#EFE3D0" strokeWidth="10" />
                    <circle
                      cx="60" cy="60" r="52" fill="none"
                      stroke={data.safety_score >= 70 ? "#7E9168" : data.safety_score >= 40 ? "#D4896A" : "#A84A3A"}
                      strokeWidth="10" strokeLinecap="round"
                      strokeDasharray={`${(data.safety_score / 100) * 327} 327`}
                    />
                  </svg>
                  <span className="font-heading text-3xl font-bold text-ink-900">{data.safety_score}</span>
                </div>
                <p className="font-heading text-lg font-semibold text-ink-800">{t(`dashboard.labels.${data.safety_label}`)}</p>
                <p className="mt-1 font-body text-sm text-dustyblue-600">{t("dashboard.total", { count: data.total_scans })}</p>
              </Card>

              {/* Breakdown */}
              <Card className="p-5">
                <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">{t("dashboard.breakdown")}</h3>
                <div className="space-y-3">
                  <BreakdownBar label={t("dashboard.safe")} count={data.breakdown.safe} total={data.total_scans} color="bg-sage-400" />
                  <BreakdownBar label={t("dashboard.careful")} count={data.breakdown.caution} total={data.total_scans} color="bg-terracotta-400" />
                  <BreakdownBar label={t("dashboard.risky")} count={data.breakdown.dangerous} total={data.total_scans} color="bg-rust-500" />
                </div>
              </Card>

              {/* Recent scans */}
              {data.recent_scans && data.recent_scans.length > 0 && (
                <Card className="p-5">
                  <h3 className="mb-3 font-heading text-base font-semibold text-ink-800">{t("dashboard.recent")}</h3>
                  <div className="space-y-2">
                    {data.recent_scans.slice(0, 5).map((s, i) => (
                      <HistoryRow key={i} item={s} />
                    ))}
                  </div>
                </Card>
              )}

              <Button onClick={() => onNavigate("/incident")} variant="outline" fullWidth>
                {t("dashboard.needHelp")}
              </Button>
              <p className="text-center font-body text-xs text-dustyblue-500">
                {t("dashboard.savedHere")}{" "}
                <button onClick={handleClear} className="underline hover:text-terracotta-600">{t("dashboard.clear")}</button>
              </p>
            </div>
          )}

          {tab === "history" && (
            <Card className="p-5">
              {history && history.length > 0 ? (
                <div className="space-y-2">
                  {history.map((s, i) => <HistoryRow key={i} item={s} />)}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <IconHistory className="mx-auto mb-3 h-10 w-10 text-dustyblue-400" />
                  <p className="font-body text-sm text-dustyblue-600">{t("dashboard.noHistory")}</p>
                </div>
              )}
            </Card>
          )}
      </div>
    </div>
  );
}

function BreakdownBar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <span className="font-body text-sm text-ink-700">{label}</span>
        <span className="font-body text-sm font-semibold text-ink-800">{count}</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-cream-200">
        <div className={`h-full rounded-full ${color} transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

const TYPE_LABELS: Record<string, string> = {
  url: "Link", message: "Message", screenshot: "Screenshot", qr_upi: "QR payment",
  qr_url: "QR link", qr_text: "QR code", file: "File", email: "Email",
};

function HistoryRow({ item }: { item: ScanHistoryItem }) {
  const { t, lang } = useI18n();
  const tone = verdictTone(item.verdict);
  const cls = toneClasses(tone);
  const date = item.timestamp ? new Date(item.timestamp).toLocaleDateString(lang === "tcy" ? "kn" : lang, { month: "short", day: "numeric" }) : "";
  return (
    <div className="flex items-center gap-3 rounded-xl bg-cream-100 p-3">
      <div className={`h-2.5 w-2.5 shrink-0 rounded-full ${riskBarColor(tone)}`} />
      <div className="flex-1 min-w-0">
        <p className="truncate font-body text-sm font-semibold text-ink-800">{item.summary || item.type}</p>
        <p className="font-body text-xs text-dustyblue-600">{TYPE_LABELS[item.type] ? t(`dashboard.types.${item.type}`) : item.type} {date && `· ${date}`}</p>
      </div>
      <span className={`shrink-0 rounded-lg px-2 py-0.5 font-body text-xs font-semibold ${cls.bg} ${cls.text}`}>
        {t(toneTagKey(tone))}
      </span>
    </div>
  );
}
