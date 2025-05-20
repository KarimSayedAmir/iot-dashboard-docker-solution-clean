# IoT-Dashboard Architektur (Streamlit-Version)

## Überblick

Diese Dokumentation beschreibt die Architektur der Streamlit-basierten Version des IoT-Dashboards. Die Lösung verwendet:

- **Frontend und Backend**: Streamlit (Python)
- **Datenverarbeitung**: Pandas und NumPy
- **Visualisierung**: Plotly Express und Plotly Graph Objects
- **Datenbank**: SQLite (lokal)
- **Containerisierung**: Docker (optional)

## Komponenten

### 1. Datenverarbeitung

- **CSV-Import**: Einlesen und Vorverarbeitung der CSV-Daten
- **Datenfilterung**: Filterung nach Zeiträumen und Ausreißerbehandlung
- **Aggregationen**: Berechnung von Zusammenfassungen und statistischen Kennzahlen

### 2. Visualisierungskomponenten

- **Zeitreihendiagramme**: Darstellung von Sensordaten über Zeit
- **Aggregationsdiagramme**: Balkendiagramme für aggregierte Werte
- **Heatmaps**: Visualisierung von Datendichte und Anomalien

### 3. Benutzeroberfläche

- **CSV-Upload**: Upload von Daten über die Streamlit-Oberfläche
- **Filter und Parameter**: Interaktive Kontrollelemente für Datenfilterung
- **Tabellarische Darstellung**: Darstellung der Rohdaten und berechneten Werte
- **Export-Funktionen**: PDF-Export und CSV-Download

### 4. Datenpersistenz

- **SQLite-Datenbank**: Lokale Speicherung von verarbeiteten Daten
- **Datei-Caching**: Zwischenspeicherung von Zwischenergebnissen für bessere Performance

## Datenfluss

1. **Datenaufnahme**: Upload von CSV-Dateien oder Laden aus der Datenbank
2. **Vorverarbeitung**: Bereinigung, Normalisierung und Erkennung von Ausreißern
3. **Analyse**: Berechnung von statistischen Kennzahlen und Aggregationen
4. **Visualisierung**: Darstellung der Daten in interaktiven Grafiken
5. **Persistenz**: Optional: Speicherung der Daten in der SQLite-Datenbank

## Verzeichnisstruktur

```
iot-dashboard-streamlit/
├── app.py                    # Hauptanwendungsdatei
├── pages/                    # Zusätzliche Seiten der Anwendung
│   ├── setup.py              # Setup-Seite
│   ├── view.py               # Ansicht-Seite
│   └── export.py             # Export-Seite
├── modules/                  # Funktionsmodule
│   ├── data_processing.py    # Datenverarbeitungsfunktionen
│   ├── visualization.py      # Visualisierungsfunktionen
│   └── db.py                 # Datenbankfunktionen
├── assets/                   # Statische Assets
│   ├── styles.css            # CSS-Stile
│   └── logo.png              # Logo
├── data/                     # Datenspeicherung
│   └── database.sqlite       # SQLite-Datenbank
├── .streamlit/               # Streamlit-Konfiguration
│   └── config.toml           # Konfigurationsdatei
├── requirements.txt          # Python-Abhängigkeiten
├── Dockerfile                # Docker-Definition (optional)
└── docker-compose.yml        # Docker-Compose-Konfiguration (optional)
```

## Technologiestack

- **Python 3.9+**: Programmiersprache
- **Streamlit 1.20+**: Web-Framework für Datenanalyse
- **Pandas 1.5+**: Datenmanipulation und -analyse
- **Plotly 5.10+**: Interaktive Visualisierungen
- **SQLite 3**: Leichtgewichtige Datenbank
- **Docker (optional)**: Containerisierung für einfache Bereitstellung

## Vorteile der neuen Architektur

1. **Einfachere Entwicklung**: Weniger Codezeilen, schnellere Iteration
2. **Bessere Wartbarkeit**: Einheitliche Codebase in Python
3. **Verbesserte Benutzererfahrung**: Interaktive Visualisierungen und schnellere Ladezeiten
4. **Reduzierte Komplexität**: Kein separates Frontend/Backend, keine Mikro-Services
5. **Einfachere Bereitstellung**: Weniger Konfiguration und Abhängigkeiten 