export type Verdict =
  | "SAFE" | "CAUTION" | "DANGEROUS"
  | "LIKELY_SAFE" | "SUSPICIOUS" | "SCAM_LIKELY" | "UNCERTAIN";

export type CheckStatus = "pass" | "warn" | "fail" | "info" | "skip";

/** One line of the "What we checked" list. Text comes from checks.<id>.<status> in the language files. */
/** One line of the score breakdown: why points were added (or taken away). */
export interface ScorePart {
  label: string;
  points: number;
}

export interface Check {
  id: string;
  status: CheckStatus;
  value?: string | number | null;
}

export interface ScanUrlResponse {
  url: string;
  score_parts?: ScorePart[];
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
    whois?: {
      registrar?: string; org?: string; country?: string; created?: string; updated?: string;
      expires?: string; age_days?: number | null; expires_in_days?: number | null; name_servers?: string[];
    };
    certificate?: {
      valid?: boolean; problem?: string; issuer?: string; issued_to?: string; valid_from?: string;
      valid_to?: string; days_left?: number; cert_age_days?: number;
    };
    server?: { country?: string; city?: string; company?: string };
    virustotal?: VirusTotalInfo | null;
  };
}

export interface ScanMessageResponse {
  score_parts?: ScorePart[];
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
  ai_review?: { verdict: "scam" | "suspicious" | "safe" | "unsure"; category: string; provider: string };
  sender?: string;
}

export interface LinkCheck {
  url: string;
  verdict: Verdict;
  risk_score: number;
  findings: string[];
  checks?: Check[];
  details?: ScanUrlResponse["details"];
}

export interface ScanQrResponse {
  score_parts?: ScorePart[];
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
  md5?: string;
  sha1?: string;
  virustotal?: VirusTotalInfo;
  apk?: { package: string; permissions: string[] } | null;
  links_checked?: LinkCheck[];
  checks?: Check[];
  score_parts?: ScorePart[];
  risk_score: number;
  verdict: Verdict;
  findings: string[];
}

export interface CheckPasswordResponse {
  score_parts?: ScorePart[];
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
  score_parts?: ScorePart[];
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
  links_checked?: LinkCheck[];
  subject?: string;
  from_name?: string;
  mode?: "form" | "source";
  checks?: Check[];
  score_parts?: ScorePart[];
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

export interface VirusTotalInfo {
  state: "found" | "not_found" | "queued" | "busy" | "error" | "off" | "too_big";
  malicious?: number;
  suspicious?: number;
  undetected?: number;
  harmless?: number;
  total?: number;
  engines?: { name: string; category: string; result: string }[];
  threat_label?: string;
  type_description?: string;
  first_seen?: string;
  last_analysis?: string;
  times_submitted?: number | null;
  names?: string[];
  tags?: string[];
  link?: string;
  /** links: "link" = this exact address, "website" = the whole site */
  scope?: "link" | "website";
  categories?: string[];
  reputation?: number | null;
  title?: string;
}
