// Scan history kept in THIS browser only, so each visitor sees just their own
// checks, and history survives the Render server going to sleep.
import type { ScanHistoryItem } from "./types";

const HISTORY_KEY = "staysafe.history.v1";
const CLIENT_ID_KEY = "staysafe.clientId.v1";
const MAX_ITEMS = 200;

let memoryHistory: ScanHistoryItem[] = [];
let memoryClientId: string | null = null;

function randomId(): string {
  try {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) return crypto.randomUUID().replace(/-/g, "");
  } catch { /* fall through */ }
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export function getClientId(): string {
  try {
    let id = localStorage.getItem(CLIENT_ID_KEY);
    if (!id) {
      id = randomId();
      localStorage.setItem(CLIENT_ID_KEY, id);
    }
    return id;
  } catch {
    if (!memoryClientId) memoryClientId = randomId();
    return memoryClientId;
  }
}

export function loadHistory(): ScanHistoryItem[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return memoryHistory;
  }
}

export function addHistory(item: ScanHistoryItem): void {
  const next = [item, ...loadHistory()].slice(0, MAX_ITEMS); // newest first
  memoryHistory = next;
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(next));
  } catch { /* storage full or blocked: keep in memory */ }
}

export function clearHistory(): void {
  memoryHistory = [];
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch { /* ignore */ }
}

const DANGER = ["DANGEROUS", "SCAM_LIKELY"];
const CAUTION = ["CAUTION", "SUSPICIOUS", "UNCERTAIN"];

// Same scoring as the backend: start at 100, deduct for risky finds in the last 50 checks.
export function computeDashboard(history: ScanHistoryItem[]) {
  const recent = history.slice(0, 50);
  const dangerous = recent.filter((s) => DANGER.includes(String(s.verdict))).length;
  const caution = recent.filter((s) => CAUTION.includes(String(s.verdict))).length;
  const safe = recent.length - dangerous - caution;
  const score = Math.max(0, 100 - dangerous * 8 - caution * 3);
  const label = score >= 80 ? "Good" : score >= 50 ? "Needs Attention" : "At Risk";
  return {
    safety_score: score,
    safety_label: label,
    total_scans: history.length,
    breakdown: { dangerous, caution, safe },
    recent_scans: history.slice(0, 10),
  };
}
