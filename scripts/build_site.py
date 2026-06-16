#!/usr/bin/env python3
"""Genereer een statische Tailwind-site voor MedMij documentatie."""

import html as html_module
import json
import shutil
from pathlib import Path

import rdflib
from rdflib.namespace import RDF

MEDMIJ = rdflib.Namespace("https://register.medmij.nl/ontology/")
OBJECTEN_DIR = Path("objecten")
SITE_DIR = Path("site")

SECTIONS = [
    ("arrangements",            "Afspraken",               "Verantwoordelijkheden en afspraken"),
    ("components",              "Componenten",             "Technische systeemcomponenten"),
    ("data-products",           "Dataproducten",           "Beschikbare dataproducten"),
    ("data-resources",          "Gegevensbronnen",         "Gegevensbronnen en -diensten"),
    ("datasets",                "Gegevenssets",            "Beschikbare gegevenssets"),
    ("frameworks",              "Frameworks",              "Frameworks en afsprakenstelsels"),
    ("implementation-guidelines","Implementatierichtlijnen","Richtlijnen voor implementatie"),
    ("kwalificaties",           "Kwalificaties",           "Kwalificatievereisten"),
    ("modules",                 "Modules",                 "Functionele modules"),
    ("object-components",       "Objectcomponenten",       "Componenten van objecten"),
    ("objectklassen",           "Objectklassen",           "Klassen en typen"),
    ("requirements",            "Eisen",                   "Technische en functionele eisen"),
    ("services",                "Diensten",                "Aangeboden diensten"),
    ("specifications",          "Specificaties",           "Technische specificaties"),
]

LAYER_STYLE = {
    "Business":           ("layer-biz",  "#f59e0b"),
    "Business/Applicatie":("layer-biz",  "#f59e0b"),
    "Applicatie":         ("layer-app",  "#38bdf8"),
    "Technologie":        ("layer-tech", "#34d399"),
}

ICONS = {
    "home":                  '<path stroke-linecap="round" stroke-linejoin="round" d="m2.25 12 8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"/>',
    "arrangements":          '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75 2.25 2.25 0 0 0-.1-.664m-5.8 0A2.251 2.251 0 0 1 13.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25ZM6.75 12h.008v.008H6.75V12Zm0 3h.008v.008H6.75V15Zm0 3h.008v.008H6.75V18Z"/>',
    "components":            '<path stroke-linecap="round" stroke-linejoin="round" d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 0 1-.657.643 48.39 48.39 0 0 1-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 0 1-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 0 0-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 0 1-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 0 0 .657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 0 1-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 0 0 5.427-.63 48.05 48.05 0 0 0 .582-4.717.532.532 0 0 0-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.96.401v0a.656.656 0 0 0 .658-.663 48.422 48.422 0 0 0-.37-5.36c-1.886.342-3.81.574-5.766.689a.578.578 0 0 1-.61-.58v0Z"/>',
    "data-products":         '<path stroke-linecap="round" stroke-linejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 2.625c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125m16.5 5.625c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125"/>',
    "data-resources":        '<path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 0 1-3-3m3 3a3 3 0 1 0 0 6h13.5a3 3 0 1 0 0-6m-16.5-3a3 3 0 0 1 3-3h13.5a3 3 0 0 1 3 3m-19.5 0a4.5 4.5 0 0 1 .9-2.7L5.737 5.1a3.375 3.375 0 0 1 2.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 0 1 .9 2.7m0 0a3 3 0 0 1-3 3m0 3h.008v.008h-.008v-.008Zm0-6h.008v.008h-.008v-.008Zm-3 6h.008v.008h-.008v-.008Zm0-6h.008v.008h-.008v-.008Z"/>',
    "datasets":              '<path stroke-linecap="round" stroke-linejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 0 1-1.125-1.125M3.375 19.5h1.5C5.496 19.5 6 18.996 6 18.375m-3.75.125v-1.5C2.25 16.254 2.754 15.75 3.375 15.75m0 0h1.5c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 0H3.375m0 0a1.125 1.125 0 0 1-1.125-1.125v-1.5a1.125 1.125 0 0 1 1.125-1.125m0 0h1.5c.621 0 1.125-.504 1.125-1.125V9.75M1.5 9.75h1.5"/>',
    "frameworks":            '<path stroke-linecap="round" stroke-linejoin="round" d="M6.429 9.75 2.25 12l4.179 2.25m0-4.5 5.571 3 5.571-3m-11.142 0L2.25 7.5 12 2.25l9.75 5.25-4.179 2.25m0 0L21.75 12l-4.179 2.25m0 0 4.179 2.25L12 21.75 2.25 16.5l4.179-2.25m11.142 0-5.571 3-5.571-3"/>',
    "implementation-guidelines":'<path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"/>',
    "kwalificaties":         '<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 0 1-1.043 3.296 3.745 3.745 0 0 1-3.296 1.043A3.745 3.745 0 0 1 12 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 0 1-3.296-1.043 3.745 3.745 0 0 1-1.043-3.296A3.745 3.745 0 0 1 3 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 0 1 1.043-3.296 3.746 3.746 0 0 1 3.296-1.043A3.746 3.746 0 0 1 12 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 0 1 3.296 1.043 3.746 3.746 0 0 1 1.043 3.296A3.745 3.745 0 0 1 21 12Z"/>',
    "modules":               '<path stroke-linecap="round" stroke-linejoin="round" d="m21 7.5-9-5.25L3 7.5m18 0-9 5.25m9-5.25v9l-9 5.25M3 7.5l9 5.25M3 7.5v9l9 5.25m0-9v9"/>',
    "object-components":     '<path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5"/>',
    "objectklassen":         '<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z"/>',
    "requirements":          '<path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"/>',
    "services":              '<path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z"/><path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>',
    "specifications":        '<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"/>',
    "search":                '<path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"/>',
    "menu":                  '<path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"/>',
    "close":                 '<path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12"/>',
    "external":              '<path stroke-linecap="round" stroke-linejoin="round" d="M13.5 6H5.25A2.25 2.25 0 0 0 3 8.25v10.5A2.25 2.25 0 0 0 5.25 21h10.5A2.25 2.25 0 0 0 18 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"/>',
}


