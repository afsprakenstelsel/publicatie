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


def cell(text: str) -> str:
    return text.strip().replace("\n", " ").replace("|", "\\|")


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
        "mappingNote": val(subj, MEDMIJ.mappingNote),
        "arrangementText": val(subj, MEDMIJ.arrangementText),
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
        "| Code | Toelichting | Tekst |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {cell(row['code'])} | {cell(row['mappingNote'])} | {cell(row['arrangementText'])} |"
        )

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
