workspace "MedMij Publicatie" "GitHub Pages publicatiepipeline – C4 Level 2" {

    model {

        !identifiers hierarchical

        redacteur = person "Redacteur" {
            description "Beheert TTL-objectbestanden lokaal en pusht wijzigingen naar GitHub."
        }

        lezer = person "Lezer" {
            description "Raadpleegt de gepubliceerde documentatiesite via een browser."
        }

        publicatie = softwareSystem "MedMij Publicatie" {
            description "Automatische publicatiepipeline van RDF-objecten naar een statische documentatiesite op GitHub Pages."

            repo = container "GitHub Repository (main)" {
                description "Bevat alle TTL-objectbestanden, het generatiescript, de MkDocs-configuratie en de GitHub Actions workflow."
                technology "Git / GitHub"
                tags "Storage"
            }

            actions = container "GitHub Actions Runner" {
                description "Voert de deploy-workflow uit na iedere push naar main: installeert dependencies (rdflib, mkdocs-material), genereert Markdown-pagina's en bouwt de statische HTML-site."
                technology "ubuntu-latest, Python 3, pip"
                tags "CI"
            }

            generateScript = container "generate_docs.py" {
                description "Parseert alle TTL-bestanden per objectmap met rdflib. Genereert voor elke map een HTML-tabel (# · arrangementText + Toelichting · code) met rijkleuren op basis van medmij:layer."
                technology "Python, rdflib"
                tags "Script"
            }

            mkdocs = container "MkDocs (Material)" {
                description "Bouwt een statische HTML-site van de gegenereerde Markdown-pagina's. Gebruikt het Material-theme met custom CSS voor brede tabelweergave."
                technology "MkDocs, mkdocs-material"
                tags "Script"
            }

            ghPages = container "gh-pages branch" {
                description "Bevat de door MkDocs gebouwde statische HTML-site. Wordt bij iedere deploy volledig overschreven."
                technology "HTML, CSS, JavaScript"
                tags "Storage"
            }

            cdn = container "GitHub Pages CDN" {
                description "Serveert de statische site publiek via HTTPS op afsprakenstelsel.github.io/publicatie/."
                technology "GitHub Pages"
                tags "Hosting"
            }
        }

        # ── Relaties ────────────────────────────────────────────────────────

        redacteur -> publicatie.repo         "pusht gewijzigde TTL-bestanden naar main"

        publicatie.repo    -> publicatie.actions        "triggert workflow bij push naar main"
        publicatie.actions -> publicatie.repo           "checkt bronbestanden uit"
        publicatie.actions -> publicatie.generateScript "voert uit"
        publicatie.generateScript -> publicatie.repo    "leest objecten/*.ttl, schrijft docs/**/index.md"
        publicatie.actions -> publicatie.mkdocs         "voert mkdocs gh-deploy --force uit"
        publicatie.mkdocs  -> publicatie.repo           "leest mkdocs.yml, docs/ en stylesheets"
        publicatie.mkdocs  -> publicatie.ghPages        "pusht gebouwde HTML"
        publicatie.ghPages -> publicatie.cdn            "geserveerd door"

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
