export type Verdict =
  | "SAFE" | "CAUTION" | "DANGEROUS"
  | "LIKELY_SAFE" | "SUSPICIOUS" | "SCAM_LIKELY" | "UNCERTAIN";

export interface ScanUrlResponse {
  url: string;
  risk_score: number;
  verdict: Verdict;
  findings: string[];
}

export interface ScanMessageResponse {
  risk_score: number;
  verdict: Verdict;
  patterns_detected: string[];
  safe_signals?: string[];
  text_analyzed?: string;
  links_checked?: LinkCheck[];
  /** extra information: language coverage, hidden-link tip */
  notes?: string[];
  /** "What this message says" — automatic translation into the website language */
  translation?: { text: string; from: string; to: string; provider?: string };
}

export interface LinkCheck {
  url: string;
  verdict: Verdict;
  risk_score: number;
  findings: string[];
}

export interface ScanQrResponse {
  risk_score: number;
  verdict: Verdict;
  findings: string[];
  qr_type: string;
  raw_data: string;
}

export interface ScanFileResponse {
  filename: string;
  sha256: string;
  detected_type?: string;
  risk_score: number;
  verdict: Verdict;
  findings: string[];
}

export interface CheckPasswordResponse {
  risk_score: number;
  verdict: Verdict;
  strength_label: string;
  breached: boolean;
  breach_count: number;
  findings: string[];
}

export interface CheckNetworkResponse {
  risk_score: number;
  verdict: Verdict;
  findings: string[];
  ip: string;
  isp: string;
  location: string;
}

export interface ScanEmailResponse {
  from: string;
  reply_to: string;
  links_found: string[];
  links: string[];
  risk_score: number;
  verdict: Verdict;
  findings: string[];
}

export interface DashboardResponse {
  safety_score: number;
  safety_label: string;
  total_scans: number;
  breakdown: { dangerous: number; caution: number; safe: number };
  recent_scans: ScanHistoryItem[];
}

export interface ScanHistoryItem {
  type: string;
  timestamp: string;
  risk_score: number;
  verdict: Verdict;
  summary: string;
}

export interface HistoryResponse {
  history: ScanHistoryItem[];
}

export interface IncidentOption {
  id: string;
  label: string;
}

export interface IncidentPlanResponse {
  incident_type: string;
  label: string;
  action_plan: string[];
}

export interface ScamEntry {
  id: string;
  category: string;
  title: string;
  how_it_works: string;
  red_flags: string[];
  what_to_do: string;
}

export interface ScamLibraryResponse {
  count: number;
  scams: ScamEntry[];
}

export interface CategoriesResponse {
  categories: string[];
}
