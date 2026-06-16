#!/usr/bin/env python3
"""Genereer MkDocs markdown-pagina's en RDF-bestanden vanuit TTL-objectbestanden."""

import shutil
from pathlib import Path
import markdown
import rdflib
from rdflib.namespace import RDF

MEDMIJ = rdflib.Namespace("https://register.medmij.nl/ontology/")

OBJECTEN_DIR = Path("objecten")
DOCS_DIR     = Path("docs")

DIR_TITLES = {
    "arrangements":             "Afspraken",
    "components":               "Componenten",
    "data-products":            "Dataproducten",
    "data-resources":           "Gegevensbronnen",
    "datasets":                 "Gegevenssets",
    "frameworks":               "Frameworks",
    "implementation-guidelines":"Implementatierichtlijnen",
    "kwalificaties":            "Kwalificaties",
    "modules":                  "Modules",
    "object-components":        "Objectcomponenten",
    "objectklassen":            "Objectklassen",
    "requirements":             "Eisen",
    "services":                 "Diensten",
    "specifications":           "Specificaties",
}

LAYER_CLASSES = {
    "Business":          "layer-biz",
    "Applicatie":        "layer-app",
    "Business/Applicatie":"layer-biz",
    "Technologie":       "layer-tech",
}

# Mapping van RDF-type → sectie-directory
TYPE_TO_SECTION: dict[str, str] = {
    str(MEDMIJ.Arrangement):             "arrangements",
    str(MEDMIJ.Module):                  "modules",
    str(MEDMIJ.Specification):           "specifications",
    str(MEDMIJ.Requirement):             "requirements",
    str(MEDMIJ.Service):                 "services",
    str(MEDMIJ.Framework):               "frameworks",
    str(MEDMIJ.Component):               "components",
    str(MEDMIJ.DataSet):                 "datasets",
    str(MEDMIJ.DataProduct):             "data-products",
    str(MEDMIJ.DataResource):            "data-resources",
    str(MEDMIJ.ImplementationGuideline): "implementation-guidelines",
    str(MEDMIJ.QualificationRule):       "kwalificaties",
    str(MEDMIJ.ObjectClass):             "objectklassen",
    str(MEDMIJ.ObjectComponent):         "object-components",
}

# Relatie-predicaten waarvoor we badges tonen (uitgaande richting)
RELATION_PREDS = [
    MEDMIJ.governedBy,
    MEDMIJ.hasSpecification,
    MEDMIJ.hasRequirement,
    MEDMIJ.specifiesArrangement,
]

_INFO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" '
    'stroke-width="1.5" stroke="currentColor" width="13" height="13" style="flex-shrink:0">'
    '<path stroke-linecap="round" stroke-linejoin="round" '
    'd="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 '
    '1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"/>'
    "</svg>"
)


# ── helpers ───────────────────────────────────────────────────────────────────

