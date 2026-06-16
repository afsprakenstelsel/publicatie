#!/usr/bin/env python3
"""
Genereer RDF-relaties tussen bestaande MedMij-objecten op basis van codecorrespondentie.

Nieuwe predicaten:
  medmij:governedBy       – Arrangement → Module (afspraak valt onder dit module)
  medmij:hasSpecification – Module/Service → Specification (module gebruikt deze spec)
  medmij:hasRequirement   – Module/Service → Requirement (module heeft deze eis)
  medmij:specifiesArrangement – Requirement/Specification → Arrangement (zelfde specifieke code)
"""

from pathlib import Path
import rdflib
from rdflib import Graph, Namespace, RDF, Literal
from rdflib.namespace import RDFS

MEDMIJ = Namespace("https://register.medmij.nl/ontology/")
OBJ    = Namespace("https://register.medmij.nl/objects/")
OBJECTEN_DIR = Path("objecten")
OUT_DIR = Path("objecten/relaties")

# ── helpers ───────────────────────────────────────────────────────────────────

def load_all(skip_dir="relaties") -> Graph:
    """Laad alle TTL-bestanden behalve eerder gegenereerde relaties."""
    g = Graph()
    g.bind("medmij", MEDMIJ)
    g.bind("obj", OBJ)
    for ttl in sorted(OBJECTEN_DIR.rglob("*.ttl")):
        if skip_dir in ttl.parts:
            continue
        g.parse(str(ttl), format="turtle")
    return g


def code_prefix(wildcard_code: str) -> str | None:
    """'(core.gnl.*)' → 'core.gnl'  |  andere codes → None"""
    c = wildcard_code.strip()
    if c.startswith("(") and c.endswith(".*)"):
        return c[1:-3]
    return None


def rel_graph() -> Graph:
    g = Graph()
    g.bind("medmij", MEDMIJ)
    g.bind("obj", OBJ)
    return g


# ── handmatige codevertaling ──────────────────────────────────────────────────
# Afspraken gebruiken soms andere afkortingen dan de modules.
# alst (AanbiedersLijST) = zakelijk synoniem voor zal (ZorgAanbiedersLijst).
ARRANGEMENT_PREFIX_TO_MODULE = {
    "core.alst": OBJ["opvragen-aanbiederslijst"],
}

# Wildcardpatronen die verwijzen naar een Service i.p.v. Module
PATTERN_TO_SERVICE = {
    "core.verzamelen": OBJ["verzamelen"],
    "core.delen":      OBJ["delen"],
}


# ── relatie 1: governedBy  (Arrangement → Module) ────────────────────────────

def build_governed_by(data: Graph) -> Graph:
    """Koppel afspraken aan het module waaronder ze vallen op basis van codecorrespondentie."""
    g = rel_graph()

    # Bouw prefix → module-URI map vanuit wildcardcodes in modules
    prefix_to_module: dict[str, rdflib.term.URIRef] = {}
    for s in data.subjects(RDF.type, MEDMIJ.Module):
        code = str(data.value(s, MEDMIJ.code) or "")
        prefix = code_prefix(code)
        if prefix:
            prefix_to_module[prefix] = s

    # Voeg handmatige vertalingen toe
    prefix_to_module.update(ARRANGEMENT_PREFIX_TO_MODULE)

    # Match elke afspraak op een module via codeprefix
    matched = 0
    for s in data.subjects(RDF.type, MEDMIJ.Arrangement):
        code = str(data.value(s, MEDMIJ.code) or "")
        if not code or code == "—":
            continue
        for prefix, module_uri in prefix_to_module.items():
            if code.startswith(prefix + "."):
                g.add((s, MEDMIJ.governedBy, module_uri))
                matched += 1
                break

    print(f"  governedBy:           {matched} triples")
    return g


# ── relatie 2 & 3: hasSpecification / hasRequirement  (Module → Spec/Req) ────

