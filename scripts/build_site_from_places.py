#!/usr/bin/env python3
"""
Regenera listados (hoteles.html, …) y crea negocios/<slug>.html desde data/places.json.
Ejecutar desde la raíz del proyecto: python scripts/build_site_from_places.py
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "places.json"
NEG = ROOT / "negocios"

CAT_LIST_FILE = {
    "hoteles": "hoteles.html",
    "restaurantes": "restaurantes.html",
    "tours": "tours.html",
    "tiendas": "tiendas.html",
    "museos": "museos.html",
    "estacionamientos": "estacionamientos.html",
    "eventos": "eventos.html",
}

CAT_LABEL = {
    "hoteles": "Hotel",
    "restaurantes": "Restaurante",
    "tours": "Tour / experiencia",
    "tiendas": "Tienda",
    "museos": "Museo o sitio",
    "estacionamientos": "Estacionamiento",
    "eventos": "Evento",
}

LIST_META = {
    "hoteles": {
        "title": "Hoteles · Tlalpujahua",
        "desc": "Hoteles y hospedaje en Tlalpujahua con fichas detalladas: horarios, teléfono, dirección y cómo llegar.",
        "body_class": "page-hoteles",
        "h1": "Hoteles",
        "intro": "Reserva con anticipación en diciembre y puentes. Cada ficha incluye dirección, horarios, teléfono y descripción del establecimiento; confirma tarifas y disponibilidad con el hotel.",
        "after_grid": "",
    },
    "restaurantes": {
        "title": "Restaurantes · Tlalpujahua",
        "desc": "Restaurantes y antojitos en Tlalpujahua con descripciones y horarios.",
        "body_class": "page-restaurantes",
        "h1": "Restaurantes",
        "intro": "Antojitos, cafés y mesas con vista al pueblo. Abre la ficha de cada negocio para ver el menú de especialidades, horarios y datos de contacto.",
        "after_grid": """      <p class="prose" style="margin-top:2rem">Más opciones en <a href="https://visitmichoacan.com.mx/town/tlalpujahua" rel="noopener noreferrer">Visit Michoacán</a> y en fondas y mercados locales.</p>
""",
    },
    "tours": {
        "title": "Tours · Tlalpujahua",
        "desc": "Tours y experiencias en Tlalpujahua y alrededores.",
        "body_class": "page-tours",
        "h1": "Tours y experiencias",
        "intro": "Guías, cerveza artesanal y recorridos a medida. Cada ficha incluye horarios, teléfonos, enlaces y descripción del servicio.",
        "after_grid": "",
    },
    "tiendas": {
        "title": "Tiendas · Tlalpujahua",
        "desc": "Tiendas de esferas, licores y recuerdos en Tlalpujahua.",
        "body_class": "page-tiendas",
        "h1": "Tiendas",
        "intro": "Esferas, licores artesanales y recuerdos. Las fichas indicen horarios, teléfono y envíos cuando el comercio los ofrece.",
        "after_grid": "",
    },
    "museos": {
        "title": "Museos y sitios · Tlalpujahua",
        "desc": "Museos, templos y sitios históricos de Tlalpujahua.",
        "body_class": "page-museos",
        "h1": "Museos y sitios históricos",
        "intro": "Templos, museos y la mina que marcaron la historia del pueblo. Cada ficha incluye datos prácticos y cómo llegar en mapas.",
        "after_grid": "",
    },
    "estacionamientos": {
        "title": "Estacionamientos · Tlalpujahua",
        "desc": "Estacionamiento en Tlalpujahua durante feria y temporada alta.",
        "body_class": "page-estacionamientos",
        "h1": "Estacionamientos",
        "intro": "En temporada de feria el centro se satura. Consulta la ficha para tarifas, horario y ubicación exacta.",
        "after_grid": """      <div class="prose" style="margin-top:2rem">
        <p><strong>Consejo:</strong> si tu hotel ofrece cajón, deja el coche ahí y camina el centro; las cuestas son cortas pero empinadas.</p>
      </div>
""",
    },
    "eventos": {
        "title": "Eventos · Tlalpujahua",
        "desc": "Feria de la Esfera y festividades en Tlalpujahua.",
        "body_class": "page-eventos",
        "h1": "Eventos",
        "intro": "La XXVII Feria de la Esfera se realiza del 7 de octubre al 15 de diciembre de 2026. En la ficha tienes teléfono, web oficial y un resumen de qué esperar.",
        "after_grid": """      <div class="two-col" style="margin-top:2rem">
        <div class="prose">
          <h2 style="margin-top:0">Virgen del Carmen</h2>
          <p>Fiesta patronal alrededor del <strong>16 de julio</strong> con procesiones y verbena en el centro histórico.</p>
        </div>
        <div class="prose">
          <h2 style="margin-top:0">Feratum y cine de género</h2>
          <p>Festival de cine fantástico con origen en la región; consulta sedes y fechas en <a href="https://www.feratumfilmfest.com/" rel="noopener noreferrer">feratumfilmfest.com</a>.</p>
        </div>
      </div>
