#!/usr/bin/env python3
"""Genereer MkDocs markdown-pagina's en RDF-bestanden vanuit TTL-objectbestanden."""

import argparse
import difflib
import json
import re
import shutil
import subprocess
from pathlib import Path
import markdown
import rdflib
from rdflib.namespace import RDF

MEDMIJ = rdflib.Namespace("https://register.medmij.nl/ontology/")

OBJECTEN_DIR = Path("objecten")
DOCS_DIR     = Path("docs")
RELEASES_FILE = Path("releases.json")

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

def diff_text(old: str, new: str) -> str:
    """Word-level diff als inline HTML met <ins>/<del> tags."""
    old_tokens = re.findall(r'\S+|\s+', old)
    new_tokens = re.findall(r'\S+|\s+', new)
    matcher = difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False)
    parts = []
    for op, i1, i2, j1, j2 in matcher.get_opcodes():
        old_chunk = ''.join(old_tokens[i1:i2])
        new_chunk = ''.join(new_tokens[j1:j2])
        if op == 'equal':
            parts.append(old_chunk)
        elif op == 'insert':
            parts.append(f'<ins>{new_chunk}</ins>')
        elif op == 'delete':
            parts.append(f'<del>{old_chunk}</del>')
        elif op == 'replace':
            parts.append(f'<del>{old_chunk}</del><ins>{new_chunk}</ins>')
    return ''.join(parts)


def text_cell(arrangement_text: str, toelichting: str, old_text: str = "") -> str:
    if old_text and old_text != arrangement_text:
        rendered = render_md(diff_text(old_text, arrangement_text))
    else:
        rendered = render_md(arrangement_text)
    parts = [rendered]
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


def change_badge_html(change_type: str) -> str:
    if change_type == "new":
        return '<span class="change-badge change-new">NIEUW</span>'
    if change_type == "modified":
        return '<span class="change-badge change-modified">GEWIJZIGD</span>'
    return ""


# ── data laden ────────────────────────────────────────────────────────────────

def _parse_graph(g: rdflib.Graph) -> dict | None:
    subjects = list(g.subjects(RDF.type, MEDMIJ.Object))
    if not subjects:
        return None
    subj = subjects[0]
    def val(pred):
        v = g.value(subj, pred)
        return str(v).strip() if v else ""
    return {
        "uri":             str(subj),
        "code":            val(MEDMIJ.code),
        "layer":           val(MEDMIJ.layer),
        "elementName":     val(MEDMIJ.elementName),
        "mappingNote":     val(MEDMIJ.mappingNote),
        "arrangementText": val(MEDMIJ.arrangementText),
        "toelichting":     val(MEDMIJ.toelichting),
    }


def parse_object(ttl_file: Path) -> dict | None:
    g = rdflib.Graph()
    g.parse(str(ttl_file), format="turtle")
    return _parse_graph(g)


def parse_ttl_string(content: str) -> dict | None:
    g = rdflib.Graph()
    g.parse(data=content, format="turtle")
    return _parse_graph(g)


def build_context() -> tuple[dict[str, dict], dict[str, list]]:
    g = rdflib.ConjunctiveGraph()
    for ttl in sorted(OBJECTEN_DIR.rglob("*.ttl")):
        g.parse(str(ttl), format="turtle")

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


# ── versie / diff ──────────────────────────────────────────────────────────────

def load_releases() -> dict:
    if not RELEASES_FILE.exists():
        return {"latest_release": None, "versions": []}
    return json.loads(RELEASES_FILE.read_text(encoding="utf-8"))


