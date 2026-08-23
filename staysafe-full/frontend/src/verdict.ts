import type { Verdict } from "./types";

export type Tone = "safe" | "caution" | "danger";

export function verdictTone(v: Verdict | string | undefined): Tone {
  const s = (v || "").toUpperCase();
  if (s === "SAFE" || s === "LIKELY_SAFE") return "safe";
  if (s === "CAUTION" || s === "SUSPICIOUS") return "caution";
  return "danger";
}

export function verdictLabel(v: Verdict | string | undefined): string {
  const s = (v || "").toUpperCase();
  switch (s) {
    case "SAFE": return "This looks safe";
    case "LIKELY_SAFE": return "This looks safe";
    case "CAUTION": return "Be careful with this";
    case "SUSPICIOUS": return "Be careful with this";
    case "DANGEROUS": return "This looks risky";
    case "SCAM_LIKELY": return "This looks risky";
    default: return "Hmm, we could not tell";
  }
}

export function toneClasses(tone: Tone): { bg: string; text: string; border: string; icon: string } {
  switch (tone) {
    case "safe":
      return {
        bg: "bg-sage-100",
        text: "text-sage-700",
        border: "border-sage-300",
        icon: "text-sage-600",
      };
    case "caution":
      return {
        bg: "bg-terracotta-300/30",
        text: "text-terracotta-700",
        border: "border-terracotta-300",
        icon: "text-terracotta-600",
      };
    case "danger":
      return {
        bg: "bg-rust-400/15",
        text: "text-rust-600",
        border: "border-rust-400",
        icon: "text-rust-500",
      };
  }
}

export function riskBarColor(tone: Tone): string {
  switch (tone) {
    case "safe": return "bg-sage-400";
    case "caution": return "bg-terracotta-400";
    case "danger": return "bg-rust-500";
  }
}
