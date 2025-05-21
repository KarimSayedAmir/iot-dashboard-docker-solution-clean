# IoT-Dashboard Todo-Liste (Streamlit-Version)

## Projektstruktur und Setup

- [x] Projektstruktur anlegen
- [x] ARCHITECTURE.md erstellen
- [x] TODO.md erstellen
- [ ] requirements.txt für Python-Abhängigkeiten erstellen
- [ ] Streamlit-Konfiguration einrichten (.streamlit/config.toml)
- [x] Ordnerstruktur für Module und Daten erstellen

## Datenverarbeitung

- [x] Basisfunktionen für CSV-Import implementieren (modules/data_processing.py)
- [x] Funktionen für Datenbereinigung und -normalisierung erstellen
- [x] Ausreißererkennung und -korrektur implementieren
- [x] Aggregationsfunktionen für tägliche und wöchentliche Werte erstellen
- [x] Zeitraumfilterung implementieren

## Datenbank

- [ ] SQLite-Datenbankschema definieren
- [ ] CRUD-Operationen für Wochen und manuelle Korrekturen implementieren
- [ ] Datenbankmigrationen für zukünftige Updates vorbereiten

## Benutzeroberfläche

- [x] Hauptseite mit Navigation erstellen (app.py)
- [x] CSV-Upload-Komponente implementieren
- [x] Filteroptionen für Zeiträume einbauen
- [ ] Setup-Seite mit Datentyp-Auswahl erstellen (pages/setup.py)
- [ ] Ansichtsseite mit Visualisierungen erstellen (pages/view.py)
- [ ] Export-Funktionalität für PDF und CSV implementieren (pages/export.py)

## Visualisierung

- [x] Zeitreihendiagramme für Sensordaten erstellen (modules/visualization.py)
- [x] Balkendiagramme für Aggregationen implementieren
- [x] Heatmaps für Datendichte und Ausreißer hinzufügen
- [x] Interaktive Elemente für Grafiken (Zoom, Hover, etc.) konfigurieren

## Dokumentation

- [ ] Installationsanleitung für Endbenutzer schreiben
- [ ] Code-Dokumentation mit DocStrings vervollständigen
- [ ] Benutzerhandbuch mit Screenshots erstellen

## Optimierung und Tests

- [x] Performance-Optimierung für große Datensätze
- [ ] Caching für wiederkehrende Berechnungen einrichten
- [ ] Tests für kritische Funktionen schreiben
- [x] Fehlerbehandlung und Validierung verbessern
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

## Erledigte Aufgaben
- ✅ Umstellung auf Streamlit
- ✅ CSV-Import mit Metadaten-Header implementieren (Überspringe die ersten 5 Zeilen)
- ✅ Pumpenlaufzeiten berechnen
- ✅ Automatische Erkennung von Pumpen-Variablen
- ✅ Template-System für das Speichern und Laden von Einstellungen
- ✅ Fehlerbehebung in der Heatmap-Visualisierung (NaN-Fehler)
- ✅ Flow-Berechnungen und Visualisierungen für Anlagen 0058 und 0059
  - Implementiert Gesamtmengenberechnung für Flow_Rate_59 und ARA_Flow
  - Hinzufügen eines neuen "Flow-Berechnungen"-Tabs mit detaillierten Visualisierungen
  - Verbesserung der Dashboard-Anzeige für Flow-Werte
- ✅ Präzise Flow-Berechnungen mit Berücksichtigung der Zeitintervalle
  - Implementierung einer verbesserten Berechnungsmethode für Flow-Mengen
  - Anwendung auf Gesamtberechnung und tägliche Statistiken
  - Kombination der Flow-Mengen von Geräten 58 und 59

## Laufende Aufgaben
- Verbesserte Datenprozessierung und Ausreißererkennung
- Optimierung der Benutzeroberfläche für bessere Übersichtlichkeit

## Zukünftige Verbesserungen
- Integration von Realtime-Updates aus IoT-Geräten
- Export von Berichten als PDF oder Excel-Dateien
- Erweiterung des Alarmierungssystems bei Überschreitung von Grenzwerten
- Mobile Benachrichtigungen konfigurieren
- Implementierung einer Datenbank zur persistenten Speicherung von Analyseergebnissen 