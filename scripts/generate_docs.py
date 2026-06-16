#!/usr/bin/env python3
"""Genereer MkDocs markdown-pagina's en RDF-bestanden vanuit TTL-objectbestanden."""

import shutil
from pathlib import Path
import rdflib
from rdflib.namespace import RDF

MEDMIJ = rdflib.Namespace("https://register.medmij.nl/ontology/")

OBJECTEN_DIR = Path("objecten")
DOCS_DIR = Path("docs")

DIR_TITLES = {
    "arrangements": "Afspraken",
    "components": "Componenten",
    "data-products": "Dataproducten",
    "data-resources": "Gegevensbronnen",
    "datasets": "Gegevenssets",
    "frameworks": "Frameworks",
    "implementation-guidelines": "Implementatierichtlijnen",
    "kwalificaties": "Kwalificaties",
    "modules": "Modules",
    "object-components": "Objectcomponenten",
    "objectklassen": "Objectklassen",
    "requirements": "Eisen",
    "services": "Diensten",
    "specifications": "Specificaties",
}


LAYER_CLASSES = {
    "Business": "layer-biz",
    "Applicatie": "layer-app",
    "Business/Applicatie": "layer-biz",
    "Technologie": "layer-tech",
}


def html_escape(text: str) -> str:
    return (
        text.strip()
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def text_cell(arrangement_text: str, toelichting: str) -> str:
    parts = [html_escape(arrangement_text)]
    if toelichting:
        parts.append(
            "<details><summary>"
            '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
            'stroke-width="1.5" stroke="currentColor" width="13" height="13" style="flex-shrink:0">'
            '<path stroke-linecap="round" stroke-linejoin="round" '
            'd="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 '
            '1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"/>'
            "</svg>"
            "Toelichting</summary>"
            f"<div class='toelichting-body'>{html_escape(toelichting)}</div>"
            "</details>"
        )
    return "".join(parts)


def parse_object(ttl_file: Path) -> dict | None:
    g = rdflib.Graph()
    g.parse(str(ttl_file), format="turtle")

    def val(subj, pred):
        v = g.value(subj, pred)
        return str(v).strip() if v else ""

    subjects = list(g.subjects(RDF.type, MEDMIJ.Object))
    if not subjects:
        return None

    subj = subjects[0]
    return {
        "code": val(subj, MEDMIJ.code),
        "layer": val(subj, MEDMIJ.layer),
        "arrangementText": val(subj, MEDMIJ.arrangementText),
        "toelichting": val(subj, MEDMIJ.toelichting),
    }


def generate_page(dir_path: Path) -> None:
    title = DIR_TITLES.get(dir_path.name, dir_path.name.replace("-", " ").title())
    rows = []

    for ttl_file in sorted(dir_path.glob("*.ttl")):
        obj = parse_object(ttl_file)
        if obj:
            rows.append(obj)

    if not rows:
        return

    table_rows = []
    for i, row in enumerate(rows, start=1):
        css = LAYER_CLASSES.get(row["layer"], "layer-none")
        code_id = html_escape(row["code"])
        tekst = text_cell(row["arrangementText"], row["toelichting"])
        table_rows.append(
            f'<tr class="{css}">'
            f'<td class="col-num">{i}.</td>'
            f'<td class="col-text">{tekst}</td>'
            f'<td class="col-code" id="{code_id}">'
            f'<span class="code-badge" data-code="{code_id}">{code_id}</span>'
            f'</td>'
            f'</tr>'
        )

    html_table = (
        "<table>\n"
        "<thead><tr><th>#</th><th>Tekst</th><th>Code</th></tr></thead>\n"
        "<tbody>\n"
        + "\n".join(table_rows)
        + "\n</tbody>\n</table>"
    )

    lines = [f"# {title}", "", html_table, ""]

    out = DOCS_DIR / dir_path.name / "index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Gegenereerd: {out}")


def publish_rdf() -> None:
    """Kopieer alle TTL-bestanden naar docs/objecten/ en genereer catalogue.ttl."""

    # Losse TTL-bestanden — toegankelijk via /objecten/<map>/<bestand>.ttl
    dest_root = DOCS_DIR / "objecten"
    if dest_root.exists():
        shutil.rmtree(dest_root)
    shutil.copytree(OBJECTEN_DIR, dest_root)
    print(f"RDF-bestanden gekopieerd naar {dest_root}/")

    # Gecombineerde catalogus — alle objecten in één bestand
    catalogue = rdflib.ConjunctiveGraph()
    for ttl_file in sorted(OBJECTEN_DIR.rglob("*.ttl")):
        catalogue.parse(str(ttl_file), format="turtle")

    out_ttl = DOCS_DIR / "catalogue.ttl"
    catalogue.serialize(destination=str(out_ttl), format="turtle")
    print(f"Gecombineerde catalogus: {out_ttl}")

    out_jsonld = DOCS_DIR / "catalogue.jsonld"
    catalogue.serialize(destination=str(out_jsonld), format="json-ld", indent=2)
    print(f"Gecombineerde catalogus: {out_jsonld}")


def main():
    for subdir in sorted(OBJECTEN_DIR.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith("."):
            generate_page(subdir)
    publish_rdf()


if __name__ == "__main__":
    main()
