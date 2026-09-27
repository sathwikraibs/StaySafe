import { useState, useEffect, useCallback } from "react";
import { Layout } from "@/components/Layout";
import { HomePage } from "@/pages/HomePage";
import { ScanUrlPage } from "@/pages/ScanUrlPage";
import { ScanMessagePage } from "@/pages/ScanMessagePage";
import { ScanQrPage } from "@/pages/ScanQrPage";
import { ScanFilePage } from "@/pages/ScanFilePage";
import { CheckPasswordPage } from "@/pages/CheckPasswordPage";
import { CheckNetworkPage } from "@/pages/CheckNetworkPage";
import { ScanEmailPage } from "@/pages/ScanEmailPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { IncidentPage } from "@/pages/IncidentPage";
import { ScamLibraryPage } from "@/pages/ScamLibraryPage";
import { HelpPage } from "@/pages/HelpPage";
import { SettingsPage } from "@/pages/SettingsPage";
import { AboutPage } from "@/pages/AboutPage";

const ROUTES = [
  "/", "/scan-url", "/scan-message", "/scan-qr", "/scan-file",
  "/check-password", "/check-network", "/scan-email",
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
      {renderPage(path, navigate)}
    </Layout>
  );
}

function renderPage(path: string, navigate: (p: string) => void) {
  switch (path) {
    case "/": return <HomePage onNavigate={navigate} />;
    case "/scan-url": return <ScanUrlPage />;
    case "/scan-message": return <ScanMessagePage />;
    case "/scan-qr": return <ScanQrPage />;
    case "/scan-file": return <ScanFilePage />;
    case "/check-password": return <CheckPasswordPage />;
    case "/check-network": return <CheckNetworkPage />;
    case "/scan-email": return <ScanEmailPage />;
    case "/dashboard": return <DashboardPage onNavigate={navigate} />;
    case "/incident": return <IncidentPage onNavigate={navigate} />;
    case "/help": return <HelpPage onNavigate={navigate} />;
    case "/settings": return <SettingsPage onNavigate={navigate} />;
    case "/about": return <AboutPage onNavigate={navigate} />;
    case "/scam-library": return <ScamLibraryPage />;
    default: return <HomePage onNavigate={navigate} />;
  }
}