def build_module_links(data: Graph) -> Graph:
    """Koppel modules aan de specificaties en eisen met hetzelfde wildcardpatroon."""
    g = rel_graph()

    # Bouw code-pattern → [module-URIs] map
    pattern_to_modules: dict[str, list] = {}
    for s in data.subjects(RDF.type, MEDMIJ.Module):
        code = str(data.value(s, MEDMIJ.code) or "")
        if code_prefix(code) is not None:  # is wildcard
            pattern_to_modules.setdefault(code, []).append(s)

    specs, reqs = 0, 0

    for s in data.subjects(RDF.type, MEDMIJ.Specification):
        code = str(data.value(s, MEDMIJ.code) or "")
        if code in pattern_to_modules:
            for module in pattern_to_modules[code]:
                g.add((module, MEDMIJ.hasSpecification, s))
                specs += 1

    for s in data.subjects(RDF.type, MEDMIJ.Requirement):
        code = str(data.value(s, MEDMIJ.code) or "")
        # Wildcard → koppel aan module of service met zelfde patroon
        if code in pattern_to_modules:
            for module in pattern_to_modules[code]:
                g.add((module, MEDMIJ.hasRequirement, s))
                reqs += 1
        elif code_prefix(code) in PATTERN_TO_SERVICE:
            service = PATTERN_TO_SERVICE[code_prefix(code)]
            g.add((service, MEDMIJ.hasRequirement, s))
            reqs += 1

    print(f"  hasSpecification:     {specs} triples")
    print(f"  hasRequirement:       {reqs} triples")
    return g


# ── relatie 4: specifiesArrangement  (Req/Spec → Arrangement, zelfde code) ───

def build_specifies_arrangement(data: Graph) -> Graph:
    """
    Wanneer een Requirement of Specification een specifieke code (geen wildcard)
    deelt met een Arrangement, legt dit predicaat de relatie vast.
    """
    g = rel_graph()

    # Index: code → arrangement-URI
    code_to_arrangement: dict[str, rdflib.term.URIRef] = {}
    for s in data.subjects(RDF.type, MEDMIJ.Arrangement):
        code = str(data.value(s, MEDMIJ.code) or "")
        if code and code != "—" and not code.startswith("("):
            code_to_arrangement[code] = s

    matched = 0
    for cls in (MEDMIJ.Requirement, MEDMIJ.Specification):
        for s in data.subjects(RDF.type, cls):
            code = str(data.value(s, MEDMIJ.code) or "")
            if code and not code.startswith("(") and code in code_to_arrangement:
                arrangement = code_to_arrangement[code]
                g.add((s, MEDMIJ.specifiesArrangement, arrangement))
                matched += 1

    print(f"  specifiesArrangement: {matched} triples")
    return g


# ── ontologie-definities ──────────────────────────────────────────────────────

def build_ontology() -> Graph:
    g = rel_graph()
    defs = [
        (MEDMIJ.governedBy,
         "Verbindt een Arrangement met het Module waaronder het valt (op basis van codeprefix)."),
        (MEDMIJ.hasSpecification,
         "Verbindt een Module of Service met een Specificatie die erop van toepassing is."),
        (MEDMIJ.hasRequirement,
         "Verbindt een Module of Service met een Eis die erop van toepassing is."),
        (MEDMIJ.specifiesArrangement,
         "Verbindt een Eis of Specificatie met de Afspraak die zij nader uitwerkt (zelfde code)."),
    ]
    for pred, comment in defs:
        g.add((pred, RDF.type, RDF.Property))
        g.add((pred, RDFS.comment, Literal(comment, lang="nl")))
    print(f"  predicaatdefinities:  {len(defs)} triples")
    return g


# ── samenvoegen en schrijven ──────────────────────────────────────────────────

def merge(*graphs: Graph) -> Graph:
    result = rel_graph()
    for g in graphs:
        for triple in g:
            result.add(triple)
    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Laden van alle objecten...")
    data = load_all()
    print(f"  {len(data)} triples geladen uit objecten/\n")

    print("Genereren van relaties:")
    g_onto   = build_ontology()
    g_gov    = build_governed_by(data)
    g_mod    = build_module_links(data)
    g_spec   = build_specifies_arrangement(data)

    combined = merge(g_onto, g_gov, g_mod, g_spec)
    total = len(combined)

    out_path = OUT_DIR / "afgeleid.ttl"
    combined.serialize(destination=str(out_path), format="turtle")
    print(f"\nGeschreven: {out_path}  ({total} triples totaal)")


if __name__ == "__main__":
    main()
