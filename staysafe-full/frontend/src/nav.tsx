import type { ComponentType } from "react";
import {
  IconHome, IconLink, IconMessage, IconQr, IconFile, IconKey,
  IconNetwork, IconEmail, IconDashboard, IconAlert, IconBook, IconHelp, IconSettings, IconInfo,
} from "@/icons";

export interface NavItem {
  path: string;
  /** translation key for the full label, e.g. "nav.link" */
  label: string;
  /** translation key for the short phone label */
  short: string;
  icon: ComponentType<{ className?: string; strokeWidth?: number }>;
  /** "urgent" = I clicked a scam (red), "help" = Need help (green) */
  tone?: "urgent" | "help";
}

/** The checks most people need: shown big on the home page and first in the menus. */
export const MAIN_TOOLS: NavItem[] = [
  { path: "/scan-message", label: "nav.message", short: "nav.messageShort", icon: IconMessage },
  { path: "/scan-url", label: "nav.link", short: "nav.linkShort", icon: IconLink },
  { path: "/scan-qr", label: "nav.qr", short: "nav.qrShort", icon: IconQr },
  { path: "/scan-file", label: "nav.file", short: "nav.fileShort", icon: IconFile },
];

/** Everything else, kept one step away so the first screen stays simple. */
export const MORE_TOOLS: NavItem[] = [
  { path: "/scan-email", label: "nav.email", short: "nav.emailShort", icon: IconEmail },
  { path: "/check-password", label: "nav.password", short: "nav.passwordShort", icon: IconKey },
  { path: "/check-network", label: "nav.network", short: "nav.networkShort", icon: IconNetwork },
  { path: "/scam-library", label: "nav.library", short: "nav.libraryShort", icon: IconBook },
  { path: "/dashboard", label: "nav.dashboard", short: "nav.dashboardShort", icon: IconDashboard },
];

export const HOME_TOOLS: NavItem[] = [...MAIN_TOOLS, ...MORE_TOOLS];

export const HELP_NAV: NavItem[] = [
  { path: "/incident", label: "nav.incident", short: "nav.incidentShort", icon: IconAlert, tone: "urgent" },
  { path: "/help", label: "nav.help", short: "nav.helpShort", icon: IconHelp, tone: "help" },
];

export const EXTRA_NAV: NavItem[] = [
  { path: "/settings", label: "nav.settings", short: "nav.settings", icon: IconSettings },
  { path: "/about", label: "nav.about", short: "nav.about", icon: IconInfo },
];

export const ALL_NAV: NavItem[] = [
  { path: "/", label: "nav.home", short: "nav.home", icon: IconHome },
  ...HOME_TOOLS,
  ...HELP_NAV,
  ...EXTRA_NAV,
];

/** Translation key for a page's label (used in breadcrumbs). */
export function navLabel(path: string): string {
  return ALL_NAV.find((n) => n.path === path)?.label ?? "";
}
