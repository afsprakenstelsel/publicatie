# MedMij Publicatie

Documentatiepublicatie van het MedMij Afsprakenstelsel. De objecten worden beheerd als RDF/Turtle-bestanden en automatisch gepubliceerd als documentatiesite via GitHub Pages.

**Site:** https://afsprakenstelsel.github.io/publicatie/

---

## C4-architectuur

### Level 1 – Systeemcontext

```structurizr
workspace "MedMij" "MedMij Afsprakenstelsel – C4 Level 1 en 2" {

    model {

        !identifiers hierarchical

        # ── Gebruikers & externe partijen ──────────────────────────────────

        persoon = person "Persoon" {
            description "Burger die gezondheidsgegevens verzamelt bij of deelt met een Aanbieder via zijn PGO."
        }

        eigenaar = person "Eigenaar MedMij" {
            description "Stichting MedMij; stelt het afsprakenstelsel vast en beheert de deelnemerslijsten."
        }

        dvp = person "Dienstverlener persoon (DVP)" {
            description "Organisatie die aan Persoon een PGO-dienst (DVP Server) aanbiedt."
        }

        dva = person "Dienstverlener aanbieder (DVA)" {
            description "Zorgaanbieder die gezondheidsgegevens beschikbaar stelt via Authorization Server en Resource Server."
        }

        digid = softwareSystem "DigiD / Authentication Server" {
            description "Externe identiteitsvoorziening die de identiteit van de Persoon vaststelt (core.rollen.205)."
            tags "External"
        }

        # ── Hoofdsysteem ────────────────────────────────────────────────────

        medmij = softwareSystem "MedMij Afsprakenstelsel" {
            description "Het totale stelsel van afspraken, componenten en lijsten dat gegevensuitwisseling tussen DVP en DVA mogelijk maakt."

            # ── Level 2 – Containers ────────────────────────────────────────

            userAgent = container "User Agent" {
                description "Webbrowser of app (front-end van DVP) die Persoon bedient en browser-redirects naar Authorization Server uitvoert. (core.rollen.203)"
                technology "Browser / WebView"
                tags "DVP-side"
            }

            dvpServer = container "DVP Server" {
                description "Back-end applicatiecomponent van DVP. Fungeert als OAuth Client; verzamelt en deelt gezondheidsgegevens namens Persoon. (core.rollen.200/203)"
                technology "HTTPS, OAuth 2.0 (RFC 6749), PKCE (RFC 7636)"
                tags "DVP-side"
            }

            authServer = container "Authorization Server" {
                description "DVA-component die toestemming en autorisatie beheert. Fungeert als OAuth Authorization Server én als Authentication Client richting DigiD. (core.rollen.201/204)"
                technology "OAuth 2.0, OpenID Connect"
                tags "DVA-side"
            }

            resourceServer = container "Resource Server" {
                description "DVA-component die gezondheidsgegevens aanbiedt of ontvangt en het access-token valideert. (core.rollen.202/205)"
                technology "FHIR R4 (HL7), HTTPS"
                tags "DVA-side"
            }

            registratie = container "MedMij Registratie" {
                description "Centrale Stelselnode van Eigenaar MedMij. Beheert en publiceert de vier stelsellijsten (ZAL, OCL, GNL, WHL) en het Aanbiedersregister (REG). (core.rollen.204)"
                technology "HTTPS, XML"
                tags "MedMij-side"
            }

            zal = container "Aanbiederslijst (ZAL)" {
                description "Dataproduct met endpoints (authorization, token, resource) per Aanbieder-Gegevensdienst-combinatie."
                technology "XML"
                tags "DataProduct"
            }

            ocl = container "OAuth Client List (OCL)" {
                description "Dataproduct waarmee DVA controleert of een DVP Server geregistreerd en toegestaan is als OAuth Client."
                technology "XML"
                tags "DataProduct"
            }

            gnl = container "Gegevensdienstnamenlijst (GNL)" {
                description "Dataproduct met gebruikersvriendelijke namen van gegevensdiensten."
                technology "XML"
                tags "DataProduct"
            }

            whl = container "Whitelist (WHL)" {
                description "Dataproduct met de toegestane Stelselnode-endpoints (ZAL/OCL/GNL/WHL) voor Node-autorisatie."
                technology "XML"
                tags "DataProduct"
            }
        }

        # ── Relaties Level 1 ────────────────────────────────────────────────

        persoon    -> medmij    "verzamelt en deelt gezondheidsgegevens"
        eigenaar   -> medmij    "beheert en stelt vast"
        dvp        -> medmij    "biedt PGO-dienst aan via"
        dva        -> medmij    "ontsluit gegevensdiensten via"
        medmij     -> digid     "authenticeert Persoon via"

        # ── Relaties Level 2 ────────────────────────────────────────────────

        persoon -> medmij.userAgent    "gebruikt PGO-interface"

        medmij.userAgent  -> medmij.dvpServer    "stuurt verzoeken door"
        medmij.userAgent  -> medmij.authServer   "browser-redirect (OAuth Authorization Code)"

        medmij.dvpServer  -> medmij.zal          "vraagt actuele endpoints op (≤15 min)"
        medmij.dvpServer  -> medmij.whl          "valideert Stelselnode-endpoints"
        medmij.dvpServer  -> medmij.authServer   "wisselt authorization code in voor access-token"
        medmij.dvpServer  -> medmij.resourceServer "haalt gezondheidsgegevens op of plaatst ze (FHIR)"

        medmij.authServer -> digid               "authenticeert Persoon (OIDC / DigiD)"
        medmij.authServer -> medmij.ocl          "controleert of DVP Server geregistreerd is"

        medmij.registratie -> medmij.zal         "publiceert"
        medmij.registratie -> medmij.ocl         "publiceert"
        medmij.registratie -> medmij.gnl         "publiceert"
        medmij.registratie -> medmij.whl         "publiceert"

        eigenaar -> medmij.registratie           "beheert"
    }

    views {

        systemContext medmij "L1-Systeemcontext" {
            title "MedMij – Level 1: Systeemcontext"
            include *
            autoLayout lr
        }

        container medmij "L2-Containers" {
            title "MedMij – Level 2: Containers"
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                background #1168bd
                color #ffffff
            }
            element "External" {
                background #999999
                color #ffffff
            }
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "DVP-side" {
                background #2e7d32
            }
            element "DVA-side" {
                background #1565c0
            }
            element "MedMij-side" {
                background #6a1b9a
            }
            element "DataProduct" {
                shape Cylinder
                background #ef6c00
                color #ffffff
            }
        }
    }
}
```

