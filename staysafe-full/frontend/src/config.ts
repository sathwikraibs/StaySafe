// Backend API base URL.
// Set VITE_API_BASE in Vercel (Project → Settings → Environment Variables) to point
// at a different backend without editing code. Falls back to the current Render URL.
const DEFAULT_API_BASE = "https://staysafe-backend-aj95.onrender.com";

export const API_BASE = (import.meta.env.VITE_API_BASE || DEFAULT_API_BASE).replace(/\/+$/, "");
