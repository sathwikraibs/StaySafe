import type { ReactNode } from "react";
import { useI18n } from "@/i18n";
import { WRONG_TOOL } from "@/api";
import { goToTool, isToolId, TOOL_LABEL, type ToolId } from "@/wrongTool";

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="light-pass relative mb-5 overflow-hidden rounded-3xl bg-gradient-to-br from-brand-50 to-cream-50 p-5 shadow-warm-sm ring-1 ring-brand-100 animate-fade-up sm:p-6">
      <span className="header-blob pointer-events-none absolute -right-10 -top-12 h-36 w-36 rounded-full bg-brand-200/40" />
      <div className="relative">
        <h1 className="font-heading text-2xl font-bold leading-tight text-ink-900 sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1.5 font-body text-[15px] leading-snug text-dustyblue-600">{subtitle}</p>}
      </div>
    </div>
  );
}

/** List of result messages. Server messages are translated automatically. */
export function FindingsList({ items, title }: { items: string[]; title?: string }) {
  const { t, ts } = useI18n();
  if (!items || items.length === 0) return null;
  return (
    <div className="mt-4 rounded-2xl bg-cream-100 p-5">
      <h3 className="mb-3 font-heading text-lg font-semibold text-ink-800">{title ?? t("common.whatWeNoticed")}</h3>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 font-body text-sm text-ink-700">
            <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-terracotta-400" />
            <span>{ts(item)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** "Open Check a Link" style button: takes people to the tool their input belongs in. */
export function GoToToolButton({ tool, qrData }: { tool: ToolId; qrData?: string }) {
  const { t } = useI18n();
  return (
    <button type="button" onClick={() => goToTool(tool, qrData)}
      className="btn-press mt-3 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 font-body text-sm font-bold text-cream-50 shadow-warm-sm hover:bg-brand-700">
      {t("wrongTool.open", { tool: t(TOOL_LABEL[tool]) })}
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M5 12h14M13 6l6 6-6 6" /></svg>
    </button>
  );
}

/** "This picture also has a QR code": shown above screenshot and file results. */
export function QrAlsoNotice({ qr }: { qr?: string }) {
  const { t } = useI18n();
  if (!qr) return null;
  return (
    <div className="mb-4 rounded-2xl border border-brand-200 bg-brand-50 p-4 animate-fade-up">
      <p className="font-body text-sm font-semibold text-ink-800">{t("wrongTool.qrInPicture")}</p>
      <GoToToolButton tool="qr" qrData={qr} />
    </div>
  );
}

/** Error box. Plain-text server errors are translated automatically. When the server said the
 *  input belongs in another tool, a button to open that tool is shown under the message. */
export function ErrorNotice({ children }: { children: ReactNode }) {
  const { ts } = useI18n();
  const wrong = typeof children === "string" ? WRONG_TOOL.get(children) : undefined;
  if (wrong && isToolId(wrong.tool)) {
    return (
      <div className="rounded-2xl border border-brand-200 bg-brand-50 p-4 animate-fade-up">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-600 text-cream-50">
            <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M12 8v.01M11 12h1v5h1" /></svg>
          </span>
          <div className="min-w-0 flex-1">
            <p className="font-body text-sm font-semibold text-ink-800">{ts(children as string)}</p>
            <GoToToolButton tool={wrong.tool} qrData={wrong.qrData} />
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-3 rounded-2xl border-2 border-rust-400 bg-rust-400/15 p-4 animate-fade-up">
      <div className="shrink-0 text-rust-500">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5M12 16v.5" />
        </svg>
      </div>
      <p className="font-body text-sm text-rust-600">{typeof children === "string" ? ts(children) : children}</p>
    </div>
  );
}
