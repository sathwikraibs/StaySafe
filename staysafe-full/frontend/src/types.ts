export type Verdict =
  | "SAFE" | "CAUTION" | "DANGEROUS"
  | "LIKELY_SAFE" | "SUSPICIOUS" | "SCAM_LIKELY" | "UNCERTAIN";

export type CheckStatus = "pass" | "warn" | "fail" | "info" | "skip";

/** One line of the "What we checked" list. Text comes from checks.<id>.<status> in the language files. */
export interface Check {
  id: string;
  status: CheckStatus;
  value?: string | number | null;
}

export interface ScanUrlResponse {
  url: string;
  risk_score: number;
  verdict: Verdict;
  findings: string[];
  checks?: Check[];
  details?: {
    domain: string;
    registered_domain: string;
    final_url: string;
    page_title: string;
    age_days: number | null;
    ip: string;
  };
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
  checks?: Check[];
}

export interface ScanQrResponse {
  risk_score: number;
  verdict: Verdict;
  findings: string[];
  qr_type: string;
  raw_data: string;
  checks?: Check[];
  details?: ScanUrlResponse["details"];
  payee?: string;
  payee_name?: string;
  amount?: string;
}

export interface ScanFileResponse {
  filename: string;
  sha256: string;
  detected_type?: string;
  size?: number;
  checks?: Check[];
  risk_score: number;
  verdict: Verdict;
  findings: string[];
}

export interface CheckPasswordResponse {
  risk_score: number;
  verdict: Verdict;
  strength_label: string;
  breached: boolean | null;
  breach_count: number;
  findings: string[];
  checks?: Check[];
  strength_score?: number;
  length?: number;
}

export interface CheckNetworkResponse {
  risk_score: number;
  verdict: Verdict;
  findings: string[];
  ip: string;
  isp: string;
  location: string;
  checks?: Check[];
  ip_version?: string;
  org?: string;
  asn?: string;
  country_code?: string;
  timezone?: string;
}

export interface ScanEmailResponse {
  from: string;
  reply_to: string;
  links_found: string[];
  links: string[];
  subject?: string;
  checks?: Check[];
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
