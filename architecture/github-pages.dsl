workspace "MedMij Publicatie" "GitHub Pages publicatiepipeline – C4 Level 2" {

    model {

        !identifiers hierarchical

        redacteur = person "Redacteur" {
            description "Beheert TTL-objectbestanden lokaal, pusht wijzigingen naar GitHub en start optioneel een lokale multi-versie build."
        }

        lezer = person "Lezer" {
            description "Raadpleegt de gepubliceerde documentatiesite via een browser."
        }

        publicatie = softwareSystem "MedMij Publicatie" {
            description "Publicatiepipeline van RDF-objecten naar een versioned statische documentatiesite op GitHub Pages. Ondersteunt zowel CI-deployment (GitHub Actions) als lokale multi-versie builds via build_all.py."

            repo = container "GitHub Repository (main)" {
                description "Bevat alle TTL-objectbestanden (objecten/), scripts, releases.json, mkdocs.yml, custom_theme/ en de GitHub Actions workflow."
                technology "Git / GitHub"
                tags "Storage"
            }

            releasesJson = container "releases.json" {
                description "Versiemanifest met per versie: id, label, type (release/branch), git_ref, URL-pad en parent_ref (voor git-diff wijzigingsdetectie)."
                technology "JSON"
                tags "DataProduct"
            }

            actions = container "GitHub Actions Runner" {
                description "Voert de deploy-workflow uit na push naar main: installeert dependencies (rdflib, mkdocs), draait add_relations.py en generate_docs.py en publiceert de site via mkdocs gh-deploy."
                technology "ubuntu-latest, Python 3, pip"
                tags "CI"
            }

            addRelationsScript = container "add_relations.py" {
                description "Genereert RDF-relaties (governedBy, hasSpecification, hasRequirement, specifiesArrangement) tussen bestaande objecten op basis van codecorrespondentie. Schrijft TTL-bestanden naar objecten/relaties/."
                technology "Python, rdflib"
                tags "Script"
            }

            generateScript = container "generate_docs.py" {
                description "Parseert TTL-objectbestanden met rdflib. Berekent nieuw/gewijzigde objecten via git diff t.o.v. parent_ref. Genereert HTML-tabellen als Markdown-pagina's, schrijft version-meta.js (voor versie-picker) en publiceert RDF-catalogus (catalogue.ttl + catalogue.jsonld)."
                technology "Python, rdflib, markdown"
                tags "Script"
            }

            buildAllScript = container "build_all.py" {
                description "Lokale multi-versie buildorchestrator. Leest releases.json, maakt per versie een tijdelijke git-worktree aan, kopieert buildtools (generate_docs.py, custom_theme, releases.json) naar de worktree en bouwt elke versie naar site/{path}/. Biedt optioneel een ingebouwde preview-server (--serve)."
                technology "Python, git worktree, http.server"
                tags "Script"
            }

            customTheme = container "custom_theme/" {
                description "Aangepast MkDocs-theme met versie-picker in de topbar, filterbar voor wijzigingen (NIEUW/GEWIJZIGD) en de version-meta.js loader die versie-informatie injecteert in de pagina."
                technology "HTML, CSS, JavaScript (Jinja2 template)"
                tags "Script"
            }

            mkdocs = container "MkDocs" {
                description "Bouwt een statische HTML-site van de gegenereerde Markdown-pagina's met het custom_theme. In CI via mkdocs gh-deploy --force; in lokale builds via mkdocs build naar site/{path}/."
                technology "MkDocs"
                tags "Script"
            }

            ghPages = container "gh-pages branch" {
                description "Bevat de gebouwde statische HTML-site met alle versies in subdirectories. CI-deploys via mkdocs gh-deploy; lokale deploys via ghp-import site/ -p."
                technology "HTML, CSS, JavaScript"
                tags "Storage"
            }

            cdn = container "GitHub Pages CDN" {
                description "Serveert de statische site publiek via HTTPS."
                technology "GitHub Pages"
                tags "Hosting"
            }
        }

        # ── Redacteur ────────────────────────────────────────────────────────

        redacteur -> publicatie.repo           "pusht gewijzigde TTL-bestanden naar main"
        redacteur -> publicatie.buildAllScript "start lokale multi-versie build"

        # ── CI-pipeline (GitHub Actions) ─────────────────────────────────────

        publicatie.repo    -> publicatie.actions          "triggert workflow bij push naar main"
        publicatie.actions -> publicatie.repo             "checkt bronbestanden uit (fetch-depth 0)"
        publicatie.actions -> publicatie.addRelationsScript "voert uit"
        publicatie.addRelationsScript -> publicatie.repo  "schrijft objecten/relaties/*.ttl"
        publicatie.actions -> publicatie.generateScript   "voert uit"
        publicatie.generateScript -> publicatie.releasesJson "leest versie-configuratie"
        publicatie.generateScript -> publicatie.repo      "leest objecten/*.ttl + git-history; schrijft docs/ + version-meta.js"
        publicatie.actions -> publicatie.mkdocs           "voert mkdocs gh-deploy --force uit"
        publicatie.mkdocs  -> publicatie.repo             "leest mkdocs.yml en docs/"
        publicatie.mkdocs  -> publicatie.customTheme      "gebruikt als theme"
        publicatie.mkdocs  -> publicatie.ghPages          "pusht gebouwde HTML"

        # ── Lokale multi-versie build ─────────────────────────────────────────

        publicatie.buildAllScript -> publicatie.releasesJson  "leest alle versies en git-refs"
        publicatie.buildAllScript -> publicatie.repo          "maakt git-worktree per versie (detached)"
        publicatie.buildAllScript -> publicatie.customTheme   "kopieert naar elke worktree"
        publicatie.buildAllScript -> publicatie.generateScript "voert uit per versie (--version, --compare-ref)"
        publicatie.buildAllScript -> publicatie.mkdocs        "voert mkdocs build uit per versie naar site/{path}/"
        publicatie.buildAllScript -> publicatie.ghPages       "deployt alle versies via ghp-import site/ -p"

        # ── Publicatie ────────────────────────────────────────────────────────

        publicatie.ghPages -> publicatie.cdn "geserveerd door"
        lezer -> publicatie.cdn "raadpleegt documentatiesite via browser"
    }

    views {

        container publicatie "L2-GitHub-Pages" {
            title "MedMij Publicatie – Level 2: GitHub Pages pipeline"
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
            element "Container" {
                background #438dd5
                color #ffffff
            }
            element "Storage" {
                shape Cylinder
                background #f5a623
                color #000000
            }
            element "DataProduct" {
                shape Cylinder
                background #ef6c00
                color #ffffff
            }
            element "CI" {
                background #e67e22
                color #ffffff
            }
            element "Script" {
                background #85bbf0
                color #000000
            }
            element "Hosting" {
                background #27ae60
                color #ffffff
            }
        }
    }
}
