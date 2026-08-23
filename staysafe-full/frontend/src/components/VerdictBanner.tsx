import { verdictTone, verdictLabel, toneClasses } from "@/verdict";
import { IconCheck, IconWarning, IconAlert } from "@/icons";
import type { Verdict } from "@/types";

interface VerdictBannerProps {
  verdict: Verdict | string;
  riskScore?: number;
}

export function VerdictBanner({ verdict, riskScore }: VerdictBannerProps) {
  const tone = verdictTone(verdict);
  const cls = toneClasses(tone);

  const Icon = tone === "safe" ? IconCheck : tone === "caution" ? IconWarning : IconAlert;

  return (
    <div className={`flex items-start gap-4 rounded-2xl border-2 ${cls.border} ${cls.bg} p-5 animate-fade-up`}>
      <div className={`shrink-0 ${cls.icon}`}>
        <Icon className="h-7 w-7" />
      </div>
      <div className="flex-1">
        <p className={`font-heading text-xl font-semibold ${cls.text}`}>{verdictLabel(verdict)}</p>
        {typeof riskScore === "number" && (
          <p className="mt-1 font-body text-sm text-ink-700/70">
            Risk score: {riskScore} out of 100
          </p>
        )}
      </div>
    </div>
  );
}
