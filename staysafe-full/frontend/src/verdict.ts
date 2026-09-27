import type { Verdict } from "./types";

export type Tone = "safe" | "caution" | "danger";

export function verdictTone(v: Verdict | string | undefined): Tone {
  const s = (v || "").toUpperCase();
  if (s === "SAFE" || s === "LIKELY_SAFE") return "safe";
  if (s === "CAUTION" || s === "SUSPICIOUS" || s === "UNCERTAIN") return "caution";
  return "danger";
}

/** Translation key for the verdict headline. */
export function verdictLabelKey(v: Verdict | string | undefined): string {
  const s = (v || "").toUpperCase();
  if (s === "SAFE" || s === "LIKELY_SAFE") return "verdict.safe";
  if (s === "CAUTION" || s === "SUSPICIOUS") return "verdict.caution";
  if (s === "DANGEROUS" || s === "SCAM_LIKELY") return "verdict.danger";
  if (s === "UNCERTAIN") return "verdict.uncertain";
  return "verdict.unknown";
}

/** Translation key for the short Safe / Careful / Risky tag. */
export function toneTagKey(tone: Tone): string {
  return tone === "safe" ? "common.safe" : tone === "caution" ? "common.careful" : "common.risky";
}

export function toneClasses(tone: Tone): { bg: string; text: string; border: string; icon: string } {
  switch (tone) {
    case "safe":
      return { bg: "bg-sage-100", text: "text-sage-700", border: "border-sage-300", icon: "text-sage-600" };
    case "caution":
      return { bg: "bg-terracotta-300/30", text: "text-terracotta-700", border: "border-terracotta-300", icon: "text-terracotta-600" };
    case "danger":
      return { bg: "bg-rust-400/15", text: "text-rust-600", border: "border-rust-400", icon: "text-rust-500" };
  }
}

export function riskBarColor(tone: Tone): string {
  switch (tone) {
    case "safe": return "bg-sage-400";
    case "caution": return "bg-terracotta-400";
    case "danger": return "bg-rust-500";
  }
}
