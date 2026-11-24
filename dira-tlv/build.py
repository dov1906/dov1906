#!/usr/bin/env python3
"""Build the installable web app (app/) from index.html (the artifact source).

Usage: python3 build.py
Writes app/index.html with a full HTML head (manifest, icons, theme color),
plus app/manifest.json, app/sw.js and app/icon-*.png.
"""
import json, pathlib, hashlib
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent
APP = ROOT / "app"
APP.mkdir(exist_ok=True)
(APP / "data").mkdir(exist_ok=True)

body = (ROOT / "index.html").read_text(encoding="utf8")
version = hashlib.sha1(body.encode()).hexdigest()[:10]

head = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1F5AA6">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Dira TLV">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="manifest.json">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="apple-touch-icon" href="icon-180.png">
<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style>
</head>
<body>
"""
(APP / "index.html").write_text(head + body + "\n</body>\n</html>\n", encoding="utf8")

manifest = {
    "name": "Dira Tel Aviv",
    "short_name": "Dira TLV",
    "description": "Recherche d'appartement à Tel Aviv : annonces, score, messages WhatsApp.",
    "lang": "fr",
    "start_url": "index.html#annonces",
    "scope": "./",
    "display": "standalone",
    "background_color": "#F4F7FA",
    "theme_color": "#1F5AA6",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
        {"src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}
(APP / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf8")

sw = f"""// Dira TLV service worker — version {version}
const CACHE = "dira-{version}";
const SHELL = ["index.html", "manifest.json", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting())); }});
self.addEventListener("activate", e => {{ e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); }});
self.addEventListener("fetch", e => {{
  const u = new URL(e.request.url);
  if (e.request.method !== "GET" || u.origin !== location.origin) return;
  // network first (fresh listings and code), cache as offline fallback
  e.respondWith(fetch(e.request).then(r => {{ const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); return r; }})
    .catch(() => caches.match(e.request).then(r => r || caches.match("index.html"))));
}});
"""
(APP / "sw.js").write_text(sw, encoding="utf8")

def icon(size, maskable=False):
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    blue, white, sun = (31, 90, 166, 255), (255, 255, 255, 255), (242, 179, 61, 255)
    if maskable:
        d.rectangle([0, 0, s, s], fill=blue)
        pad = s * 0.2
    else:
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=blue)
        pad = s * 0.12
    inner = s - 2 * pad
    k = inner / 34.0
    def X(v): return pad + v * k
    w = max(2, int(2.2 * k))
    d.rectangle([X(8), X(9), X(26), X(26)], outline=white, width=w)
    d.line([X(8), X(15), X(26), X(15)], fill=white, width=w)
    d.line([X(14), X(15), X(14), X(26)], fill=white, width=w)
    d.line([X(20), X(15), X(20), X(26)], fill=white, width=w)
    r = 3.4 * k
    d.ellipse([X(25) - r, X(8) - r, X(25) + r, X(8) + r], fill=sun)
    return img

icon(192).save(APP / "icon-192.png")
icon(512).save(APP / "icon-512.png")
icon(180, maskable=True).convert("RGB").save(APP / "icon-180.png")
icon(512, maskable=True).save(APP / "icon-maskable-512.png")
print("built app/ version", version)
