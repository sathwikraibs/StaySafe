import { useState, type ReactNode } from "react";
import { useI18n } from "@/i18n";
import { useFormatAge } from "@/components/ResultReport";
import { IconGlobe, IconLock, IconShield, IconLink } from "@/icons";
import type { LinkCheck, ScanUrlResponse } from "@/types";
import { verdictTone, toneClasses, toneTagKey } from "@/verdict";
import { IconChevronRight } from "@/icons";

type Details = NonNullable<ScanUrlResponse["details"]>;

function useFormatDate() {
  const { lang } = useI18n();
  return (iso?: string) => {
    if (!iso) return "";
    try {
      return new Intl.DateTimeFormat(lang === "tcy" ? "kn-IN" : `${lang}-IN`, { day: "numeric", month: "short", year: "numeric" })
        .format(new Date(`${iso}T00:00:00`));
    } catch {
      return iso;
    }
  };
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-b border-cream-200/80 py-2 last:border-0 sm:flex-row sm:items-baseline sm:gap-4">
      <dt className="shrink-0 font-body text-xs font-bold uppercase tracking-wide text-dustyblue-600 sm:w-40">{label}</dt>
      <dd className="min-w-0 break-words font-body text-sm text-ink-800">{children}</dd>
    </div>
  );
}

function Panel({ icon, title, tone, badge, children }: {
  icon: ReactNode; title: string; tone: "blue" | "green" | "amber" | "red"; badge?: ReactNode; children: ReactNode;
}) {
  const head = {
    blue: "from-dustyblue-100 to-cream-50 text-dustyblue-600",
    green: "from-sage-100 to-cream-50 text-sage-700",
    amber: "from-terracotta-300/30 to-cream-50 text-terracotta-700",
    red: "from-rust-400/20 to-cream-50 text-rust-600",
  }[tone];
  return (
    <div className="overflow-hidden rounded-2xl border border-cream-200 bg-cream-50 shadow-warm-sm animate-fade-up">
      <div className={`flex items-center gap-2.5 bg-gradient-to-r px-4 py-3 ${head}`}>
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-cream-50/80">{icon}</span>
        <h4 className="flex-1 font-heading text-base font-semibold">{title}</h4>
        {badge}
      </div>
      <dl className="px-4 py-1">{children}</dl>
    </div>
  );
}

/** Created ... today ... expires: a small visual timeline of the website's registration. */
function Timeline({ created, expires }: { created?: string; expires?: string }) {
  const { t } = useI18n();
  const formatDate = useFormatDate();
  if (!created) return null;
  const start = new Date(`${created}T00:00:00`).getTime();
  const end = expires ? new Date(`${expires}T00:00:00`).getTime() : 0;
  const now = Date.now();
  const pct = end > start ? Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100)) : 100;
  return (
    <div className="py-3">
      <div className="relative h-2.5 rounded-full bg-cream-200">
        <div className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-dustyblue-300 to-sage-400 grow-x" style={{ width: `${pct}%` }} />
        <span className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-cream-50 bg-sage-600 shadow" style={{ left: `${pct}%` }} />
      </div>
      <div className="mt-2 flex justify-between gap-2 font-body text-[11px] text-dustyblue-600">
        <span>{t("siteInfo.tlCreated")}<br /><b className="text-ink-800">{formatDate(created)}</b></span>
        <span className="text-center">{t("siteInfo.tlToday")}</span>
        {expires && <span className="text-right">{t("siteInfo.tlEnds")}<br /><b className="text-ink-800">{formatDate(expires)}</b></span>}
      </div>
    </div>
  );
}