# ── helpers ───────────────────────────────────────────────────────────────────

def icon(key: str, size: int = 16) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
        f'stroke-width="1.5" stroke="currentColor" width="{size}" height="{size}" '
        f'style="flex-shrink:0">{ICONS.get(key, ICONS["search"])}</svg>'
    )


def esc(text: str) -> str:
    return html_module.escape(str(text).strip())


# ── data parsing ──────────────────────────────────────────────────────────────

def _parse_one(ttl_file: Path) -> dict | None:
    g = rdflib.Graph()
    g.parse(str(ttl_file), format="turtle")
    subjects = list(g.subjects(RDF.type, MEDMIJ.Object))
    if not subjects:
        return None
    subj = subjects[0]

    def val(pred):
        v = g.value(subj, pred)
        return str(v).strip() if v else ""

    return {
        "code":  val(MEDMIJ.code),
        "layer": val(MEDMIJ.layer),
        "text":  val(MEDMIJ.arrangementText),
        "note":  val(MEDMIJ.toelichting),
        "name":  val(MEDMIJ.elementName),
    }


def parse_objects(dir_path: Path) -> list[dict]:
    return [o for f in sorted(dir_path.glob("*.ttl")) if (o := _parse_one(f))]


def load_all_data(section_slugs: list[str]) -> dict[str, list[dict]]:
    data = {}
    for slug in section_slugs:
        path = OBJECTEN_DIR / slug
        if path.is_dir():
            data[slug] = parse_objects(path)
        else:
            data[slug] = []
    return data


# ── CSS & JS shared across all pages ─────────────────────────────────────────

