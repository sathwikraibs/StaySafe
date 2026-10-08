// TrustLight service worker. It does one job: receive things people share to TrustLight
// from other apps (a message, a link, a screenshot or a file) and hand them to the page.
// Nothing is cached for offline use, so the site is always the newest version.
const SHARE_CACHE = "staysafe-share";

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "POST" || url.origin !== self.location.origin || url.pathname !== "/share-target") return;
  event.respondWith((async () => {
    try {
      const form = await event.request.formData();
      const file = form.getAll("file").find((f) => f && typeof f !== "string" && f.size > 0) || null;
      const str = (k) => { const v = form.get(k); return typeof v === "string" ? v.slice(0, 10000) : ""; };
      const data = { title: str("title"), text: str("text"), url: str("url"), at: Date.now(),
                     file: file ? { name: file.name || "", type: file.type || "" } : null };
      const cache = await caches.open(SHARE_CACHE);
      await cache.put("/__share/data", new Response(JSON.stringify(data), { headers: { "content-type": "application/json" } }));
      if (file) await cache.put("/__share/file", new Response(file, { headers: { "content-type": file.type || "application/octet-stream" } }));
      else await cache.delete("/__share/file");
    } catch (e) {
      // the page will simply open normally
    }
    return Response.redirect("/?shared=1", 303);
  })());
});
