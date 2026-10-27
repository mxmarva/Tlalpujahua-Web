#!/usr/bin/env python3
"""Genera sitemap.xml para www.tlalpujahua.net a partir de los .html del repo.
lastmod = fecha del último commit de cada archivo."""
import pathlib, subprocess, datetime
BASE = "https://www.tlalpujahua.net/"
ROOT = pathlib.Path(__file__).resolve().parent.parent
EXCLUDE = {"404.html"}
urls = []
for f in sorted(ROOT.rglob("*.html")):
    rel = f.relative_to(ROOT).as_posix()
    if rel.startswith((".git/", "scripts/", "assets/", "data/")) or rel in EXCLUDE:
        continue
    d = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel], cwd=ROOT,
                       capture_output=True, text=True).stdout.strip() or datetime.date.today().isoformat()
    loc = BASE if rel == "index.html" else BASE + rel
    pr = "1.0" if rel == "index.html" else ("0.6" if rel.startswith("negocios/") else "0.8")
    urls.append(f"  <url><loc>{loc}</loc><lastmod>{d}</lastmod><priority>{pr}</priority></url>")
(ROOT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n")
print(len(urls), "URLs")
