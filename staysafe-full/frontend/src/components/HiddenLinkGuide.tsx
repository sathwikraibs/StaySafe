import { useI18n } from "@/i18n";
import { IconLink, IconChevronRight } from "@/icons";

/**
 * Explains that links hidden behind words like "Click here" can't be seen in a
 * screenshot or copied text, and how to copy the real link safely.
 */
export function HiddenLinkGuide({ onNavigate, defaultOpen = false, showLinkButton = true }: {
  onNavigate?: (path: string) => void;
  defaultOpen?: boolean;
  showLinkButton?: boolean;
}) {
  const { t, tl } = useI18n();
  return (
    <details open={defaultOpen} className="group rounded-2xl border-2 border-dustyblue-200 bg-dustyblue-100/60">
      <summary className="flex cursor-pointer list-none items-start gap-3 p-4 [&::-webkit-details-marker]:hidden">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-dustyblue-200 text-dustyblue-600">
          <IconLink className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <p className="font-heading text-base font-semibold text-ink-800">{t("hiddenLink.title")}</p>
          <p className="mt-0.5 font-body text-sm text-dustyblue-600">{t("hiddenLink.summary")}</p>
        </div>
        <IconChevronRight className="mt-1 h-5 w-5 shrink-0 text-dustyblue-400 transition-transform group-open:rotate-90" />
      </summary>

      <div className="space-y-3 px-4 pb-4">
        <p className="font-body text-sm text-ink-700">{t("hiddenLink.why")}</p>
        <p className="rounded-xl bg-rust-400/15 px-3 py-2 font-body text-sm font-semibold text-rust-600">{t("hiddenLink.warning")}</p>
        <p className="font-body text-sm font-semibold text-ink-800">{t("hiddenLink.stepsTitle")}</p>
        <ol className="space-y-2">
          {tl("hiddenLink.steps").map((step, i) => (
            <li key={i} className="flex items-start gap-3 font-body text-sm text-ink-700">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-200 font-heading text-xs font-bold text-brand-700">{i + 1}</span>
              <span className="pt-0.5">{step}</span>
            </li>
          ))}
        </ol>
        {showLinkButton && onNavigate && (
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              onClick={() => onNavigate("/scan-url")}
              className="btn-press rounded-xl bg-brand-400 px-4 py-2.5 font-body text-sm font-bold text-cream-50 hover:bg-brand-500"
            >
              {t("hiddenLink.goLink")}
            </button>
            <button
              onClick={() => onNavigate("/scan-email")}
              className="btn-press rounded-xl border-2 border-brand-300 bg-cream-50 px-4 py-2.5 font-body text-sm font-bold text-brand-700 hover:bg-brand-100"
            >
              {t("hiddenLink.goEmail")}
            </button>
          </div>
        )}
      </div>
    </details>
  );
}