SHARED_HEAD = """
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root { color-scheme: dark; }

    body {
      font-family: 'Inter', system-ui, sans-serif;
      background: #070b14;
      color: #e2e8f0;
      overflow-x: hidden;
    }

    /* ── scrollbar ── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #334155; }

    /* ── sidebar ── */
    #sidebar {
      width: 256px;
      min-width: 256px;
      background: #0d1117;
      border-right: 1px solid rgba(255,255,255,0.055);
      display: flex;
      flex-direction: column;
      position: fixed;
      top: 0; left: 0; bottom: 0;
      overflow-y: auto;
      z-index: 40;
      transition: transform 0.25s cubic-bezier(.4,0,.2,1);
    }

    #sidebar-overlay {
      display: none;
      position: fixed; inset: 0;
      background: rgba(0,0,0,0.6);
      backdrop-filter: blur(4px);
      z-index: 39;
    }

    @media (max-width: 768px) {
      #sidebar { transform: translateX(-100%); }
      #sidebar.open { transform: translateX(0); }
      #sidebar-overlay.open { display: block; }
      #main { margin-left: 0 !important; }
    }

    #main { margin-left: 256px; min-height: 100vh; }

    /* ── nav items ── */
    .nav-item {
      display: flex; align-items: center; gap: 10px;
      padding: 7px 12px; border-radius: 8px;
      font-size: 0.8125rem; color: #8b98b0;
      text-decoration: none; transition: all 0.15s;
      border: 1px solid transparent;
    }
    .nav-item:hover { background: rgba(255,255,255,0.045); color: #e2e8f0; }
    .nav-item.active {
      background: rgba(99,102,241,0.12);
      color: #a5b4fc;
      border-color: rgba(99,102,241,0.25);
    }
    .nav-item .count {
      margin-left: auto;
      font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;
      background: rgba(255,255,255,0.06); color: #64748b;
      padding: 1px 6px; border-radius: 4px;
    }
    .nav-item.active .count { background: rgba(99,102,241,0.2); color: #818cf8; }

    /* ── layer row colors ── */
    .layer-biz  { border-left: 2px solid rgba(245,158,11,0.55);  background: rgba(245,158,11,0.035); }
    .layer-app  { border-left: 2px solid rgba(56,189,248,0.55);  background: rgba(56,189,248,0.035); }
    .layer-tech { border-left: 2px solid rgba(52,211,153,0.55);  background: rgba(52,211,153,0.035); }
    .layer-biz:hover  { background: rgba(245,158,11,0.07); }
    .layer-app:hover  { background: rgba(56,189,248,0.07); }
    .layer-tech:hover { background: rgba(52,211,153,0.07); }

    /* ── dot badges ── */
    .dot-biz  { width:7px; height:7px; border-radius:50%; background:#f59e0b; flex-shrink:0; }
    .dot-app  { width:7px; height:7px; border-radius:50%; background:#38bdf8; flex-shrink:0; }
    .dot-tech { width:7px; height:7px; border-radius:50%; background:#34d399; flex-shrink:0; }
    .dot-none { width:7px; height:7px; border-radius:50%; background:#475569; flex-shrink:0; }

    /* ── code badge ── */
    .code-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.68rem; font-weight: 500;
      background: rgba(255,255,255,0.055);
      border: 1px solid rgba(255,255,255,0.09);
      color: #94a3b8; padding: 3px 8px; border-radius: 5px;
      white-space: nowrap; cursor: pointer;
      transition: all 0.15s; display: inline-block;
      text-decoration: none;
    }
    .code-badge:hover {
      background: rgba(99,102,241,0.15);
      border-color: rgba(99,102,241,0.35);
      color: #c7d2fe;
    }
    .code-badge.copied {
      background: rgba(52,211,153,0.15);
      border-color: rgba(52,211,153,0.35);
      color: #6ee7b7;
    }

    /* ── table ── */
    .doc-table { width: 100%; border-collapse: collapse; }
    .doc-table thead th {
      padding: 10px 16px; text-align: left;
      font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em;
      text-transform: uppercase; color: #475569;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      background: rgba(255,255,255,0.02);
    }
    .doc-table tbody tr {
      border-bottom: 1px solid rgba(255,255,255,0.04);
      transition: background 0.1s;
    }
    .doc-table tbody td {
      padding: 12px 16px; vertical-align: top;
      font-size: 0.8125rem; line-height: 1.6;
      color: #cbd5e1;
    }
    .doc-table tbody td:first-child {
      color: #475569; font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      white-space: nowrap; padding-left: 18px;
    }

    /* ── toelichting ── */
    details { margin-top: 6px; }
    details summary {
      cursor: pointer; color: #64748b; font-size: 0.75rem;
      display: inline-flex; align-items: center; gap: 4px;
      list-style: none; user-select: none;
      transition: color 0.15s;
    }
    details summary::-webkit-details-marker { display: none; }
    details summary:hover { color: #94a3b8; }
    details[open] summary { color: #818cf8; }
    .toelichting-body {
      margin-top: 8px; padding: 10px 14px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 8px; color: #94a3b8;
      font-size: 0.78rem; line-height: 1.65;
    }
    /* nested lists in toelichting */
    .toelichting-body ul { margin: 6px 0 6px 18px; list-style: disc; }
    .toelichting-body li { margin: 3px 0; }

    /* ── search overlay ── */
    #search-overlay {
      display: none; position: fixed; inset: 0; z-index: 50;
      background: rgba(0,0,0,0.7); backdrop-filter: blur(8px);
    }
    #search-overlay.open { display: flex; align-items: flex-start; justify-content: center; padding-top: 80px; }
    #search-box {
      width: 100%; max-width: 580px; margin: 0 16px;
      background: #111827; border: 1px solid rgba(255,255,255,0.1);
      border-radius: 14px; overflow: hidden;
      box-shadow: 0 25px 60px rgba(0,0,0,0.6);
    }
    #search-input {
      width: 100%; padding: 16px 20px; background: transparent;
      border: none; outline: none; color: #e2e8f0;
      font-size: 1rem; font-family: 'Inter', sans-serif;
      caret-color: #818cf8;
    }
    #search-results { max-height: 420px; overflow-y: auto; border-top: 1px solid rgba(255,255,255,0.07); }
    .search-result {
      display: flex; align-items: center; gap: 12px;
      padding: 11px 20px; cursor: pointer; transition: background 0.1s;
      text-decoration: none; color: inherit;
      border-bottom: 1px solid rgba(255,255,255,0.04);
    }
    .search-result:hover, .search-result.focused { background: rgba(99,102,241,0.08); }
    .search-result-text { flex: 1; font-size: 0.8rem; color: #94a3b8; overflow: hidden; }
    .search-result-text mark { background: none; color: #a5b4fc; font-weight: 500; }
    .search-result-code { font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #64748b; white-space: nowrap; }
    .search-result-section { font-size: 0.68rem; color: #475569; }
    #search-empty { padding: 32px 20px; text-align: center; color: #475569; font-size: 0.85rem; }

    /* ── heading font ── */
    h1, h2, h3 { font-family: 'Syne', sans-serif; }

    /* ── gradient text ── */
    .grad { background: linear-gradient(135deg, #fff 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
    .grad-accent { background: linear-gradient(135deg, #818cf8 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }

    /* ── section cards (home) ── */
    .section-card {
      background: rgba(255,255,255,0.028);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 12px; padding: 20px;
      text-decoration: none; color: inherit;
      transition: all 0.2s; display: block;
    }
    .section-card:hover {
      background: rgba(99,102,241,0.07);
      border-color: rgba(99,102,241,0.25);
      transform: translateY(-1px);
    }

    /* ── stat cards ── */
    .stat-card {
      background: rgba(255,255,255,0.028);
      border: 1px solid rgba(255,255,255,0.07);
      border-radius: 12px; padding: 24px;
    }

    /* ── legend ── */
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: #64748b; }

    /* ── top bar ── */
    #topbar {
      position: sticky; top: 0; z-index: 30;
      background: rgba(7,11,20,0.85); backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(255,255,255,0.055);
      padding: 12px 32px; display: flex; align-items: center; gap: 8px;
    }

    /* ── breadcrumb ── */
    .breadcrumb { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #475569; }
    .breadcrumb a { color: #475569; text-decoration: none; transition: color 0.15s; }
    .breadcrumb a:hover { color: #94a3b8; }
    .breadcrumb-sep { color: #2d3748; }

    /* ── hero gradient blob ── */
    .hero-blob {
      position: absolute; width: 500px; height: 350px;
      background: radial-gradient(ellipse, rgba(99,102,241,0.12) 0%, transparent 70%);
      pointer-events: none; border-radius: 50%;
    }

    /* ── animation ── */
    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(10px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .fade-up { animation: fadeUp 0.4s ease both; }
    .fade-up-1 { animation-delay: 0.05s; }
    .fade-up-2 { animation-delay: 0.10s; }
    .fade-up-3 { animation-delay: 0.15s; }
  </style>
"""