""",
    },
}


def get_site_header() -> str:
    idx = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r'(<header class="site-header">.*?</header>)', idx, re.S)
    if not m:
        raise RuntimeError("No se encontró site-header en index.html")
    return m.group(1)


def rel_root_paths(fragment: str, prefix: str) -> str:
    """prefix '' o '../' para recursos y enlaces .html desde raíz o negocios/."""
    out = fragment
    out = re.sub(r'href="(?!https?:|#|//|mailto:)([^"]+)"', lambda m: f'href="{prefix}{m.group(1)}"', out)
    out = re.sub(r'src="(?!https?://)([^"]+)"', lambda m: f'src="{prefix}{m.group(1)}"', out)
    return out


def linkify_urls(text: str) -> str:
    esc = html.escape(text)
    for m in re.finditer(r"(https?://[^\s<]+)", text):
        url = m.group(1).rstrip(").,;]")
        e = html.escape(url)
        esc = esc.replace(e, f'<a href="{e}" rel="noopener noreferrer">{e}</a>', 1)
    return esc


def maps_link(dest: str) -> str:
    if not dest:
        return ""
    q = quote(dest, safe=",")
    return f"https://www.google.com/maps/dir/?api=1&destination={q}"


def snippet(p: dict, max_len: int = 220) -> str:
    parts = []
    if p.get("direccion"):
        parts.append(p["direccion"])
    if p.get("horarios"):
        h = p["horarios"][0]
        label = (h[0] + ": ") if h[0] else ""
        parts.append(label + h[1])
    oi = p.get("otra_info") or []
    if oi and oi[0][1]:
        parts.append(oi[0][1])
    g = (p.get("informacion_general") or "").strip()
    if g:
        parts.append(g)
    full = " ".join(parts)
    if len(full) > max_len:
        full = full[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return full if full else "Ver ficha completa."


def render_horarios_dl(p: dict) -> str:
    rows = p.get("horarios") or []
    if not rows:
        return "<p class=\"place-detail-muted\">Sin horario publicado.</p>"
    bits = ["<dl class=\"place-detail-kv\">"]
    for k, v in rows:
        bits.append(f"<dt>{html.escape(k) if k else 'Horario'}</dt><dd>{html.escape(v)}</dd>")
    bits.append("</dl>")
    return "\n".join(bits)


def render_otra_ul(p: dict) -> str:
    rows = p.get("otra_info") or []
    if not rows:
        return "<p class=\"place-detail-muted\">Sin datos adicionales.</p>"
    bits = ["<ul class=\"otra-info-list\">"]
    for _, v in rows:
        bits.append(f"<li>{linkify_urls(v)}</li>")
    bits.append("</ul>")
    return "\n".join(bits)


def render_general(p: dict) -> str:
    t = (p.get("informacion_general") or "").strip()
    if not t:
        return ""
    t_html = html.escape(t).replace("*", " · ")
    return f'<div class="prose place-detail-prose"><p>{t_html}</p></div>'


def card_html(p: dict, meta_label: str | None = None) -> str:
    slug = p["slug"]
    img = p.get("imagen") or ""
    title = html.escape(p["title"])
    lab = html.escape(meta_label or CAT_LABEL.get(p["categoria"], "Lugar"))
    sn = linkify_urls(snippet(p))
    maps = maps_link(p.get("mapa_destino") or "")
    map_btn = (
        f'<a class="btn-sm secondary" href="{html.escape(maps)}" rel="noopener noreferrer">Cómo llegar</a>'
        if maps
        else ""
    )
    img_tag = (
        f'<a class="place-card-media" href="negocios/{html.escape(slug)}.html"><img src="{html.escape(img)}" width="800" height="533" alt="{title}" loading="lazy"></a>'
        if img
        else ""
    )
    return f"""        <article class="place-card">
          {img_tag}
          <div class="place-body">
            <p class="place-meta">{lab}</p>
            <h2><a href="negocios/{html.escape(slug)}.html">{title}</a></h2>
            <p>{sn}</p>
            <div class="place-actions">
              <a class="btn-sm" href="negocios/{html.escape(slug)}.html">Ficha completa</a>
              {map_btn}
            </div>
          </div>
        </article>
