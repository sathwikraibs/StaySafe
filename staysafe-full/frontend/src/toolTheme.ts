// Each tool has its own colour, so pages, tiles and animations are easy to tell apart.
export interface ToolTheme {
  /** soft background */
  soft: string;
  /** strong colour for icons and text */
  ink: string;
  /** gradient for the icon tile */
  from: string;
  to: string;
}

export const TOOL_THEMES: Record<string, ToolTheme> = {
  "/scan-url": { soft: "#DCEBEA", ink: "#2F6E70", from: "#5C9A9B", to: "#2F6E70" },
  "/scan-message": { soft: "#E3EBDC", ink: "#4D6039", from: "#8AA173", to: "#4D6039" },
  "/scan-qr": { soft: "#ECE3F0", ink: "#6E4E7C", from: "#A283B0", to: "#6E4E7C" },
  "/scan-file": { soft: "#F5EAD2", ink: "#86621A", from: "#D2A649", to: "#86621A" },
  "/check-password": { soft: "#F4E1D8", ink: "#A85F47", from: "#DB9B7D", to: "#A85F47" },
  "/check-network": { soft: "#DDE6EB", ink: "#3E5862", from: "#7F9DA9", to: "#3E5862" },
  "/check-number": { soft: "#DCE6F0", ink: "#365E86", from: "#7A9CC0", to: "#365E86" },
  "/scan-email": { soft: "#F3DFDF", ink: "#944A4A", from: "#CF8A86", to: "#944A4A" },
  "/dashboard": { soft: "#E0E8DA", ink: "#3A4A2C", from: "#7E9168", to: "#3A4A2C" },
  "/scam-library": { soft: "#E2E4F1", ink: "#48548F", from: "#8792C6", to: "#48548F" },
};

export const DEFAULT_THEME: ToolTheme = TOOL_THEMES["/scan-message"];

export function themeFor(path: string): ToolTheme {
  return TOOL_THEMES[path] ?? DEFAULT_THEME;
}
