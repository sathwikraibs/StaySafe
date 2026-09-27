import { useState } from "react";
import { useI18n } from "@/i18n";
import type { VirusTotalInfo } from "@/types";
import { IconArrowRight, IconChevronRight } from "@/icons";

/** Ring showing how many security companies flagged the file, like VirusTotal's score. */
function DetectionRing({ flagged, total }: { flagged: number; total: number }) {
  const r = 42;
  const c = 2 * Math.PI * r;
  const part = total ? flagged / total : 0;
  const color = flagged === 0 ? "#647A4F" : flagged < 3 ? "#C57A5E" : "#A84A3A";
  return (
    <div className="relative h-28 w-28 shrink-0">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#EFE3D0" strokeWidth="10" />
        <circle
          cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={`${Math.max(flagged ? 6 : 0, part * c)} ${c}`}
          className="ring-draw"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-heading text-3xl font-bold leading-none" style={{ color }}>{flagged}</span>
        <span className="mt-0.5 font-body text-xs font-bold text-dustyblue-600">/ {total}</span>
      </div>
    </div>
  );
}

const CAT_STYLE: Record<string, string> = {
  malicious: "bg-rust-500 text-cream-50",
  suspicious: "bg-terracotta-400 text-cream-50",
  harmless: "bg-sage-200 text-sage-700",
  undetected: "bg-sage-100 text-sage-700",
};

export function VirusTotalPanel({ vt }: { vt?: VirusTotalInfo }) {
  const { t } = useI18n();
  const [showAll, setShowAll] = useState(false);
  if (!vt || vt.state === "off") return null;

  if (vt.state !== "found") {
    const key = vt.state === "not_found" ? "vt.notSeen" : vt.state === "queued" ? "vt.queued" : vt.state === "too_big" ? "vt.tooBig" : "vt.busy";
    return (
      <div className="rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60 p-5">
        <h3 className="font-heading text-lg font-semibold text-ink-900">{t("vt.title")}</h3>
        <p className="mt-2 font-body text-sm text-ink-700">{t(key)}</p>
        {vt.link && (
          <a href={vt.link} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-1.5 font-body text-sm font-bold text-dustyblue-600 underline underline-offset-2">
            {t("vt.open")} <IconArrowRight className="h-4 w-4" />
          </a>
        )}
      </div>
    );
  }

  const flagged = (vt.malicious ?? 0) + (vt.suspicious ?? 0);
  const total = vt.total ?? 0;
  const engines = vt.engines ?? [];
  const shown = showAll ? engines : engines.slice(0, Math.max(8, engines.filter((e) => e.category === "malicious" || e.category === "suspicious").length));
  const bad = flagged > 0;

  return (
    <div className="overflow-hidden rounded-2xl bg-cream-50 shadow-warm animate-fade-up">
      <div className={`flex items-center gap-4 p-5 ${bad ? "bg-rust-400/10" : "bg-sage-100"}`}>
        <DetectionRing flagged={flagged} total={total} />
        <div className="min-w-0">
          <p className="font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600">{t("vt.title")}</p>
          <p className={`mt-1 font-heading text-lg font-bold leading-snug ${bad ? "text-rust-600" : "text-sage-700"}`}>
            {bad ? t("vt.flagged", { n: flagged, total }) : t("vt.clean", { total })}
          </p>
          {vt.threat_label && (
            <p className="mt-1.5 inline-block rounded-lg bg-rust-500 px-2 py-0.5 font-mono text-xs text-cream-50">{vt.threat_label}</p>
          )}
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 border-b border-cream-200 px-5 py-4 sm:grid-cols-4">
        {[
          [t("vt.type"), vt.type_description],
          [t("vt.firstSeen"), vt.first_seen],
          [t("vt.lastScan"), vt.last_analysis],
          [t("vt.submitted"), vt.times_submitted ? String(vt.times_submitted) : ""],
        ].filter(([, v]) => v).map(([k, v]) => (
          <div key={k}>
            <dt className="font-body text-[11px] font-bold uppercase tracking-wide text-dustyblue-500">{k}</dt>
            <dd className="font-body text-sm font-semibold text-ink-800">{v}</dd>
          </div>
        ))}
      </dl>

      {engines.length > 0 && (
        <div className="px-5 py-4">
          <p className="mb-2.5 font-heading text-base font-semibold text-ink-900">{t("vt.engines")}</p>
          <ul className="grid gap-1.5 sm:grid-cols-2">
            {shown.map((e) => (
              <li key={e.name} className="flex items-center justify-between gap-2 rounded-lg bg-cream-100 px-3 py-2">
                <span className="truncate font-body text-sm font-semibold text-ink-800">{e.name}</span>
                <span className={`max-w-[55%] truncate rounded-md px-2 py-0.5 font-body text-[11px] font-bold ${CAT_STYLE[e.category] ?? "bg-cream-200 text-ink-700"}`}>
                  {e.result || t(`vt.cat.${e.category}`)}
                </span>
              </li>
            ))}
          </ul>
          {engines.length > shown.length && (
            <button onClick={() => setShowAll(true)} className="mt-3 flex items-center gap-1 font-body text-sm font-bold text-dustyblue-600">
              <IconChevronRight className="h-4 w-4" /> {t("vt.showAll", { n: engines.length })}
            </button>
          )}
        </div>
      )}

      {vt.link && (
        <a href={vt.link} target="_blank" rel="noopener noreferrer" className="flex items-center justify-between border-t border-cream-200 px-5 py-3 font-body text-sm font-bold text-dustyblue-600 hover:bg-cream-100">
          {t("vt.open")} <IconArrowRight className="h-4 w-4" />
        </a>
      )}
    </div>
  );
}
