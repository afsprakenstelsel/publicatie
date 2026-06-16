#!/usr/bin/env python3
"""Genereer MkDocs markdown-pagina's vanuit TTL-objectbestanden."""

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


def escape(text: str) -> str:
    return text.strip().replace("|", "\\|")


def text_cell(arrangement_text: str, toelichting: str) -> str:
    """Bouw een tabelcel met arrangementText en optioneel een inklapbare toelichting."""
    parts = [escape(arrangement_text).replace("\n", " ")]
    if toelichting:
        detail = escape(toelichting).replace("\n", " ")
        parts.append(
            f'<details><summary>Toelichting</summary>'
            f'<div style="margin-left:1em">{detail}</div>'
            f'</details>'
        )
    return " ".join(parts)


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

    lines = [
        f"# {title}",
        "",
        "| # | Tekst | Code |",
        "| --- | --- | --- |",
    ]
    for i, row in enumerate(rows, start=1):
        tekst = text_cell(row["arrangementText"], row["toelichting"])
        code = escape(row["code"])
        lines.append(f"| {i} | {tekst} | {code} |")

    out = DOCS_DIR / dir_path.name / "index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Gegenereerd: {out}")


def main():
    for subdir in sorted(OBJECTEN_DIR.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith("."):
            generate_page(subdir)


if __name__ == "__main__":
    main()