SHARED_JS = """
<script>
// ── search ──────────────────────────────────────────────────────────────────
const overlay    = document.getElementById('search-overlay');
const searchInp  = document.getElementById('search-input');
const searchRes  = document.getElementById('search-results');
const searchEmpty = document.getElementById('search-empty');

function openSearch() {
  overlay.classList.add('open');
  searchInp.focus();
}
function closeSearch() {
  overlay.classList.remove('open');
  searchInp.value = '';
  renderResults('');
}
overlay.addEventListener('click', e => { if (e.target === overlay) closeSearch(); });
document.addEventListener('keydown', e => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') { e.preventDefault(); openSearch(); }
  if (e.key === 'Escape') closeSearch();
  if (overlay.classList.contains('open')) handleResultNav(e);
});

function highlight(text, q) {
  if (!q) return escHtml(text);
  const safe = q.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
  return escHtml(text).replace(new RegExp('(' + safe + ')', 'gi'), '<mark>$1</mark>');
}
function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function renderResults(q) {
  searchRes.innerHTML = '';
  if (!q) { searchEmpty.textContent = 'Begin met typen om te zoeken...'; searchEmpty.style.display = 'block'; return; }
  const ql = q.toLowerCase();
  const hits = (window.SEARCH_INDEX || []).filter(i =>
    i.code.toLowerCase().includes(ql) ||
    i.text.toLowerCase().includes(ql) ||
    i.section_title.toLowerCase().includes(ql)
  ).slice(0, 12);
  if (!hits.length) { searchEmpty.textContent = 'Geen resultaten gevonden.'; searchEmpty.style.display = 'block'; return; }
  searchEmpty.style.display = 'none';
  hits.forEach(item => {
    const a = document.createElement('a');
    a.className = 'search-result';
    a.href = item.url;
    a.innerHTML = `
      <div class="${item.dot_class}"></div>
      <div style="flex:1;overflow:hidden">
        <div class="search-result-text" style="white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${highlight(item.text || item.name || item.code, q)}</div>
        <div class="search-result-section">${escHtml(item.section_title)}</div>
      </div>
      <div class="search-result-code">${escHtml(item.code)}</div>`;
    a.addEventListener('click', closeSearch);
    searchRes.appendChild(a);
  });
}

searchInp.addEventListener('input', () => renderResults(searchInp.value.trim()));

let focusIdx = -1;
function handleResultNav(e) {
  const items = Array.from(searchRes.querySelectorAll('.search-result'));
  if (e.key === 'ArrowDown') { e.preventDefault(); focusIdx = Math.min(focusIdx+1, items.length-1); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); focusIdx = Math.max(focusIdx-1, 0); }
  else if (e.key === 'Enter' && focusIdx >= 0) { items[focusIdx]?.click(); return; }
  else return;
  items.forEach((el,i) => el.classList.toggle('focused', i === focusIdx));
  items[focusIdx]?.scrollIntoView({ block: 'nearest' });
}

// ── mobile sidebar ───────────────────────────────────────────────────────────
const sidebar  = document.getElementById('sidebar');
const sOverlay = document.getElementById('sidebar-overlay');
const menuBtn  = document.getElementById('menu-btn');
if (menuBtn) {
  menuBtn.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    sOverlay.classList.toggle('open');
  });
}
sOverlay.addEventListener('click', () => {
  sidebar.classList.remove('open');
  sOverlay.classList.remove('open');
});

// ── code badge copy ──────────────────────────────────────────────────────────
document.querySelectorAll('.code-badge[data-code]').forEach(badge => {
  badge.addEventListener('click', () => {
    navigator.clipboard?.writeText(badge.dataset.code).catch(() => {});
    const prev = badge.textContent;
    badge.textContent = 'gekopieerd!';
    badge.classList.add('copied');
    setTimeout(() => { badge.textContent = prev; badge.classList.remove('copied'); }, 1400);
  });
});
</script>
"""