/** Everything we found out about a website: address, registration record, certificate and server. */
export function LinkDetails({ details }: { details?: ScanUrlResponse["details"] }) {
  const { t } = useI18n();
  const formatAge = useFormatAge();
  const formatDate = useFormatDate();
  if (!details) return null;
  const d = details as Details;
  const w = d.whois ?? {};
  const c = d.certificate ?? {};
  const srv = d.server ?? {};
  const age = d.age_days ?? w.age_days;
  const hasWhois = Boolean(w.created || w.registrar || w.expires);
  const hasCert = c.valid !== undefined;
  const hasServer = Boolean(d.ip || srv.country || srv.company);

  return (
    <div className="space-y-3">
      <h3 className="px-1 font-heading text-lg font-semibold text-ink-900">{t("siteInfo.title")}</h3>

      <Panel icon={<IconLink className="h-4 w-4" />} title={t("siteInfo.addressTitle")} tone="blue">
        {d.domain && <Row label={t("linkInfo.site")}><span className="font-mono">{d.domain}</span></Row>}
        {d.final_url && <Row label={t("linkInfo.goesTo")}><span className="break-all font-mono text-xs">{d.final_url}</span></Row>}
        {d.page_title && <Row label={t("linkInfo.pageTitle")}>“{d.page_title}”</Row>}
      </Panel>

      <Panel
        icon={<IconShield className="h-4 w-4" />}
        title={t("siteInfo.ownerTitle")}
        tone={age !== null && age !== undefined && age < 180 ? "amber" : "green"}
        badge={age !== null && age !== undefined ? (
          <span className="rounded-full bg-cream-50 px-2.5 py-1 font-body text-xs font-bold">{formatAge(age)}</span>
        ) : undefined}
      >
        {hasWhois ? (
          <>
            <Timeline created={w.created} expires={w.expires} />
            {w.created && <Row label={t("siteInfo.registered")}>{formatDate(w.created)}{age !== null && age !== undefined ? ` (${t("siteInfo.ago", { age: formatAge(age) })})` : ""}</Row>}
            {w.registrar && <Row label={t("siteInfo.registrar")}>{w.registrar}</Row>}
            <Row label={t("siteInfo.owner")}>{!w.org || w.org === "hidden" ? t("siteInfo.ownerHidden") : w.org}</Row>
            {w.country && <Row label={t("siteInfo.country")}>{w.country}</Row>}
            {w.updated && <Row label={t("siteInfo.updated")}>{formatDate(w.updated)}</Row>}
            {w.expires && (
              <Row label={t("siteInfo.expires")}>
                {formatDate(w.expires)}
                {typeof w.expires_in_days === "number" && w.expires_in_days >= 0 && ` (${t("siteInfo.inTime", { age: formatAge(w.expires_in_days) })})`}
              </Row>
            )}
            {w.name_servers && w.name_servers.length > 0 && <Row label={t("siteInfo.nameServers")}><span className="font-mono text-xs">{w.name_servers.join(", ")}</span></Row>}
          </>
        ) : (
          <p className="py-3 font-body text-sm text-ink-700">{t("siteInfo.noWhois")}</p>
        )}
      </Panel>

      <Panel
        icon={<IconLock className="h-4 w-4" />}
        title={t("siteInfo.certTitle")}
        tone={!hasCert ? "amber" : c.valid ? "green" : "red"}
        badge={hasCert ? (
          <span className={`rounded-full px-2.5 py-1 font-body text-xs font-bold ${c.valid ? "bg-sage-500 text-cream-50" : "bg-rust-500 text-cream-50"}`}>
            {c.valid ? t("siteInfo.certValid") : t("siteInfo.certInvalid")}
          </span>
        ) : undefined}
      >
        {hasCert && c.valid ? (
          <>
            {c.issuer && <Row label={t("siteInfo.issuer")}>{c.issuer}</Row>}
            {c.issued_to && <Row label={t("siteInfo.issuedTo")}>{c.issued_to}</Row>}
            {c.valid_from && <Row label={t("siteInfo.validFrom")}>{formatDate(c.valid_from)}</Row>}
            {c.valid_to && (
              <Row label={t("siteInfo.validTo")}>
                {formatDate(c.valid_to)}{typeof c.days_left === "number" ? ` (${t("siteInfo.inTime", { age: formatAge(Math.max(0, c.days_left)) })})` : ""}
              </Row>
            )}
          </>
        ) : hasCert ? (
          <p className="py-3 font-body text-sm text-rust-600">{t("siteInfo.certBroken")}</p>
        ) : (
          <p className="py-3 font-body text-sm text-ink-700">{t("siteInfo.noCert")}</p>
        )}
      </Panel>

      {hasServer && (
        <Panel icon={<IconGlobe className="h-4 w-4" />} title={t("siteInfo.serverTitle")} tone="blue">
          {d.ip && <Row label={t("siteInfo.serverIp")}><span className="font-mono">{d.ip}</span></Row>}
          {(srv.city || srv.country) && <Row label={t("siteInfo.location")}>{[srv.city, srv.country].filter(Boolean).join(", ")}</Row>}
          {srv.company && <Row label={t("siteInfo.company")}>{srv.company}</Row>}
        </Panel>
      )}
    </div>
  );
}

/** Links found inside a message or email: verdict, main reason, and the website details on tap. */
export function CheckedLinks({ links, title, note }: { links: LinkCheck[]; title: string; note?: string }) {
  const { t, ts } = useI18n();
  const [open, setOpen] = useState<string | null>(null);
  if (!links.length) return null;
  return (
    <div className="rounded-2xl bg-cream-50 p-5 shadow-warm">
      <p className="font-heading text-lg font-semibold text-ink-900">{title}</p>
      <ul className="mt-3 space-y-2.5">
        {links.map((link) => {
          const tone = verdictTone(link.verdict);
          const cls = toneClasses(tone);
          const reason = link.findings.find((f) => !f.startsWith("Could not"));
          const isOpen = open === link.url;
          return (
            <li key={link.url} className={`rounded-xl border-2 ${cls.border} ${cls.bg} p-3`}>
              <div className="flex items-start gap-2">
                <span className={`shrink-0 rounded-lg bg-cream-50 px-2 py-0.5 font-body text-xs font-bold ${cls.text}`}>{t(toneTagKey(tone))}</span>
                <span className="min-w-0 break-all font-body text-sm font-semibold text-ink-800">{link.url}</span>
              </div>
              {tone !== "safe" && reason && <p className="mt-1.5 font-body text-sm text-ink-700">{ts(reason)}</p>}
              {link.details && (
                <button
                  type="button"
                  onClick={() => setOpen(isOpen ? null : link.url)}
                  className="mt-2 flex items-center gap-1 font-body text-xs font-bold text-dustyblue-600 hover:text-ink-900"
                >
                  <IconChevronRight className={`h-4 w-4 transition-transform ${isOpen ? "rotate-90" : ""}`} />
                  {isOpen ? t("siteInfo.hide") : t("siteInfo.show")}
                </button>
              )}
              {isOpen && <div className="mt-3"><LinkDetails details={link.details} /></div>}
            </li>
          );
        })}
      </ul>
      {note && <p className="mt-3 font-body text-xs text-dustyblue-600">{note}</p>}
    </div>
  );
}
