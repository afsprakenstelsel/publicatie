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


LAYER_COLORS = {
    "Business": "#fffae6",
    "Applicatie": "#e6fcff",
    "Business/Applicatie": "#fffae6",
    "Technologie": "#e3fcef",
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
            "<details><summary>Toelichting</summary>"
            f"<div style='margin-left:1em'>{html_escape(toelichting)}</div>"
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
        bg = LAYER_COLORS.get(row["layer"], "")
        style = f' style="background-color:{bg}"' if bg else ""
        code_id = html_escape(row["code"])
        tekst = text_cell(row["arrangementText"], row["toelichting"])
        table_rows.append(
            f'<tr{style}>'
            f'<td style="white-space:nowrap;width:40px">{i}.</td>'
            f'<td>{tekst}</td>'
            f'<td style="white-space:nowrap;width:160px" id="{code_id}">{code_id}</td>'
            f'</tr>'
        )

    html_table = (
        "<table style='width:100%'>\n"
        "<colgroup><col style='width:40px'><col><col style='width:160px'></colgroup>\n"
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
