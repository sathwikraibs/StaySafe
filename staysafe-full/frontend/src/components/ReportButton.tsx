import { useState } from "react";
import { apiPostJSON } from "@/api";
import { API_BASE } from "@/config";
import { useI18n } from "@/i18n";
import { IconAlert, IconCheck } from "@/icons";

type State = "idle" | "sending" | "sent" | "already" | "limit" | "notReportable" | "unavailable";

/** "Report as scam": builds StaySafe's own list. Shown under link, number and QR results. */
export function ReportButton({ kind, value }: { kind: "link" | "number" | "upi"; value: string }) {
  const { t } = useI18n();
  const [state, setState] = useState<State>("idle");

  async function send() {
    if (state !== "idle") return;
    setState("sending");
    try {
      const r = await apiPostJSON<{ ok: boolean; already?: boolean; reason?: string }>(`${API_BASE}/api/report`, { kind, value });
      if (r.ok) setState(r.already ? "already" : "sent");
      else setState(r.reason === "limit" ? "limit" : r.reason === "not_reportable" ? "notReportable" : "unavailable");
    } catch {
      setState("unavailable");
    }
  }

  const done = state !== "idle" && state !== "sending";
  const good = state === "sent" || state === "already";
  return (
    <div className="rounded-2xl bg-cream-50 p-5 shadow-warm-sm">
      {!done ? (
        <>
          <button
            type="button"
            onClick={send}
            disabled={state === "sending"}
            className="btn-press inline-flex items-center gap-2 rounded-xl border-2 border-rust-400 bg-cream-50 px-4 py-2.5 font-body text-sm font-bold text-rust-600 hover:bg-rust-400/10 disabled:opacity-60"
          >
            <IconAlert className="h-4 w-4" />
            {state === "sending" ? t("common.checking") : t("reportScam.button")}
          </button>
          <p className="mt-2 font-body text-xs text-dustyblue-600">{t("reportScam.note")}</p>
        </>
      ) : (
        <p className={`flex items-start gap-2 font-body text-sm ${good ? "text-sage-700" : "text-dustyblue-600"}`}>
          {good && <IconCheck className="mt-0.5 h-4 w-4 shrink-0" />}
          {t(`reportScam.${state}`)}
        </p>
      )}
    </div>
  );
}