"""


def detail_html(p: dict, site_header: str) -> str:
    prefix = "../"
    nav = rel_root_paths(site_header, prefix)
    slug = p["slug"]
    cat = p["categoria"]
    list_file = CAT_LIST_FILE[cat]
    cat_title = {"museos": "Museos y sitios"}.get(cat, LIST_META[cat]["h1"])
    crumbs = f'<p class="place-detail-crumbs"><a href="{prefix}{list_file}">{html.escape(cat_title)}</a> · {html.escape(p["title"])}</p>'
    h1 = html.escape(p["title"])
    addr = ""
    if p.get("direccion"):
        addr = f'<p class="place-detail-address"><i class="fa-solid fa-location-dot" aria-hidden="true"></i> {html.escape(p["direccion"])}</p>'
    hero = ""
    if p.get("imagen"):
        hero = f'<figure class="place-detail-hero"><img src="{html.escape(p["imagen"])}" width="1200" height="630" alt="{h1}" loading="lazy"></figure>'
    rating = ""
    if p.get("valoracion"):
        rating = f'<p class="place-detail-rating"><i class="fa-solid fa-star" aria-hidden="true"></i> Valoración publicada: <strong>{html.escape(p["valoracion"])}/10</strong></p>'
    maps = maps_link(p.get("mapa_destino") or "")
    map_block = ""
    if maps:
        map_block = f'<p><a class="btn btn-primary" href="{html.escape(maps)}" rel="noopener noreferrer"><i class="fa-solid fa-diamond-turn-right" aria-hidden="true"></i> Cómo llegar en Google Maps</a></p>'

    body = f"""  <header class="page-head">
    <div class="page-head-inner">
      {crumbs}
      <h1 id="main">{h1}</h1>
      {addr}
    </div>
  </header>
  <section class="section">
    <div class="section-inner place-detail-page">
      {hero}
      <div class="place-detail-grid">
        <div class="place-detail-card">
          <h2><i class="fa-regular fa-clock" aria-hidden="true"></i> Horarios</h2>
          {render_horarios_dl(p)}
        </div>
        <div class="place-detail-card">
          <h2><i class="fa-solid fa-circle-info" aria-hidden="true"></i> Contacto y más</h2>
          {render_otra_ul(p)}
          {rating}
          {map_block}
        </div>
      </div>
      <h2 class="place-detail-h2">Sobre el lugar</h2>
      {render_general(p) or '<p class="place-detail-muted">Sin descripción extendida.</p>'}
    </div>
  </section>
"""
    raw_meta = (p.get("informacion_general") or "").strip() or p["title"]
    if len(raw_meta) > 155:
        raw_meta = raw_meta[:152] + "…"
    desc = html.escape(raw_meta)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{desc}">
  <title>{h1} · Tlalpujahua</title>
  <link rel="icon" href="{prefix}assets/img/wp/2023/08/cropped-favicon-32x32.png" type="image/png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400..700;1,9..40,400..700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}css/site.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" crossorigin="anonymous" referrerpolicy="no-referrer">
</head>
<body class="page-negocio" data-nav-active="{prefix}{list_file}">
  <a class="skip-link" href="#main">Ir al contenido</a>
{nav}
{body}
  <footer class="site-footer">
    <div class="footer-inner">
      <p class="footer-note" style="margin:0"><a href="{prefix}index.html">Inicio</a> · © <span id="year"></span></p>
      <p class="footer-note" style="margin:0">Un sitio desarrollado y hospedado por <a href="https://www.solucionesmarva.com" target="_blank" rel="noopener noreferrer">Soluciones Marva</a>.</p>
    </div>
  </footer>
  <script src="{prefix}js/site.js" defer></script>
</body>
</html>
"""


def listing_page(cat: str, places: list[dict], site_header: str) -> str:
    meta = LIST_META[cat]
    subset = [p for p in places if p["categoria"] == cat]
    subset.sort(key=lambda x: x["title"].lower())
    cards = "\n".join(card_html(p) for p in subset)
    after = meta["after_grid"]
    head = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(meta['desc'])}">
  <title>{html.escape(meta['title'])}</title>
  <link rel="icon" href="assets/img/wp/2023/08/cropped-favicon-32x32.png" type="image/png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400..700;1,9..40,400..700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/site.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css" crossorigin="anonymous" referrerpolicy="no-referrer">
</head>
<body class="{html.escape(meta['body_class'])}">
  <a class="skip-link" href="#main">Ir al contenido</a>
{site_header}
  <header class="page-head">
    <div class="page-head-inner">
      <h1 id="main">{html.escape(meta['h1'])}</h1>
      <p>{html.escape(meta['intro'])}</p>
    </div>
  </header>
  <section class="section">
    <div class="section-inner">
      <div class="listing-grid">
{cards}
      </div>
{after}    </div>
  </section>
  <footer class="site-footer">
    <div class="footer-inner">
      <p class="footer-note" style="margin:0"><a href="index.html">Inicio</a> · © <span id="year"></span></p>
      <p class="footer-note" style="margin:0">Un sitio desarrollado y hospedado por <a href="https://www.solucionesmarva.com" target="_blank" rel="noopener noreferrer">Soluciones Marva</a>.</p>
    </div>
  </footer>
  <script src="js/site.js" defer></script>
</body>
</html>
"""
    return head


def main() -> None:
    places = json.loads(DATA.read_text(encoding="utf-8"))
    NEG.mkdir(exist_ok=True)
    site_header = get_site_header()

    for p in places:
        out = NEG / f"{p['slug']}.html"
        out.write_text(detail_html(p, site_header), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))

    for cat in CAT_LIST_FILE:
        path = ROOT / CAT_LIST_FILE[cat]
        path.write_text(listing_page(cat, places, site_header), encoding="utf-8")
        print("updated", path.name)

    print("done,", len(places), "fichas")


if __name__ == "__main__":
    main()