def html_escape(text: str) -> str:
    return (
        text.strip()
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_md(text: str) -> str:
    return markdown.markdown(text.strip()).replace("\n", "")


# ── cel-renderers ─────────────────────────────────────────────────────────────

def text_cell(arrangement_text: str, toelichting: str) -> str:
    parts = [render_md(arrangement_text)]
    if toelichting:
        parts.append(
            f"<details><summary>{_INFO_SVG}Toelichting</summary>"
            f"<div class='toelichting-body'>{render_md(toelichting)}</div>"
            "</details>"
        )
    return "".join(parts)


def object_cell(element_name: str, mapping_note: str) -> str:
    parts = []
    if element_name:
        parts.append(f"<span class='obj-name'>{html_escape(element_name)}</span>")
    if mapping_note:
        parts.append(f"<span class='obj-note'>{html_escape(mapping_note)}</span>")
    return "".join(parts)


def rel_badges_html(uri: str, outgoing: dict[str, list]) -> str:
    """Geef HTML voor relatiebadges van een object, of lege string als er geen zijn."""
    targets = outgoing.get(uri, [])
    if not targets:
        return ""
    badges = []
    for t in targets:
        href = f"../{t['section']}/#{t['slug']}"
        name = html_escape(t["elementName"]) or html_escape(t["slug"])
        label = html_escape(t["section_label"])
        badges.append(
            f'<a href="{href}" class="rel-badge">'
            f'<span class="rel-section">{label}</span>'
            f'{name}'
            f'</a>'
        )
    return f'<div class="rel-badges">{"".join(badges)}</div>'


# ── data laden ────────────────────────────────────────────────────────────────

def parse_object(ttl_file: Path) -> dict | None:
    g = rdflib.Graph()
    g.parse(str(ttl_file), format="turtle")

    def val(pred):
        v = g.value(subj, pred)
        return str(v).strip() if v else ""

    subjects = list(g.subjects(RDF.type, MEDMIJ.Object))
    if not subjects:
        return None

    subj = subjects[0]
    return {
        "uri":             str(subj),
        "code":            val(MEDMIJ.code),
        "layer":           val(MEDMIJ.layer),
        "elementName":     val(MEDMIJ.elementName),
        "mappingNote":     val(MEDMIJ.mappingNote),
        "arrangementText": val(MEDMIJ.arrangementText),
        "toelichting":     val(MEDMIJ.toelichting),
    }


def build_context() -> tuple[dict[str, dict], dict[str, list]]:
    """
    Laad alle TTL-bestanden en geef twee lookups terug:
      obj_info  – uri → {slug, elementName, section}
      outgoing  – uri → [{section_label, slug, elementName, section}]
    """
    g = rdflib.ConjunctiveGraph()
    for ttl in sorted(OBJECTEN_DIR.rglob("*.ttl")):
        g.parse(str(ttl), format="turtle")

    # Object-index
    obj_info: dict[str, dict] = {}
    for s in g.subjects(RDF.type, MEDMIJ.Object):
        slug = str(s).split("/")[-1]
        element_name = str(g.value(s, MEDMIJ.elementName) or "")
        section = None
        for type_node in g.objects(s, RDF.type):
            section = TYPE_TO_SECTION.get(str(type_node))
            if section:
                break
        obj_info[str(s)] = {
            "slug":        slug,
            "elementName": element_name,
            "section":     section,
        }

    # Uitgaande relaties
    outgoing: dict[str, list] = {}
    for pred in RELATION_PREDS:
        for s, o in g.subject_objects(pred):
            target = obj_info.get(str(o))
            if not target or not target["section"]:
                continue
            outgoing.setdefault(str(s), []).append({
                "section_label": DIR_TITLES.get(target["section"], target["section"]),
                "slug":          target["slug"],
                "elementName":   target["elementName"],
                "section":       target["section"],
            })

    return obj_info, outgoing


# ── pagina genereren ──────────────────────────────────────────────────────────

def generate_page(dir_path: Path, obj_info: dict, outgoing: dict) -> None:
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
        css     = LAYER_CLASSES.get(row["layer"], "layer-none")
        code_id = html_escape(row["code"])
        slug    = obj_info.get(row["uri"], {}).get("slug", "")

        if row["arrangementText"]:
            tekst = text_cell(row["arrangementText"], row["toelichting"])
        else:
            tekst = object_cell(row["elementName"], row["mappingNote"])

        tekst += rel_badges_html(row["uri"], outgoing)

        table_rows.append(
            f'<tr class="{css}" id="{html_escape(slug)}">'
            f'<td class="col-num">{i}.</td>'
            f'<td class="col-text">{tekst}</td>'
            f'<td class="col-code">'
            f'<span class="code-badge" data-code="{code_id}">{code_id}</span>'
            f'</td>'
            f'</tr>'
        )

    html_table = (
        "<table>\n"
        "<thead><tr><th>#</th><th>Tekst</th>"
        "<th style='text-align:right'>Code</th></tr></thead>\n"
        "<tbody>\n"
        + "\n".join(table_rows)
        + "\n</tbody>\n</table>"
    )

    out = DOCS_DIR / dir_path.name / "index.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join([f"# {title}", "", html_table, ""]), encoding="utf-8")
    print(f"Gegenereerd: {out}")


# ── RDF publiceren ────────────────────────────────────────────────────────────

def publish_rdf() -> None:
    dest_root = DOCS_DIR / "objecten"
    if dest_root.exists():
        shutil.rmtree(dest_root)
    shutil.copytree(OBJECTEN_DIR, dest_root)
    print(f"RDF-bestanden gekopieerd naar {dest_root}/")

    catalogue = rdflib.ConjunctiveGraph()
    for ttl_file in sorted(OBJECTEN_DIR.rglob("*.ttl")):
        catalogue.parse(str(ttl_file), format="turtle")

    out_ttl = DOCS_DIR / "catalogue.ttl"
    catalogue.serialize(destination=str(out_ttl), format="turtle")
    print(f"Gecombineerde catalogus: {out_ttl}")

    out_jsonld = DOCS_DIR / "catalogue.jsonld"
    catalogue.serialize(destination=str(out_jsonld), format="json-ld", indent=2)
    print(f"Gecombineerde catalogus: {out_jsonld}")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    obj_info, outgoing = build_context()
    print(f"Context: {len(obj_info)} objecten, {sum(len(v) for v in outgoing.values())} relaties")

    for subdir in sorted(OBJECTEN_DIR.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith("."):
            generate_page(subdir, obj_info, outgoing)

    publish_rdf()


if __name__ == "__main__":
    main()
