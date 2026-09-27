// Translated content that normally comes from the server in English.
export interface IncidentText { label: string; steps: string[] }
export interface ScamText { category: string; title: string; how_it_works: string; red_flags: string[]; what_to_do: string }

export interface LangContent {
  /** English server message template -> translated template (same {placeholders}) */
  server: Record<string, string>;
  /** incident id -> translated label + steps */
  incidents: Record<string, IncidentText>;
  /** scam library id -> translated entry */
  scams: Record<string, ScamText>;
}