# ── navigation HTML ───────────────────────────────────────────────────────────

def build_nav(current: str | None, counts: dict[str, int], base: str) -> str:
    parts = []

    # Logo
    parts.append(f"""
      <div style="padding:20px 16px 16px; border-bottom:1px solid rgba(255,255,255,0.05)">
        <a href="{base}" style="text-decoration:none; display:flex; align-items:center; gap:10px">
          <div style="width:32px;height:32px;border-radius:8px;
               background:linear-gradient(135deg,#6366f1,#38bdf8);
               display:flex;align-items:center;justify-content:center;flex-shrink:0">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="white" width="16" height="16">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12Z"/>
            </svg>
          </div>
          <div>
            <div style="font-family:'Syne',sans-serif;font-size:0.95rem;font-weight:700;
                 background:linear-gradient(135deg,#fff,#94a3b8);
                 -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                 background-clip:text;line-height:1.1">MedMij</div>
            <div style="font-size:0.65rem;color:#475569;letter-spacing:0.05em;margin-top:1px">Afsprakenstelsel</div>
          </div>
        </a>
      </div>
    """)

    # Search trigger
    parts.append(f"""
      <div style="padding:12px 12px 8px">
        <button onclick="openSearch()" style="
          width:100%; display:flex; align-items:center; gap:8px;
          background:rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
          border-radius:8px; padding:8px 12px; cursor:pointer; transition:all 0.15s;
          color:#4b5563; font-size:0.8rem; font-family:inherit; text-align:left"
          onmouseover="this.style.background='rgba(255,255,255,0.07)';this.style.borderColor='rgba(255,255,255,0.14)'"
          onmouseout="this.style.background='rgba(255,255,255,0.04)';this.style.borderColor='rgba(255,255,255,0.08)'">
          {icon('search', 14)}
          <span style="flex:1">Zoeken...</span>
          <span style="font-size:0.65rem;background:rgba(255,255,255,0.06);padding:2px 5px;border-radius:4px;color:#374151">⌘K</span>
        </button>
      </div>
    """)

    # Home
    active_home = current is None
    parts.append(f"""
      <div style="padding:4px 8px">
        <a href="{base}" class="nav-item {'active' if active_home else ''}">
          {icon('home', 15)}
          <span>Home</span>
        </a>
      </div>
    """)

    # Section label
    parts.append('<div style="padding:12px 20px 6px"><span style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#2d3748">Inhoud</span></div>')

    # Section items
    parts.append('<div style="padding:0 8px 12px; flex:1">')
    for slug, title, _ in SECTIONS:
        active = current == slug
        count = counts.get(slug, 0)
        count_html = f'<span class="count">{count}</span>' if count else ""
        parts.append(f"""
          <a href="{base}{slug}/" class="nav-item {'active' if active else ''}">
            {icon(slug, 15)}
            <span style="flex:1">{esc(title)}</span>
            {count_html}
          </a>
        """)
    parts.append('</div>')

    # Footer links
    parts.append(f"""
      <div style="padding:12px 12px 16px; border-top:1px solid rgba(255,255,255,0.05); margin-top:auto">
        <div style="display:flex;gap:8px">
          <a href="{base}catalogue.ttl" style="flex:1;display:flex;align-items:center;justify-content:center;gap:5px;
             padding:7px;border-radius:7px;font-size:0.7rem;color:#475569;
             background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
             text-decoration:none;transition:all 0.15s"
             onmouseover="this.style.color='#94a3b8'"
             onmouseout="this.style.color='#475569'">
            {icon('external', 12)} RDF/TTL
          </a>
          <a href="{base}catalogue.jsonld" style="flex:1;display:flex;align-items:center;justify-content:center;gap:5px;
             padding:7px;border-radius:7px;font-size:0.7rem;color:#475569;
             background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
             text-decoration:none;transition:all 0.15s"
             onmouseover="this.style.color='#94a3b8'"
             onmouseout="this.style.color='#475569'">
            {icon('external', 12)} JSON-LD
          </a>
        </div>
      </div>
    """)

    return "\n".join(parts)