def compute_changes(parent_ref: str) -> tuple[dict[str, str], dict[str, str]]:
    """
    Vergelijk huidige objecten met parent_ref via git diff.
    Geeft ({code: 'new'|'modified'}, {code: oude_arrangementText}) terug.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", parent_ref, "HEAD", "--", str(OBJECTEN_DIR)],
            capture_output=True, text=True, check=True,
        )
    except subprocess.CalledProcessError:
        print(f"Waarschuwing: git diff mislukt voor ref '{parent_ref}'.")
        return {}, {}

    changes: dict[str, str] = {}
    text_diffs: dict[str, str] = {}
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        status = parts[0]
        filepath = parts[-1]
        if not filepath.endswith(".ttl"):
            continue
        obj = parse_object(Path(filepath))
        if not obj or not obj["code"]:
            continue
        code = obj["code"]
        changes[code] = "new" if status == "A" else "modified"

        # Haal oude arrangementText op voor gewijzigde objecten met tekst
        if status == "M" and obj["arrangementText"]:
            old = subprocess.run(
                ["git", "show", f"{parent_ref}:{filepath}"],
                capture_output=True, text=True,
            )
            if old.returncode == 0:
                old_obj = parse_ttl_string(old.stdout)
                if old_obj and old_obj.get("arrangementText"):
                    old_text = old_obj["arrangementText"]
                    if old_text != obj["arrangementText"]:
                        text_diffs[code] = old_text

    return changes, text_diffs


def write_version_meta(version_cfg: dict, releases: dict, changes: dict[str, str]) -> None:
    """Schrijf version-meta.js zodat het template de versie-info kan inladen."""
    versions_for_js = []
    for v in releases.get("versions", []):
        versions_for_js.append({
            "id":    v["id"],
            "label": v["label"],
            "type":  v["type"],
            "path":  v.get("path", "/"),
            "date":  v.get("date"),
        })

    meta = {
        "current":        version_cfg["id"],
        "current_label":  version_cfg["label"],
        "current_type":   version_cfg["type"],
        "current_path":   version_cfg.get("path", "/"),
        "latest_release": releases.get("latest_release"),
        "versions":       versions_for_js,
        "changes":        changes,
        "has_changes":    bool(changes),
    }

    js = f"window.__MEDMIJ_VERSION_META__ = {json.dumps(meta, ensure_ascii=False, indent=2)};\n"
    out = DOCS_DIR / "version-meta.js"
    out.write_text(js, encoding="utf-8")
    print(f"Versie-meta: {out} (versie={version_cfg['id']}, {len(changes)} wijzigingen)")


# ── pagina genereren ──────────────────────────────────────────────────────────

def generate_page(
    dir_path: Path,
    obj_info: dict,
    outgoing: dict,
    changes: dict[str, str],
    text_diffs: dict[str, str],
) -> None:
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
        change  = changes.get(row["code"], "")

        if change:
            css += " row-changed"

        if row["arrangementText"]:
            tekst = text_cell(row["arrangementText"], row["toelichting"], text_diffs.get(row["code"], ""))
        else:
            tekst = object_cell(row["elementName"], row["mappingNote"])

        tekst += rel_badges_html(row["uri"], outgoing)

        change_attr = f' data-changed="{change}"' if change else ""
        code_cell = (
            f'{change_badge_html(change)}'
            f'<span class="code-badge" data-code="{code_id}">{code_id}</span>'
        )

        table_rows.append(
            f'<tr class="{css}" id="{html_escape(slug)}"{change_attr}>'
            f'<td class="col-num">{i}.</td>'
            f'<td class="col-text">{tekst}</td>'
            f'<td class="col-code">'
            f'{code_cell}'
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
    parser = argparse.ArgumentParser(description="Genereer MedMij documentatiesite.")
    parser.add_argument(
        "--version",
        metavar="VERSION_ID",
        default=None,
        help="Versie-ID uit releases.json (standaard: eerste versie of 'main')",
    )
    parser.add_argument(
        "--compare-ref",
        metavar="GIT_REF",
        default=None,
        help="Git-ref (tag/commit) om wijzigingen tegen te vergelijken. "
             "Overschrijft parent_ref uit releases.json.",
    )
    args = parser.parse_args()

    releases = load_releases()

    # Bepaal huidige versie-config
    version_cfg = None
    if args.version:
        for v in releases.get("versions", []):
            if v["id"] == args.version:
                version_cfg = v
                break
        if not version_cfg:
            print(f"Versie '{args.version}' niet gevonden in releases.json.")
    if not version_cfg:
        version_cfg = releases.get("versions", [{}])[0] if releases.get("versions") else {
            "id": "main", "label": "main", "type": "branch", "path": "/",
        }

    # Bepaal parent ref voor diff
    parent_ref = args.compare_ref or version_cfg.get("parent_ref")

    # Bereken wijzigingen t.o.v. parent
    changes: dict[str, str] = {}
    text_diffs: dict[str, str] = {}
    if parent_ref:
        print(f"Vergelijk met '{parent_ref}'...")
        changes, text_diffs = compute_changes(parent_ref)
        print(f"  {len(changes)} gewijzigde objecten gevonden ({len(text_diffs)} met tekstdiff).")

    # Schrijf version-meta.js voor het template
    write_version_meta(version_cfg, releases, changes)

    # Genereer pagina's
    obj_info, outgoing = build_context()
    print(f"Context: {len(obj_info)} objecten, {sum(len(v) for v in outgoing.values())} relaties")

    for subdir in sorted(OBJECTEN_DIR.iterdir()):
        if subdir.is_dir() and not subdir.name.startswith("."):
            generate_page(subdir, obj_info, outgoing, changes, text_diffs)

    publish_rdf()


if __name__ == "__main__":
    main()
