import { useEffect, useState } from "react";
import { apiGet } from "@/api";
import { API_BASE } from "@/config";

export interface RatingSummary {
  count: number;
  average: number;
  stars: Record<"1" | "2" | "3" | "4" | "5", number>;
  reviews: { id: string; stars: number; text: string; lang: string; at: number }[];
}

/** Shown only once enough people have rated, so a page never says "1 rating". */
export const MIN_TO_SHOW = 3;
let cached: Promise<RatingSummary | null> | null = null;

/** The average stars and shared reviews (one request per visit). */
export function useRatingSummary(): RatingSummary | null {
  const [value, setValue] = useState<RatingSummary | null>(null);
  useEffect(() => {
    if (!cached) cached = apiGet<RatingSummary>(`${API_BASE}/api/feedback/summary`).catch(() => null);
    let alive = true;
    void cached.then((v) => { if (alive) setValue(v); });
    return () => { alive = false; };
  }, []);
  return value;
}

/** After someone rates, the next look gets fresh numbers. */
export function forgetRatingSummary(): void {
  cached = null;
}