# ── table row ─────────────────────────────────────────────────────────────────

def build_table_row(num: int, obj: dict, base: str, section: str) -> str:
    code = obj["code"]
    layer = obj["layer"]
    text = obj["text"] or obj["name"]
    note = obj["note"]

    css_class, _ = LAYER_STYLE.get(layer, ("", "#475569"))
    dot_cls = {"layer-biz": "dot-biz", "layer-app": "dot-app", "layer-tech": "dot-tech"}.get(css_class, "dot-none")

    toelichting_html = ""
    if note:
        toelichting_html = f"""
        <details>
          <summary>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="12" height="12" style="display:inline;vertical-align:middle">
              <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5"/>
            </svg>
            Toelichting
          </summary>
          <div class="toelichting-body">{esc(note)}</div>
        </details>"""

    anchor_id = esc(code).replace(".", "_").replace("/", "_").replace(" ", "_")
    code_anchor = f'#{anchor_id}' if code and code != "—" else ""

    return f"""
    <tr class="{css_class}" id="{anchor_id}">
      <td><span style="display:inline-flex;align-items:center;gap:6px">
        <span class="{dot_cls}"></span>{num}
      </span></td>
      <td>
        <div>{esc(text)}</div>
        {toelichting_html}
      </td>
      <td style="text-align:right">
        {'<span class="code-badge" data-code="' + esc(code) + '">' + esc(code) + '</span>' if code and code != "—" else '<span style="color:#2d3748">—</span>'}
      </td>
    </tr>"""


# ── legend ────────────────────────────────────────────────────────────────────

def layer_legend(rows: list[dict]) -> str:
    seen = set()
    items = []
    for r in rows:
        css, dot_color = LAYER_STYLE.get(r["layer"], ("", "#475569"))
        dot_cls = {"layer-biz": "dot-biz", "layer-app": "dot-app", "layer-tech": "dot-tech"}.get(css, "dot-none")
        label = r["layer"] or "Onbekend"
        if dot_cls not in seen and r["layer"]:
            seen.add(dot_cls)
            items.append(f'<span class="legend-item"><span class="{dot_cls}"></span>{esc(label)}</span>')
    if not items:
        return ""
    return (
        '<div style="display:flex;flex-wrap:wrap;gap:16px;padding:14px 0 20px">'
        + " ".join(items) +
        '</div>'
    )


# ── search index ──────────────────────────────────────────────────────────────

def build_search_index(all_data: dict[str, list[dict]]) -> str:
    items = []
    for slug, title, _ in SECTIONS:
        rows = all_data.get(slug, [])
        for obj in rows:
            css, _ = LAYER_STYLE.get(obj["layer"], ("", "#475569"))
            dot_cls = {"layer-biz": "dot-biz", "layer-app": "dot-app", "layer-tech": "dot-tech"}.get(css, "dot-none")
            anchor = (obj["code"] or "").replace(".", "_").replace("/", "_").replace(" ", "_")
            items.append({
                "code":          obj["code"],
                "text":          obj["text"] or obj["name"],
                "name":          obj["name"],
                "layer":         obj["layer"],
                "section":       slug,
                "section_title": title,
                "dot_class":     dot_cls,
                "url":           f"../{slug}/#{anchor}",
            })
    return f"window.SEARCH_INDEX = {json.dumps(items, ensure_ascii=False)};"


# ── full page template ────────────────────────────────────────────────────────

def page_shell(
    title: str,
    current: str | None,
    counts: dict[str, int],
    all_data: dict[str, list[dict]],
    body_content: str,
    breadcrumb: str,
    base: str,
) -> str:
    nav = build_nav(current, counts, base)
    search_idx = build_search_index(all_data)

    return f"""<!DOCTYPE html>
<html lang="nl">
<head>
  <title>{esc(title)} — MedMij</title>
  {SHARED_HEAD}
</head>
<body>

<!-- Search overlay -->
<div id="search-overlay">
  <div id="search-box">
    <div style="display:flex;align-items:center;padding:0 16px;gap:10px;color:#475569">
      {icon('search', 18)}
      <input id="search-input" type="text" placeholder="Zoek op code, tekst of sectie..." autocomplete="off" spellcheck="false">
    </div>
    <div id="search-results"></div>
    <div id="search-empty" style="padding:28px 20px;text-align:center;color:#475569;font-size:0.82rem">Begin met typen om te zoeken...</div>
  </div>
</div>

<!-- Sidebar overlay (mobile) -->
<div id="sidebar-overlay"></div>

<!-- Sidebar -->
<aside id="sidebar">{nav}</aside>

<!-- Main -->
<div id="main">
  <!-- Top bar -->
  <div id="topbar">
    <button id="menu-btn" style="display:none;background:none;border:none;cursor:pointer;color:#475569;padding:4px;border-radius:6px;transition:color 0.15s"
      onmouseover="this.style.color='#94a3b8'" onmouseout="this.style.color='#475569'">
      {icon('menu', 20)}
    </button>
    <div class="breadcrumb">{breadcrumb}</div>
  </div>

  <!-- Content -->
  <div style="max-width:1200px;padding:32px 32px 64px">
    {body_content}
  </div>
</div>

<script>{search_idx}</script>
{SHARED_JS}
<style>@media(max-width:768px){{#menu-btn{{display:inline-flex!important}}}}</style>
</body>
</html>"""


