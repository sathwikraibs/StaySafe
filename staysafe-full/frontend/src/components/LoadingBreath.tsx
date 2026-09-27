import { useEffect, useState } from "react";
import { useI18n } from "@/i18n";

export function LoadingBreath({ label }: { label?: string }) {
  // The free Render server sleeps when idle; tell people why the first check is slow.
  const { t } = useI18n();
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setSlow(true), 8000);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center gap-5 py-12">
      <div className="relative flex h-24 w-24 items-center justify-center">
        <div className="absolute h-20 w-20 rounded-full bg-sage-300/50 animate-breath" />
        <div className="absolute h-14 w-14 rounded-full bg-sage-400/60 animate-breath-delayed" />
        <div className="absolute h-8 w-8 rounded-full bg-sage-500/70 animate-breath" />
      </div>
      {label && (
        <p className="font-body text-base text-dustyblue-600 animate-pulse">{label}</p>
      )}
      {slow && (
        <p className="max-w-xs text-center font-body text-sm text-dustyblue-500">
          {t("loading.slow")}
        </p>
      )}
    </div>
  );
}
