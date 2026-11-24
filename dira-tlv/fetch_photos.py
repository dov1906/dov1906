#!/usr/bin/env python3
"""Download and shrink listing photos so they can be uploaded to the tracker artifact.

Usage: python3 fetch_photos.py photos.json OUT_DIR [max_per_listing]
photos.json: {"<listing id>": {"photos": ["https://...jpg", ...]}, ...}
Writes OUT_DIR/<listing id>-<n>.jpg (max 900 px, JPEG q78) and OUT_DIR/manifest.json:
{"<listing id>": ["/abs/path/file.jpg", ...]}
Only https URLs are fetched; failures are skipped and reported.
"""
import json, sys, subprocess, pathlib
from PIL import Image

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 4
out.mkdir(parents=True, exist_ok=True)
data = json.loads(src.read_text(encoding="utf8"))
manifest, failed = {}, 0
for lid, info in data.items():
    urls = [u for u in (info.get("photos") or []) if str(u).startswith("https://")][:limit]
    files = []
    for n, url in enumerate(urls, 1):
        raw = out / f"{lid}-{n}.raw"
        r = subprocess.run(["curl", "-s", "-f", "-L", "--max-time", "20", "-o", str(raw), url])
        if r.returncode != 0 or not raw.exists():
            failed += 1
            continue
        try:
            im = Image.open(raw)
            im.thumbnail((900, 900))
            dest = out / f"{lid}-{n}.jpg"
            im.convert("RGB").save(dest, quality=78, optimize=True)
            files.append(str(dest))
        except Exception:
            failed += 1
        finally:
            raw.unlink(missing_ok=True)
    if files:
        manifest[lid] = files
(out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf8")
print(f"{sum(len(v) for v in manifest.values())} photos for {len(manifest)} listings, {failed} failed -> {out}")