# ── home page ─────────────────────────────────────────────────────────────────

def build_home(counts: dict[str, int], all_data: dict[str, list[dict]]) -> str:
    total = sum(counts.values())
    cards = []
    for slug, title, subtitle in SECTIONS:
        count = counts.get(slug, 0)
        cards.append(f"""
          <a href="./{slug}/" class="section-card fade-up">
            <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px;margin-bottom:10px">
              <div style="color:#4f5e78">{icon(slug, 18)}</div>
              <span style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;
                   background:rgba(99,102,241,0.1);color:#818cf8;
                   padding:2px 7px;border-radius:4px">{count}</span>
            </div>
            <div style="font-family:'Syne',sans-serif;font-size:0.9rem;font-weight:600;color:#e2e8f0;margin-bottom:4px">{esc(title)}</div>
            <div style="font-size:0.75rem;color:#475569">{esc(subtitle)}</div>
          </a>""")

    cards_html = "\n".join(cards)
    breadcrumb = '<a href="./">Home</a>'

    body = f"""
    <!-- Hero -->
    <div style="position:relative;padding:40px 0 48px;overflow:hidden">
      <div class="hero-blob" style="top:-60px;left:-80px;opacity:0.8"></div>
      <div class="hero-blob" style="top:40px;right:-120px;background:radial-gradient(ellipse,rgba(56,189,248,0.08) 0%,transparent 70%)"></div>

      <div style="position:relative">
        <div style="display:inline-flex;align-items:center;gap:8px;
             background:rgba(99,102,241,0.1);border:1px solid rgba(99,102,241,0.2);
             border-radius:999px;padding:5px 14px;margin-bottom:20px">
          <span style="width:6px;height:6px;border-radius:50%;background:#818cf8;flex-shrink:0"></span>
          <span style="font-size:0.72rem;color:#818cf8;font-weight:500;letter-spacing:0.04em">Technische documentatie</span>
        </div>

        <h1 style="font-size:clamp(2rem,4vw,3rem);font-weight:800;line-height:1.1;margin-bottom:16px"
            class="grad fade-up">
          MedMij<br>Afsprakenstelsel
        </h1>

        <p style="font-size:1rem;color:#64748b;max-width:500px;line-height:1.7;margin-bottom:28px" class="fade-up fade-up-1">
          Technische en functionele documentatie van het Nederlandse stelsel voor gezondheidsgegevensuitwisseling.
        </p>

        <div style="display:flex;gap:12px;flex-wrap:wrap" class="fade-up fade-up-2">
          <a href="./arrangements/" style="display:inline-flex;align-items:center;gap:8px;
             padding:10px 20px;border-radius:9px;
             background:linear-gradient(135deg,rgba(99,102,241,0.2),rgba(56,189,248,0.15));
             border:1px solid rgba(99,102,241,0.3);color:#a5b4fc;
             font-size:0.85rem;font-weight:500;text-decoration:none;transition:all 0.15s"
             onmouseover="this.style.background='linear-gradient(135deg,rgba(99,102,241,0.3),rgba(56,189,248,0.2))'"
             onmouseout="this.style.background='linear-gradient(135deg,rgba(99,102,241,0.2),rgba(56,189,248,0.15))'">
            Afspraken verkennen {icon('external', 14)}
          </a>
          <button onclick="openSearch()" style="display:inline-flex;align-items:center;gap:8px;
             padding:10px 20px;border-radius:9px;
             background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);
             color:#64748b;font-size:0.85rem;cursor:pointer;font-family:inherit;transition:all 0.15s"
             onmouseover="this.style.background='rgba(255,255,255,0.08)';this.style.color='#94a3b8'"
             onmouseout="this.style.background='rgba(255,255,255,0.05)';this.style.color='#64748b'">
            {icon('search', 14)} Zoeken <span style="font-size:0.65rem;background:rgba(255,255,255,0.08);padding:2px 5px;border-radius:4px">⌘K</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:48px" class="fade-up fade-up-2">
      <div class="stat-card">
        <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800" class="grad-accent">{total}</div>
        <div style="font-size:0.8rem;color:#475569;margin-top:4px">Objecten totaal</div>
      </div>
      <div class="stat-card">
        <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800" class="grad-accent">{len(SECTIONS)}</div>
        <div style="font-size:0.8rem;color:#475569;margin-top:4px">Secties</div>
      </div>
      <div class="stat-card">
        <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800" class="grad-accent">RDF</div>
        <div style="font-size:0.8rem;color:#475569;margin-top:4px">Machine-leesbare ontsluiting</div>
      </div>
    </div>

    <!-- Sections grid -->
    <div style="margin-bottom:20px">
      <h2 style="font-size:1rem;font-weight:600;color:#64748b;letter-spacing:0.04em;text-transform:uppercase;font-size:0.75rem;margin-bottom:16px">Alle secties</h2>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px">
        {cards_html}
      </div>
    </div>
    """

    return page_shell(
        title="Home",
        current=None,
        counts=counts,
        all_data=all_data,
        body_content=body,
        breadcrumb='<a href="./">Home</a>',
        base="./",
    )


