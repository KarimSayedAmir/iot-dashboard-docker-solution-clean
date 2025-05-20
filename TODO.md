# IoT-Dashboard Todo-Liste (Streamlit-Version)

## Projektstruktur und Setup

- [x] Projektstruktur anlegen
- [x] ARCHITECTURE.md erstellen
- [x] TODO.md erstellen
- [ ] requirements.txt für Python-Abhängigkeiten erstellen
- [ ] Streamlit-Konfiguration einrichten (.streamlit/config.toml)
- [ ] Ordnerstruktur für Module und Daten erstellen

## Datenverarbeitung

- [ ] Basisfunktionen für CSV-Import implementieren (modules/data_processing.py)
- [ ] Funktionen für Datenbereinigung und -normalisierung erstellen
- [ ] Ausreißererkennung und -korrektur implementieren
- [ ] Aggregationsfunktionen für tägliche und wöchentliche Werte erstellen
- [ ] Zeitraumfilterung implementieren

## Datenbank

- [ ] SQLite-Datenbankschema definieren
- [ ] CRUD-Operationen für Wochen und manuelle Korrekturen implementieren
- [ ] Datenbankmigrationen für zukünftige Updates vorbereiten

## Benutzeroberfläche

- [ ] Hauptseite mit Navigation erstellen (app.py)
- [ ] CSV-Upload-Komponente implementieren
- [ ] Setup-Seite mit Datentyp-Auswahl erstellen (pages/setup.py)
- [ ] Ansichtsseite mit Visualisierungen erstellen (pages/view.py)
- [ ] Export-Funktionalität für PDF und CSV implementieren (pages/export.py)
- [ ] Filteroptionen für Zeiträume einbauen

## Visualisierung

- [ ] Zeitreihendiagramme für Sensordaten erstellen (modules/visualization.py)
- [ ] Balkendiagramme für Aggregationen implementieren
- [ ] Heatmaps für Datendichte und Ausreißer hinzufügen
- [ ] Interaktive Elemente für Grafiken (Zoom, Hover, etc.) konfigurieren

## Dokumentation

- [ ] Installationsanleitung für Endbenutzer schreiben
- [ ] Code-Dokumentation mit DocStrings vervollständigen
- [ ] Benutzerhandbuch mit Screenshots erstellen

## Optimierung und Tests

- [ ] Performance-Optimierung für große Datensätze
- [ ] Caching für wiederkehrende Berechnungen einrichten
- [ ] Tests für kritische Funktionen schreiben
- [ ] Fehlerbehandlung und Validierung verbessern
- [ ] Responsive Design für verschiedene Bildschirmgrößen anpassen

## Bereitstellung (optional)

- [ ] Dockerfile für Container-Bereitstellung erstellen
- [ ] docker-compose.yml für einfache Bereitstellung definieren
- [ ] CI/CD-Pipeline für automatisierte Tests und Deployment konfigurieren

## Erweiterungen

- [ ] Mehrsprachige Unterstützung hinzufügen (Deutsch/Englisch)
- [ ] Benutzerauthentifizierung implementieren (falls erforderlich)
- [ ] Dunkelmodus für die Benutzeroberfläche hinzufügen
- [ ] REST-API für externe Integrationen bereitstellen
- [ ] Automatische Benachrichtigungen für Anomalien implementieren 