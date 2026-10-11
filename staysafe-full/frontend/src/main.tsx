import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import { LanguageProvider, loadLanguage, startingLanguage } from './i18n';
import './index.css';
import { API_BASE } from './config';
import { registerServiceWorker, listenForInstall } from './share';

// The fonts load alongside the page instead of holding it back (the page shows at once in a system font)
const fonts = document.createElement('link');
fonts.rel = 'stylesheet';
fonts.href = 'https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;600;700;800&family=Baloo+Tamma+2:wght@500;600;700;800&family=Noto+Sans:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans+Kannada:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap';
document.head.appendChild(fonts);

registerServiceWorker();
listenForInstall();

// Wake the server as soon as someone opens the site, so their first check or question is quick
try { fetch(`${API_BASE}/api/assistant/status`, { cache: 'no-store' }).catch(() => undefined); } catch { /* ignore */ }

// Load the visitor's language first (English is built in), then show the site
loadLanguage(startingLanguage()).catch(() => undefined).finally(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <LanguageProvider>
        <App />
      </LanguageProvider>
    </StrictMode>
  );
});
