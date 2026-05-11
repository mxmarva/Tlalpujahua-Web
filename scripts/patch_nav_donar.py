from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
needle = """          <li>
            <a href="contacto.html"><i class="fa-brands fa-whatsapp fa-fw" aria-hidden="true"></i><span>Contacto</span></a>
          </li>
        </ul>"""
repl = """          <li>
            <a href="contacto.html"><i class="fa-brands fa-whatsapp fa-fw" aria-hidden="true"></i><span>Contacto</span></a>
          </li>
          <li>
            <a href="https://imarva.net/JnJkNd" target="_blank" rel="noopener noreferrer"><i class="fa-solid fa-heart fa-fw" aria-hidden="true"></i><span>Donar</span></a>
          </li>
          <li>
            <a href="agregar-negocio.html"><i class="fa-solid fa-circle-plus fa-fw" aria-hidden="true"></i><span>Agregar negocio</span></a>
          </li>
        </ul>"""
needle_n = needle.replace("contacto.html", "../contacto.html").replace(
    'href="agregar-negocio.html"', 'href="../agregar-negocio.html"'
)
repl_n = repl.replace("contacto.html", "../contacto.html").replace(
    'href="agregar-negocio.html"', 'href="../agregar-negocio.html"'
)

for p in sorted(ROOT.glob("*.html")):
    if p.name == "agregar-negocio.html":
        continue
    t = p.read_text(encoding="utf-8")
    if "imarva.net/JnJkNd" in t:
        continue
    if needle in t:
        p.write_text(t.replace(needle, repl), encoding="utf-8")
        print("root", p.name)

neg = ROOT / "negocios"
if neg.is_dir():
    for p in sorted(neg.glob("*.html")):
        t = p.read_text(encoding="utf-8")
        if "imarva.net/JnJkNd" in t:
            continue
        if needle_n in t:
            p.write_text(t.replace(needle_n, repl_n), encoding="utf-8")
            print("neg", p.name)