> Het script kan worden geopend in [Structurizr Lite](https://structurizr.com/help/lite) of [structurizr.com](https://structurizr.com) voor een interactief diagram.

---

## Werkwijze – Een afspraak publiceren

Een afspraak (arrangement) is een verantwoordelijkheid of verplichting waaraan deelnemers zich conformeren. Elke afspraak wordt beheerd als een RDF/Turtle-bestand en bij iedere wijziging automatisch gepubliceerd.

### 1. Maak of wijzig een TTL-bestand

Elk object staat in `objecten/<type>/<naam>.ttl`. Voor een afspraak is de map `objecten/arrangements/`.

De bestandsstructuur volgt het patroon van `core.rollen.206`:

```turtle
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .
@prefix medmij: <https://register.medmij.nl/ontology/> .
@prefix obj:    <https://register.medmij.nl/objects/> .

obj:<slug>
    a medmij:Object, medmij:Arrangement ;
    medmij:elementName "<naam van de afspraak>" ;
    medmij:code "<code, bijv. core.rollen.206>" ;
    medmij:objectClass medmij:Arrangement ;
    medmij:layer "<Business | Applicatie | Technologie>" ;
    medmij:mappingNote "<korte toelichting, max één zin>" ;
    medmij:arrangementText "<volledige tekst van de verantwoordelijkheid>" ;
    medmij:toelichting "<optionele nadere uitleg, zichtbaar als inklapbare sectie>" ;
    medmij:sourceUrl <https://afsprakenstelsel.medmij.nl/...> .
```

**Verplichte velden:** `elementName`, `code`, `objectClass`, `layer`, `mappingNote`  
**Optioneel voor afspraken:** `arrangementText`, `toelichting`, `sourceUrl`

De `layer` bepaalt de rijkleur in de gepubliceerde tabel:

| Waarde | Kleur |
|--------|-------|
| `Business` | geel |
| `Applicatie` | cyaan |
| `Technologie` | groen |

### 2. Commit en push naar `main`

```bash
git add objecten/arrangements/<naam>.ttl
git commit -m "Voeg afspraak <code> toe: <korte omschrijving>"
git push
```

### 3. Automatische publicatie (GitHub Actions)

Na iedere push naar `main` voert de workflow `.github/workflows/deploy.yml` automatisch de volgende stappen uit:

```
push naar main
    └── GitHub Actions
            ├── pip install (mkdocs-material, rdflib)
            ├── python scripts/generate_docs.py
            │       └── parseert alle TTL-bestanden met rdflib
            │           genereert docs/<map>/index.md per objectmap
            │           tabel: # · arrangementText (+ Toelichting) · code
            │           rijkleur op basis van medmij:layer
            └── mkdocs gh-deploy --force
                    └── bouwt HTML en pusht naar gh-pages branch
                            └── GitHub Pages serveert de site
```

De gepubliceerde site is binnen circa één minuut beschikbaar op:  
**https://afsprakenstelsel.github.io/publicatie/**

### Objectmappen

| Map | Objectklasse | Omschrijving |
|-----|-------------|--------------|
| `arrangements/` | Arrangement | Verantwoordelijkheden en verplichtingen (de "artikelen") |
| `specifications/` | Specification | Externe standaarden waarnaar afspraken verwijzen |
| `requirements/` | Requirement | Technische en functionele eisen |
| `implementation-guidelines/` | ImplementationGuideline | Toelichtingen en aanbevelingen |
| `components/` | Component | Architectuurcomponenten (DVP Server, Authorization Server, …) |
| `services/` | Service | Gegevensdiensten (Verzamelen, Delen, …) |
| `modules/` | Module | Functionele bouwstenen |
| `frameworks/` | Framework | Overkoepelende kaders |
| `data-products/` | DataProduct | Gepubliceerde lijsten (ZAL, OCL, GNL, WHL) |
| `data-resources/` | DataResource | Adresseerbare endpoints |
| `datasets/` | DataSet | Gegevenssets per dienst |
| `object-components/` | ObjectComponent | Compositierelaties tussen objecten |
| `objectklassen/` | ObjectClass | Definities van de objectklassen |
| `kwalificaties/` | QualificationRule | Kwalificatieregels per objectklasse |