# ── section page ──────────────────────────────────────────────────────────────

def build_section_page(
    slug: str,
    title: str,
    subtitle: str,
    rows: list[dict],
    counts: dict[str, int],
    all_data: dict[str, list[dict]],
) -> str:
    if not rows:
        table_html = '<p style="color:#475569;font-size:0.875rem;padding:32px 0">Geen objecten gevonden.</p>'
    else:
        table_rows = "\n".join(build_table_row(i + 1, obj, "../", slug) for i, obj in enumerate(rows))
        table_html = f"""
        {layer_legend(rows)}
        <div style="border:1px solid rgba(255,255,255,0.06);border-radius:12px;overflow:hidden">
          <table class="doc-table">
            <thead>
              <tr>
                <th style="width:52px">#</th>
                <th>Tekst</th>
                <th style="width:180px;text-align:right">Code</th>
              </tr>
            </thead>
            <tbody>{table_rows}</tbody>
          </table>
        </div>"""

    count_badge = f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;background:rgba(99,102,241,0.1);color:#818cf8;padding:3px 9px;border-radius:5px;margin-left:10px">{len(rows)}</span>'

    body = f"""
    <div style="margin-bottom:32px" class="fade-up">
      <div style="margin-bottom:8px">
        <h1 style="font-size:1.75rem;font-weight:800;display:inline-flex;align-items:baseline;gap:4px" class="grad">
          {esc(title)}{count_badge}
        </h1>
      </div>
      <p style="font-size:0.875rem;color:#475569;margin:0">{esc(subtitle)}</p>
    </div>
    <div class="fade-up fade-up-1">
      {table_html}
    </div>
    """

    breadcrumb = f'<a href="../">Home</a><span class="breadcrumb-sep">/</span><span style="color:#64748b">{esc(title)}</span>'

    return page_shell(
        title=title,
        current=slug,
        counts=counts,
        all_data=all_data,
        body_content=body,
        breadcrumb=breadcrumb,
        base="../",
    )


# ── build ─────────────────────────────────────────────────────────────────────

def build_all():
    slugs = [s for s, _, _ in SECTIONS]
    all_data = load_all_data(slugs)
    counts = {slug: len(rows) for slug, rows in all_data.items()}

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True)

    # Home
    (SITE_DIR / "index.html").write_text(build_home(counts, all_data), encoding="utf-8")
    print("Generated: site/index.html")

    # Section pages
    for slug, title, subtitle in SECTIONS:
        out_dir = SITE_DIR / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        html = build_section_page(slug, title, subtitle, all_data[slug], counts, all_data)
        (out_dir / "index.html").write_text(html, encoding="utf-8")
        print(f"Generated: site/{slug}/index.html  ({counts[slug]} objecten)")

    # RDF catalogue
    import rdflib as _rdf
    catalogue = _rdf.ConjunctiveGraph()
    for ttl_file in sorted(OBJECTEN_DIR.rglob("*.ttl")):
        catalogue.parse(str(ttl_file), format="turtle")

    out_ttl = SITE_DIR / "catalogue.ttl"
    catalogue.serialize(destination=str(out_ttl), format="turtle")

    out_jsonld = SITE_DIR / "catalogue.jsonld"
    catalogue.serialize(destination=str(out_jsonld), format="json-ld", indent=2)

    # Copy loose TTL objects so /objecten/<map>/<bestand>.ttl still works
    dest_objecten = SITE_DIR / "objecten"
    shutil.copytree(OBJECTEN_DIR, dest_objecten)

    # .nojekyll for GitHub Pages
    (SITE_DIR / ".nojekyll").touch()

    print(f"\nSite klaar in {SITE_DIR}/  ({sum(counts.values())} objecten, {len(SECTIONS)} secties)")


if __name__ == "__main__":
    build_all()
