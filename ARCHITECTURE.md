# IoT-Dashboard Architektur (Streamlit-Version)

## Überblick

Diese Dokumentation beschreibt die Architektur der Streamlit-basierten Version des IoT-Dashboards. Die Lösung verwendet:

- **Frontend und Backend**: Streamlit (Python)
- **Datenverarbeitung**: Pandas und NumPy
- **Visualisierung**: Plotly Express und Plotly Graph Objects
- **Datenbank**: SQLite (geplant, aktuell dateibasiert)
- **Containerisierung**: Docker (optional, geplant)

## Komponenten

### 1. Datenverarbeitung

- **CSV-Import**: Einlesen und Vorverarbeitung der CSV-Daten mit Unterstützung für Metadaten-Header (erste 5 Zeilen)
- **Datenfilterung**: Filterung nach Zeiträumen (Tag, Woche, benutzerdefiniert) und Ausreißerbehandlung
- **Aggregationen**: Berechnung von Zusammenfassungen und statistischen Kennzahlen
- **Pumpen-Laufzeiten**: Automatische Erkennung und Berechnung von Pumpenlaufzeiten in Stunden
- **Flow-Berechnungen**: Präzise Berechnung von Durchflussmengen mit Berücksichtigung der Zeitintervalle
- **Template-System**: Speichern und Laden von Konfigurationseinstellungen (Grenzwerte, Pumpenvariablen)

### 2. Visualisierungskomponenten

- **Zeitreihendiagramme**: Darstellung von Sensordaten über Zeit
- **Aggregationsdiagramme**: Balkendiagramme für aggregierte Werte
- **Heatmaps**: Visualisierung von Datendichte und Anomalien
- **Dashboard-Ansicht**: Kombinierte Darstellung der wichtigsten Kennzahlen
- **Pumpen-Visualisierung**: Darstellung der Pumpenlaufzeiten und -aktivitäten
- **Flow-Visualisierung**: Spezielle Diagramme für Durchflussmengen und tägliche Statistiken

### 3. Benutzeroberfläche

- **Tabs-basierte Navigation**: Dashboard, Detailansicht, Datenanalyse, Pumpen-Übersicht, Flow-Berechnungen
- **CSV-Upload**: Upload von Daten über die Streamlit-Oberfläche
- **Filter und Parameter**: Interaktive Kontrollelemente für Datenfilterung und Zeitraumauswahl
- **Tabellarische Darstellung**: Darstellung der Rohdaten und berechneten Werte
- **Grenzwert-Konfiguration**: Definition von Maximalwerten für Variablen mit visueller Hervorhebung
- **Template-Verwaltung**: Speichern und Laden von benutzerdefinierten Einstellungen

### 4. Datenpersistenz

- **Template-Dateien**: JSON-basierte Speicherung von Benutzereinstellungen
- **Dateisystem**: Organisierte Struktur für hochgeladene Daten und generierte Berichte
- **SQLite-Datenbank**: Geplante Integration für verbesserte Datenpersistenz

## Datenfluss

1. **Datenaufnahme**: Upload von CSV-Dateien mit Unterstützung für Metadaten-Header
2. **Vorverarbeitung**: Bereinigung, Normalisierung und Erkennung von Ausreißern
3. **Analyse**: Berechnung von statistischen Kennzahlen, Aggregationen, Pumpenlaufzeiten und Durchflussmengen
4. **Visualisierung**: Darstellung der Daten in interaktiven Grafiken und Übersichten
5. **Persistenz**: Speicherung von Benutzereinstellungen in Template-Dateien

## Verzeichnisstruktur

```
iot-dashboard-streamlit/
├── app.py                    # Hauptanwendungsdatei
├── modules/                  # Funktionsmodule
│   ├── data_processing.py    # Datenverarbeitungsfunktionen
│   └── visualization.py      # Visualisierungsfunktionen
├── assets/                   # Statische Assets
├── data/                     # Datenspeicherung
│   └── templates/            # Gespeicherte Benutzereinstellungen
├── .streamlit/               # Streamlit-Konfiguration
├── requirements.txt          # Python-Abhängigkeiten (geplant)
├── Dockerfile                # Docker-Definition (geplant)
└── docker-compose.yml        # Docker-Compose-Konfiguration (geplant)
```

## Technologiestack

- **Python 3.9+**: Programmiersprache
- **Streamlit 1.20+**: Web-Framework für Datenanalyse
- **Pandas 1.5+**: Datenmanipulation und -analyse
- **Plotly 5.10+**: Interaktive Visualisierungen
- **NumPy**: Wissenschaftliche Berechnungen
- **Docker (geplant)**: Containerisierung für einfache Bereitstellung

## Spezielle Funktionen

### Pumpen-Laufzeitberechnung
- Automatische Erkennung von Pumpenvariablen (z.B. "Pump_58", "Pump_59")
- Berechnung der Laufzeit in Stunden basierend auf binären (0/1) oder booleschen (True/False) Werten
- Anzeige individueller Laufzeiten pro Pumpe und Gesamtlaufzeit

### Flow-Berechnungen
- Präzise Berechnung von Durchflussmengen unter Berücksichtigung der Zeitintervalle zwischen Messungen
- Kombinierte Anzeige der Gesamtmengen für verschiedene Geräte (z.B. Geräte 58+59)
- Tägliche Flow-Statistiken mit detaillierter Visualisierung

### Grenzwert-System
- Definition von Maximalwerten für Variablen über die Benutzeroberfläche
- Visuelle Hervorhebung von Werten, die Grenzwerte überschreiten
- Speicherung von Grenzwert-Konfigurationen in Templates

### Template-System
- Speichern und Laden von benutzerdefinierten Einstellungen (Grenzwerte, Pumpenvariablen)
- Einfache Verwaltung über die Benutzeroberfläche
- JSON-basierte Persistenz

## Online-Bereitstellungsmöglichkeiten

Für die Bereitstellung der Anwendung sind folgende Optionen geplant:

1. **Docker-basierte Bereitstellung**:
   - Containerisierung der Anwendung für einfache Installation und Konsistenz
   - Multi-Container-Setup mit Docker Compose für zukünftige Erweiterungen

2. **Cloud-Hosting**:
   - Bereitstellung auf Cloud-Plattformen wie Heroku, AWS, oder Google Cloud
   - Integration mit CI/CD-Pipelines für automatisierte Deployments

3. **Lokales Deployment**:
   - Einfache Installation für Endbenutzer mit klaren Anweisungen
   - Unterstützung für verschiedene Betriebssysteme

## Vorteile der Streamlit-Architektur

1. **Einfachere Entwicklung**: Weniger Codezeilen, schnellere Iteration
2. **Bessere Wartbarkeit**: Einheitliche Codebase in Python
3. **Verbesserte Benutzererfahrung**: Interaktive Visualisierungen und schnellere Ladezeiten
4. **Reduzierte Komplexität**: Kein separates Frontend/Backend, keine Mikro-Services
5. **Einfachere Bereitstellung**: Weniger Konfiguration und Abhängigkeiten 