import type { ComponentType } from "react";
import {
  IconHome, IconLink, IconMessage, IconQr, IconFile, IconKey,
  IconNetwork, IconEmail, IconDashboard, IconAlert, IconBook, IconHelp,
} from "@/icons";

export interface NavItem {
  path: string;
  label: string;
  icon: ComponentType<{ className?: string; strokeWidth?: number }>;
  short: string;
  /** "urgent" = I clicked a scam (red), "help" = Need help (green) */
  tone?: "urgent" | "help";
}

export const HOME_TOOLS: NavItem[] = [
  { path: "/scan-url", label: "Check a Link", icon: IconLink, short: "Link" },
  { path: "/scan-message", label: "Check a Message", icon: IconMessage, short: "Message" },
  { path: "/scan-qr", label: "Check a QR Code", icon: IconQr, short: "QR Code" },
  { path: "/scan-file", label: "Check a File", icon: IconFile, short: "File" },
  { path: "/check-password", label: "Check a Password", icon: IconKey, short: "Password" },
  { path: "/check-network", label: "Check My Connection", icon: IconNetwork, short: "Connection" },
  { path: "/scan-email", label: "Check an Email", icon: IconEmail, short: "Email" },
  { path: "/dashboard", label: "Safety Dashboard", icon: IconDashboard, short: "Dashboard" },
  { path: "/scam-library", label: "Scam Knowledge Base", icon: IconBook, short: "Learn" },
];

export const HELP_NAV: NavItem[] = [
  { path: "/incident", label: "I Clicked a Scam", icon: IconAlert, short: "Clicked Scam", tone: "urgent" },
  { path: "/help", label: "Need Help?", icon: IconHelp, short: "Help", tone: "help" },
];

export const ALL_NAV: NavItem[] = [
  { path: "/", label: "Home", icon: IconHome, short: "Home" },
  ...HOME_TOOLS,
  ...HELP_NAV,
];

export function navLabel(path: string): string {
  return ALL_NAV.find((n) => n.path === path)?.label ?? "";
}
