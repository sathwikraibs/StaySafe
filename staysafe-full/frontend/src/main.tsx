import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import { LanguageProvider } from './i18n';
import './index.css';
import { API_BASE } from './config';

// Wake the server as soon as someone opens the site, so their first check or question is quick
try { fetch(`${API_BASE}/api/assistant/status`, { cache: 'no-store' }).catch(() => undefined); } catch { /* ignore */ }

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LanguageProvider>
      <App />
    </LanguageProvider>
  </StrictMode>
);
