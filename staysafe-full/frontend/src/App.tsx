import { useState, useEffect, useCallback, lazy, Suspense } from "react";
import { Layout } from "@/components/Layout";
import { HomePage } from "@/pages/HomePage";
import { API_BASE } from "@/config";
import { receiveShare } from "@/share";

// Each tool's page is downloaded only when needed, so the home page opens faster.
// Shortly after the home page shows, the rest are fetched quietly so moving around stays instant.
const loadScanUrlPage = () => import("@/pages/ScanUrlPage").then((m) => ({ default: m.ScanUrlPage }));
const loadScanMessagePage = () => import("@/pages/ScanMessagePage").then((m) => ({ default: m.ScanMessagePage }));
const loadScanQrPage = () => import("@/pages/ScanQrPage").then((m) => ({ default: m.ScanQrPage }));
const loadScanFilePage = () => import("@/pages/ScanFilePage").then((m) => ({ default: m.ScanFilePage }));
const loadCheckPasswordPage = () => import("@/pages/CheckPasswordPage").then((m) => ({ default: m.CheckPasswordPage }));
const loadCheckNetworkPage = () => import("@/pages/CheckNetworkPage").then((m) => ({ default: m.CheckNetworkPage }));
const loadScanEmailPage = () => import("@/pages/ScanEmailPage").then((m) => ({ default: m.ScanEmailPage }));
const loadDashboardPage = () => import("@/pages/DashboardPage").then((m) => ({ default: m.DashboardPage }));
const loadIncidentPage = () => import("@/pages/IncidentPage").then((m) => ({ default: m.IncidentPage }));
const loadScamLibraryPage = () => import("@/pages/ScamLibraryPage").then((m) => ({ default: m.ScamLibraryPage }));
const loadHelpPage = () => import("@/pages/HelpPage").then((m) => ({ default: m.HelpPage }));
const loadSettingsPage = () => import("@/pages/SettingsPage").then((m) => ({ default: m.SettingsPage }));
const loadAboutPage = () => import("@/pages/AboutPage").then((m) => ({ default: m.AboutPage }));
const loadCheckNumberPage = () => import("@/pages/CheckNumberPage").then((m) => ({ default: m.CheckNumberPage }));
const ScanUrlPage = lazy(loadScanUrlPage);
const ScanMessagePage = lazy(loadScanMessagePage);
const ScanQrPage = lazy(loadScanQrPage);
const ScanFilePage = lazy(loadScanFilePage);
const CheckPasswordPage = lazy(loadCheckPasswordPage);
const CheckNetworkPage = lazy(loadCheckNetworkPage);
const ScanEmailPage = lazy(loadScanEmailPage);
const DashboardPage = lazy(loadDashboardPage);
const IncidentPage = lazy(loadIncidentPage);
const ScamLibraryPage = lazy(loadScamLibraryPage);
const HelpPage = lazy(loadHelpPage);
const SettingsPage = lazy(loadSettingsPage);
const AboutPage = lazy(loadAboutPage);
const CheckNumberPage = lazy(loadCheckNumberPage);
const ALL_PAGES = [loadScanUrlPage, loadScanMessagePage, loadScanQrPage, loadScanFilePage, loadCheckPasswordPage, loadCheckNetworkPage, loadScanEmailPage, loadDashboardPage, loadIncidentPage, loadScamLibraryPage, loadHelpPage, loadSettingsPage, loadAboutPage, loadCheckNumberPage];

const ROUTES = [
  "/", "/scan-url", "/scan-message", "/scan-qr", "/scan-file",
  "/check-password", "/check-network", "/scan-email", "/check-number",
  "/dashboard", "/incident", "/scam-library", "/help", "/settings", "/about",
];

function getInitialPath(): string {
  const hash = window.location.hash.replace(/^#/, "");
  if (ROUTES.includes(hash)) return hash;
  return "/";
}

export default function App() {
  const [path, setPath] = useState<string>(getInitialPath());

  const navigate = useCallback((newPath: string) => {
    if (!ROUTES.includes(newPath)) return;
    setPath(newPath);
    window.location.hash = newPath;
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  // Wake the free server up as soon as someone opens the site, so their first check is quicker
  useEffect(() => {
    fetch(`${API_BASE}/`).catch(() => { /* it's only a wake-up call */ });
  }, []);

  useEffect(() => {
    const t = window.setTimeout(() => { ALL_PAGES.forEach((load) => { load().catch(() => undefined); }); }, 2500);
    return () => window.clearTimeout(t);
  }, []);

  // Opened by sharing a message, link, screenshot or file to TrustLight: go to the right check
  useEffect(() => {
    receiveShare().then((p) => { if (p) navigate(p); }).catch(() => undefined);
  }, [navigate]);

  useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash.replace(/^#/, "");
      if (ROUTES.includes(hash)) setPath(hash);
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return (
    <Layout currentPath={path} onNavigate={navigate}>
      <Suspense fallback={<PageLoading />}>{renderPage(path, navigate)}</Suspense>
    </Layout>
  );
}

function renderPage(path: string, navigate: (p: string) => void) {
  switch (path) {
    case "/": return <HomePage onNavigate={navigate} />;
    case "/scan-url": return <ScanUrlPage onNavigate={navigate} />;
    case "/scan-message": return <ScanMessagePage onNavigate={navigate} />;
    case "/scan-qr": return <ScanQrPage onNavigate={navigate} />;
    case "/scan-file": return <ScanFilePage onNavigate={navigate} />;
    case "/check-password": return <CheckPasswordPage onNavigate={navigate} />;
    case "/check-network": return <CheckNetworkPage onNavigate={navigate} />;
    case "/scan-email": return <ScanEmailPage onNavigate={navigate} />;
    case "/check-number": return <CheckNumberPage onNavigate={navigate} />;
    case "/dashboard": return <DashboardPage onNavigate={navigate} />;
    case "/incident": return <IncidentPage onNavigate={navigate} />;
    case "/help": return <HelpPage onNavigate={navigate} />;
    case "/settings": return <SettingsPage onNavigate={navigate} />;
    case "/about": return <AboutPage onNavigate={navigate} />;
    case "/scam-library": return <ScamLibraryPage onNavigate={navigate} />;
    default: return <HomePage onNavigate={navigate} />;
  }
}

function PageLoading() {
  return (
    <div className="flex justify-center py-16" role="status" aria-label="Loading">
      <span className="h-6 w-6 animate-spin rounded-full border-2 border-brand-300 border-t-transparent" />
    </div>
  );
}
