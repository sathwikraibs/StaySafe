import { useState } from "react";
import { useI18n } from "@/i18n";
import type { VirusTotalInfo } from "@/types";
import { IconShield } from "@/icons";
import { Section } from "@/components/Section";

/** Ring showing how many security companies flagged it, like VirusTotal's score. */
function DetectionRing({ flagged, total }: { flagged: number; total: number }) {
  const r = 42;
  const c = 2 * Math.PI * r;
  const part = total ? flagged / total : 0;
  const color = flagged === 0 ? "#22905C" : flagged < 3 ? "#D98324" : "#CC3A2E";
  return (
    <div className="relative h-24 w-24 shrink-0">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#E6E8F1" strokeWidth="10" />
        <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="10" strokeLinecap="round"
          strokeDasharray={`${Math.max(flagged ? 6 : 0, part * c)} ${c}`} className="ring-draw" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-heading text-2xl font-bold leading-none" style={{ color }}>{flagged}</span>
        <span className="mt-0.5 font-body text-xs font-bold text-dustyblue-600">/ {total}</span>
      </div>
    </div>
  );
}

const CAT_STYLE: Record<string, string> = {
  malicious: "bg-rust-500 text-cream-50",
  suspicious: "bg-terracotta-400 text-cream-50",
  harmless: "bg-sage-200 text-sage-700",
  undetected: "bg-cream-200 text-ink-700",
};
const BAR: ["malicious" | "suspicious" | "harmless" | "undetected", string][] = [
  ["malicious", "bg-rust-500"], ["suspicious", "bg-terracotta-400"], ["harmless", "bg-sage-400"], ["undetected", "bg-cream-300"],
];

/**
 * The full VirusTotal result shown right here: the count, what kind of thing it is, when it
 * was first seen, and what every security company said. Nothing to open elsewhere.
 */
export function VirusTotalPanel({ vt, kind = "file" }: { vt?: VirusTotalInfo; kind?: "file" | "link" }) {
  const { t } = useI18n();
  const [showAll, setShowAll] = useState(false);
  // Nothing to say when the service didn't answer: other checks cover it.
  if (!vt || vt.state === "off" || vt.state === "busy" || vt.state === "error") return null;

  if (vt.state !== "found") {
    if (kind === "link") return null;
    const key = vt.state === "not_found" ? "vt.notSeen" : vt.state === "queued" ? "vt.queued" : "vt.tooBig";
    return (
      <Section icon={<IconShield className="h-5 w-5" />} title={t("vt.title")} tone="info" summary={t("vt.newFile")} defaultOpen>
        <p className="font-body text-sm text-ink-800">{t(key)}</p>
      </Section>
    );
  }

  const flagged = (vt.malicious ?? 0) + (vt.suspicious ?? 0);
  const total = vt.total ?? 0;
  const engines = vt.engines ?? [];
  const bad = engines.filter((e) => e.category === "malicious" || e.category === "suspicious");
  const shown = showAll ? engines : bad.length ? bad : engines.slice(0, 6);
  const tone = flagged === 0 ? "good" : flagged < 3 ? "warn" : "bad";
  const facts: [string, string | undefined][] = [
    [t("vt.type"), vt.type_description],
    [t("vt.firstSeen"), vt.first_seen],
    [t("vt.lastScan"), vt.last_analysis],
    [t("vt.submitted"), vt.times_submitted ? String(vt.times_submitted) : undefined],
    [t("vt.categories"), vt.categories && vt.categories.length ? vt.categories.join(", ") : undefined],
    [t("vt.pageTitle"), vt.title || undefined],
    [t("vt.names"), vt.names && vt.names.length ? vt.names.slice(0, 3).join(", ") : undefined],
  ];

  return (
    <Section icon={<IconShield className="h-5 w-5" />} title={t("vt.title")} tone={tone}
      summary={`${flagged}/${total}`} defaultOpen={flagged > 0 || kind === "file"}>
      <div className="flex items-center gap-4">
        <DetectionRing flagged={flagged} total={total} />
        <div className="min-w-0">
          <p className={`font-heading text-base font-bold leading-snug ${flagged ? "text-rust-600" : "text-sage-700"}`}>
            {flagged ? t(kind === "file" ? "vt.flagged" : "vt.flaggedLink", { n: flagged, total }) : t(kind === "file" ? "vt.clean" : "vt.cleanLink", { total })}
          </p>
          {vt.scope === "website" && <p className="mt-1 font-body text-xs text-dustyblue-600">{t("vt.websiteScope")}</p>}
          {vt.threat_label && <p className="mt-1.5 inline-block rounded-md bg-rust-500 px-2 py-0.5 font-mono text-xs text-cream-50">{vt.threat_label}</p>}
        </div>
      </div>

      {/* how the answers split */}
      {total > 0 && (
        <div className="mt-4">
          <div className="flex h-2.5 overflow-hidden rounded-full bg-cream-200">
            {BAR.map(([k, cls]) => {
              const n = Number(vt[k] ?? 0);
              return n ? <span key={k} className={`h-full ${cls}`} style={{ width: `${(n / total) * 100}%` }} /> : null;
            })}
          </div>
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
            {BAR.map(([k, cls]) => (
              <span key={k} className="flex items-center gap-1.5 font-body text-xs text-ink-700">
                <span className={`h-2.5 w-2.5 rounded-full ${cls}`} />{t(`vt.cat.${k}`)}: <b>{Number(vt[k] ?? 0)}</b>
              </span>
            ))}
          </div>
        </div>
      )}

      {facts.some(([, v]) => v) && (
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2.5 rounded-xl bg-cream-100/70 p-3 sm:grid-cols-3">
          {facts.filter(([, v]) => v).map(([k, v]) => (
            <div key={k} className="min-w-0">
              <dt className="font-body text-[11px] font-bold uppercase tracking-wide text-dustyblue-500">{k}</dt>
              <dd className="break-words font-body text-sm font-semibold text-ink-800">{v}</dd>
            </div>
          ))}
        </dl>
      )}

      {engines.length > 0 && (
        <div className="mt-4">
          <p className="mb-2 font-heading text-sm font-bold text-ink-900">{t("vt.engines")}</p>
          <ul className="grid gap-1.5 sm:grid-cols-2">
            {shown.map((e) => (
              <li key={e.name} className="flex items-center justify-between gap-2 rounded-lg bg-cream-100 px-3 py-1.5">
                <span className="truncate font-body text-sm font-semibold text-ink-800">{e.name}</span>
                <span className={`max-w-[55%] truncate rounded-md px-2 py-0.5 font-body text-[11px] font-bold ${CAT_STYLE[e.category] ?? "bg-cream-200 text-ink-700"}`}>
                  {e.category === "malicious" || e.category === "suspicious" ? (e.result || t(`vt.cat.${e.category}`)) : t(`vt.cat.${e.category}`)}
                </span>
              </li>
            ))}
          </ul>
          {engines.length > shown.length || showAll ? (
            <button type="button" onClick={() => setShowAll(!showAll)} className="mt-2.5 flex items-center gap-1 font-body text-sm font-bold text-dustyblue-600">
              <svg viewBox="0 0 24 24" className={`h-4 w-4 transition-transform ${showAll ? "-rotate-90" : ""}`}><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" /></svg>
              {showAll ? t("vt.showLess") : t("vt.showAll", { n: engines.length })}
            </button>
          ) : null}
        </div>
      )}
    </Section>
  );
}
