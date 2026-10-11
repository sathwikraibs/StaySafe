import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

// Each build gets its own version; the app compares it with /version.json to know when to update
const APP_VERSION = (process.env.VERCEL_GIT_COMMIT_SHA || String(Date.now())).slice(0, 12);

export default defineConfig({
  plugins: [
    react(),
    {
      name: 'trustlight-version',
      generateBundle() {
        this.emitFile({ type: 'asset', fileName: 'version.json', source: JSON.stringify({ version: APP_VERSION }) });
      },
    },
  ],
  define: { __APP_VERSION__: JSON.stringify(APP_VERSION) },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  build: {
    sourcemap: true,   // the code is open source; this lets browsers show readable errors
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
});
