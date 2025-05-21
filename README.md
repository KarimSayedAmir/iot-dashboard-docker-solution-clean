# IoT-Dashboard

Ein leistungsstarkes Dashboard zur Analyse und Visualisierung von IoT-Sensordaten, insbesondere für Pumpensysteme und Durchflussmessungen.

## Funktionen

- **Datenimport**: CSV-Upload mit Unterstützung für Metadaten-Header
- **Datenanalyse**: Zeitreihenanalyse, Ausreißererkennung und statistische Kennzahlen
- **Pumpenlaufzeiten**: Automatische Berechnung der Pumpenlaufzeiten in Stunden
- **Flow-Berechnungen**: Präzise Berechnung von Durchflussmengen mit Berücksichtigung der Zeitintervalle
- **Visualisierungen**: Interaktive Diagramme, Heatmaps und Dashboard-Ansichten
- **Template-System**: Speichern und Laden von benutzerdefinierten Einstellungen

## Installation

### Lokale Installation

1. Klonen Sie das Repository:
   ```
   git clone https://github.com/ihr-username/iot-dashboard.git
   cd iot-dashboard
   ```

2. Erstellen Sie eine virtuelle Umgebung und installieren Sie die Abhängigkeiten:
   ```
   python -m venv iot-env
   source iot-env/bin/activate  # Unter Windows: iot-env\Scripts\activate
   pip install -r iot-dashboard-streamlit/requirements.txt
   ```

3. Starten Sie die Anwendung:
   ```
   cd iot-dashboard-streamlit
   streamlit run app.py
   ```

4. Öffnen Sie Ihren Browser und navigieren Sie zu `http://localhost:8501`

## Verwendung

1. **Daten hochladen**: Laden Sie Ihre CSV-Datei über die Sidebar hoch
2. **Visualisierungen anzeigen**: Wechseln Sie zwischen den Tabs "Dashboard", "Detailansicht", "Datenanalyse", "Pumpen-Übersicht" und "Flow-Berechnungen"
3. **Filter anwenden**: Filtern Sie die Daten nach Zeitraum (Tag, Woche, benutzerdefiniert)
4. **Grenzwerte setzen**: Definieren Sie Maximalwerte für Ihre Variablen
5. **Templates speichern**: Speichern Sie Ihre Einstellungen für spätere Verwendung

## Typischer Workflow

1. CSV-Datei hochladen
2. Zeitraum und relevante Variablen in der Sidebar auswählen
3. Pumpenvariablen konfigurieren (automatisch oder manuell)
4. Dashboard und Detailansichten analysieren
5. Bei Bedarf Grenzwerte definieren und als Template speichern

## Projektstruktur

```
iot-dashboard-streamlit/
├── app.py                    # Hauptanwendungsdatei
├── modules/                  # Funktionsmodule
│   ├── data_processing.py    # Datenverarbeitungsfunktionen
│   └── visualization.py      # Visualisierungsfunktionen
├── data/                     # Datenspeicherung
│   └── templates/            # Gespeicherte Benutzereinstellungen
```

## Online-Bereitstellung

Für die Bereitstellung in einer Produktionsumgebung empfehlen wir:

1. **Streamlit Cloud**: 
   - Verbinden Sie Ihr GitHub-Repository mit https://streamlit.io/cloud
   - Vollständig kostenlos für öffentliche Apps
   - Automatische Bereitstellung bei jedem Push
   - Einfache Weitergabe über eine URL

2. **Heroku**:
   - Python-basierte Bereitstellung ohne Docker
   - Einfach zu konfigurieren mit einer Procfile-Datei
   - Automatische Skalierung bei Bedarf

3. **PythonAnywhere** oder **AWS Elastic Beanstalk**:
   - Alternative Optionen für längerfristiges Hosting

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe LICENSE-Datei für Details. 