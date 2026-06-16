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

        persoon  -> medmij          "verzamelt en deelt gezondheidsgegevens"
        eigenaar -> medmij          "beheert en stelt vast"
        dvp      -> medmij          "biedt PGO-dienst aan via"
        dva      -> medmij          "ontsluit gegevensdiensten via"
        medmij   -> digid           "authenticeert Persoon via"

        # ── Relaties Level 2 ────────────────────────────────────────────────

        persoon -> medmij.userAgent "gebruikt PGO-interface"

        medmij.userAgent  -> medmij.dvpServer     "stuurt verzoeken door"
        medmij.userAgent  -> medmij.authServer    "browser-redirect (OAuth Authorization Code)"

        medmij.dvpServer  -> medmij.zal           "vraagt actuele endpoints op (≤15 min)"
        medmij.dvpServer  -> medmij.whl           "valideert Stelselnode-endpoints"
        medmij.dvpServer  -> medmij.authServer    "wisselt authorization code in voor access-token"
        medmij.dvpServer  -> medmij.resourceServer "haalt gezondheidsgegevens op of plaatst ze (FHIR)"

        medmij.authServer -> digid                "authenticeert Persoon (OIDC / DigiD)"
        medmij.authServer -> medmij.ocl           "controleert of DVP Server geregistreerd is"

        medmij.registratie -> medmij.zal          "publiceert"
        medmij.registratie -> medmij.ocl          "publiceert"
        medmij.registratie -> medmij.gnl          "publiceert"
        medmij.registratie -> medmij.whl          "publiceert"

        eigenaar -> medmij.registratie            "beheert"
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
