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
  "/scan-message": { soft: "#E0F4F1", ink: "#0E6E69", from: "#2CB3A6", to: "#0F7C77" },
  "/scan-url": { soft: "#E5EAFE", ink: "#2D3FB0", from: "#6382F8", to: "#3346C8" },
  "/scan-qr": { soft: "#EEE8FC", ink: "#5737B0", from: "#9D7DEB", to: "#6744C7" },
  "/scan-file": { soft: "#FDF1DA", ink: "#8C5409", from: "#F0B240", to: "#C77A10" },
  "/check-number": { soft: "#E1F0FC", ink: "#185F9F", from: "#43A4E9", to: "#1C6FBF" },
  "/scan-email": { soft: "#FDE8E2", ink: "#A9402A", from: "#F28B6E", to: "#D0533A" },
  "/check-password": { soft: "#FCE6EE", ink: "#A2305B", from: "#EC709C", to: "#C13D6E" },
  "/check-network": { soft: "#DFF3F7", ink: "#1A6B82", from: "#47B7D0", to: "#1E7E99" },
  "/scam-library": { soft: "#ECEDFE", ink: "#3730A3", from: "#7578DD", to: "#3730A3" },
  "/dashboard": { soft: "#E3F4EB", ink: "#16673F", from: "#4FB07F", to: "#1A784B" },
};

export const DEFAULT_THEME: ToolTheme = TOOL_THEMES["/scam-library"];

export function themeFor(path: string): ToolTheme {
  return TOOL_THEMES[path] ?? DEFAULT_THEME;
}
