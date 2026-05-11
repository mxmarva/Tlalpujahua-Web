#!/usr/bin/env python3
"""
Extrae fichas de https://www.tlalpujahua.net/destinations/... desde archivos tipo.
Salida: data/places.json (sin depender de BeautifulSoup).
"""
from __future__ import annotations

import json
import re
import ssl
import time
import urllib.request
from html import unescape
from urllib.parse import urljoin, urlparse

BASE = "https://www.tlalpujahua.net"
ARCHIVES = [
    "/type/hoteles/",
    "/type/restaurantes/",
    "/type/tours/",
    "/type/tiendas/",
    "/type/museos/",
    "/type/estacionamientos/",
    "/type/eventos/",
]

UA = "Mozilla/5.0 (compatible; TlalpujStaticImport/1.0)"


def fetch(url: str) -> str:
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=ctx, timeout=45) as r:
        return r.read().decode("utf-8", errors="replace")


def strip_tags(html: str) -> str:
    t = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.I | re.S)
    t = re.sub(r"<style[^>]*>.*?</style>", "", t, flags=re.I | re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_dest_urls(html: str) -> list[str]:
    out = []
    for m in re.finditer(r'href="(https?://www\.tlalpujahua\.net/destinations/[^"]+)"', html):
        u = m.group(1).rstrip("/")
        if u not in out:
            out.append(u)
    return out


def parse_box_list(html: str, title: str) -> list[tuple[str, str]]:
    """Encuentra <h3>title</h3> ... <ul><li>...</li></ul> y devuelve pares (strong, texto)."""
    pat = rf"<h3>\s*{re.escape(title)}\s*</h3>\s*<ul>(.*?)</ul>"
    m = re.search(pat, html, re.I | re.S)
    if not m:
        return []
    block = m.group(1)
    rows = []
    for li in re.finditer(r"<li>(.*?)</li>", block, re.S):
        raw = li.group(1)
        sm = re.search(r"<strong>([^<]*)</strong>\s*:\s*(.*)", raw, re.S)
        if sm:
            k = strip_tags(sm.group(1))
            v = strip_tags(sm.group(2))
        else:
            k = ""
            v = strip_tags(raw)
        if v:
            rows.append((k, v))
    return rows


def parse_general(html: str) -> str:
    m = re.search(
        r"<h2>\s*Información General\s*</h2>\s*<p>(.*?)</p>",
        html,
        re.I | re.S,
    )
    if not m:
        return ""
    return strip_tags(m.group(1))


def parse_og_image(html: str) -> str:
    m = re.search(r'<meta property="og:image" content="([^"]+)"', html, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r'data-image-src="([^"]+)"', html)
    return m.group(1).strip() if m else ""


def parse_address(html: str) -> str:
    m = re.search(r'icon_pin[^>]*></i>\s*([^<]+)</span>', html, re.I)
    return strip_tags(m.group(1)) if m else ""


def parse_daddr(html: str) -> str:
    m = re.search(r'name="daddr"\s+value="([^"]+)"', html)
    if not m:
        return ""
    return m.group(1).replace(" ", "").strip()


def parse_rating(html: str) -> str | None:
    m = re.search(
        r'<div[^>]*class="[^"]*score_in[^"]*"[^>]*data-value="([^"]+)"',
        html,
        re.I,
    )
    if m:
        return m.group(1).strip()
    m = re.search(r'<div[^>]*class="[^"]*score[^"]*"[^>]*data-value="([^"]+)"', html, re.I)
    return m.group(1).strip() if m else None


def parse_title(html: str) -> str:
    m = re.search(r"<title>([^<|]+)", html)
    if m:
        return strip_tags(m.group(1)).replace("&#8211;", "–").strip()
    return ""


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/").split("/")[-1]
    return path


def main() -> None:
    all_urls: list[str] = []
    url_category: dict[str, str] = {}
    for path in ARCHIVES:
        url = urljoin(BASE, path)
        cat = path.strip("/").split("/")[-1]
        print("archive", url)
        html = fetch(url)
        for u in extract_dest_urls(html):
            if u not in all_urls:
                all_urls.append(u)
            url_category[u] = cat
        time.sleep(0.4)

    places: list[dict] = []
    for u in sorted(all_urls):
        print("place", u)
        html = fetch(u)
        slug = slug_from_url(u)
        title = parse_title(html)
        if "–" in title:
            title = title.split("–", 1)[0].strip()
        if "|" in title:
            title = title.split("|", 1)[0].strip()

        horarios = parse_box_list(html, "Horarios")
        otra = parse_box_list(html, "Otra info")
        general = parse_general(html)
        rating = parse_rating(html)
        daddr = parse_daddr(html)
        og_image = parse_og_image(html)
        direccion = parse_address(html)

        places.append(
            {
                "url": u,
                "slug": slug,
                "categoria": url_category.get(u, ""),
                "title": title,
                "horarios": horarios,
                "otra_info": otra,
                "informacion_general": general,
                "valoracion": rating,
                "mapa_destino": daddr,
                "imagen": og_image,
                "direccion": direccion,
            }
        )
        time.sleep(0.35)

    out_path = "data/places.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(places, f, ensure_ascii=False, indent=2)
    print("wrote", out_path, "count", len(places))


if __name__ == "__main__":
    main()
