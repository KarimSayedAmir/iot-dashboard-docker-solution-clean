# IoT-Dashboard Docker-Lösung - Dokumentation

## Übersicht

Diese Dokumentation beschreibt die Docker-basierte, selbstgehostete Lösung für das IoT-Dashboard. Die Lösung verwendet:

- **Frontend**: React mit TypeScript
- **Backend**: Express.js mit REST API
- **Datenbank**: SQLite (lokal im Container)
- **Containerisierung**: Docker und Docker Compose

Diese Architektur bietet folgende Vorteile:
- Keine externen Kosten (im Gegensatz zu Firebase)
- Einfache Bereitstellung auf einem Linux-Server
- Persistente Datenspeicherung für bis zu 1 Jahr
- Alle Funktionen des ursprünglichen Dashboards

## Systemanforderungen

- Linux-Server (z.B. Hetzner)
- Docker und Docker Compose installiert
- Mindestens 1GB freier Speicherplatz
- Port 8099 verfügbar für den Webzugriff

## Installation

### 1. Vorbereitung

Stellen Sie sicher, dass Docker und Docker Compose auf Ihrem Server installiert sind:

```bash
# Docker installieren (falls noch nicht vorhanden)
sudo apt update
sudo apt install -y docker.io docker-compose

# Docker-Dienst starten und aktivieren
sudo systemctl start docker
sudo systemctl enable docker

# Benutzer zur Docker-Gruppe hinzufügen (optional)
sudo usermod -aG docker $USER
```

### 2. Dashboard-Dateien auf den Server kopieren

Kopieren Sie das gesamte Dashboard-Verzeichnis auf Ihren Server:

```bash
# Beispiel mit scp
scp -r dashboard/ benutzer@server:/pfad/zum/zielverzeichnis/
```

### 3. Docker-Container starten

Navigieren Sie zum Dashboard-Verzeichnis und starten Sie die Container:

```bash
cd /pfad/zum/zielverzeichnis/dashboard
docker-compose up -d
```

Das Dashboard ist nun unter der IP-Adresse oder Domain Ihres Servers auf Port 8099 erreichbar (z.B. http://ihre-server-ip:8099).

## Architektur

### Container-Struktur

Die Lösung besteht aus zwei Docker-Containern:

1. **Frontend-Container**:
   - Nginx-Webserver mit React-Anwendung
   - Stellt die Benutzeroberfläche bereit
   - Leitet API-Anfragen an das Backend weiter

2. **Backend-Container**:
   - Express.js-Server mit REST API
   - SQLite-Datenbank für Datenpersistenz
   - Automatische Datenbereinigung (Daten älter als 1 Jahr)

### Datenmodell

Die SQLite-Datenbank enthält folgende Tabellen:

1. **weeks**: Speichert Metadaten zu jeder Woche
   - id: Eindeutige ID der Woche
   - start_date: Startdatum
   - end_date: Enddatum
   - data_type: Datentyp (Telemetrie, Gesamtmengen, beides)
   - created_at: Erstellungszeitstempel
   - last_modified: Letzter Änderungszeitstempel

2. **iot_data**: Speichert die IoT-Daten
   - id: Eindeutige ID des Datenpunkts
   - week_id: Referenz zur Woche
   - time: Zeitstempel des Datenpunkts
   - data: JSON-Daten des Datenpunkts

3. **manual_corrections**: Speichert manuelle Korrekturen
   - id: Eindeutige ID der Korrektur
   - week_id: Referenz zur Woche
   - pump_duration: Pumpdauer
   - total_flow_ara: Gesamtmenge ARA
   - total_flow_galgenkanal: Gesamtmenge Galgenkanal
   - notes: Notizen

## Datenpersistenz

Die Daten werden in einem Docker-Volume gespeichert, das auch bei Neustarts oder Updates der Container erhalten bleibt. Die SQLite-Datenbank befindet sich im Verzeichnis `/app/data` im Backend-Container.

## Wartung und Verwaltung

### Container-Status prüfen

```bash
docker-compose ps
```

### Logs anzeigen

```bash
# Alle Logs
docker-compose logs

# Nur Backend-Logs
docker-compose logs backend

# Nur Frontend-Logs
docker-compose logs frontend
```

### Container neu starten

```bash
docker-compose restart
```

### Aktualisierung der Anwendung

Um eine neue Version der Anwendung zu installieren:

```bash
# Stoppen Sie die Container
docker-compose down

# Ziehen Sie die neuesten Änderungen (falls Git verwendet wird)
git pull

# Bauen Sie die Container neu
docker-compose build

# Starten Sie die Container neu
docker-compose up -d
```

### Backup der Datenbank

Um ein Backup der SQLite-Datenbank zu erstellen:

```bash
# Kopieren Sie die Datenbank aus dem Container
docker cp dashboard_backend_1:/app/data/iot_dashboard.db ./backup_$(date +%Y%m%d).db
```

## Fehlerbehebung

### Problem: Dashboard ist nicht erreichbar

1. Prüfen Sie, ob die Container laufen:
   ```bash
   docker-compose ps
   ```

2. Prüfen Sie die Logs auf Fehler:
   ```bash
   docker-compose logs
   ```

3. Stellen Sie sicher, dass Port 80 nicht blockiert ist:
   ```bash
   sudo netstat -tulpn | grep 80
   ```

### Problem: Daten werden nicht gespeichert

1. Prüfen Sie die Backend-Logs:
   ```bash
   docker-compose logs backend
   ```

2. Stellen Sie sicher, dass das Datenbank-Volume korrekt eingebunden ist:
   ```bash
   docker volume ls
   docker volume inspect dashboard_db-data
   ```

## Sicherheitshinweise

Diese Implementierung enthält keine Benutzerauthentifizierung. Wenn Sie das Dashboard öffentlich zugänglich machen, sollten Sie zusätzliche Sicherheitsmaßnahmen wie einen Reverse-Proxy mit Passwortschutz oder eine VPN-Lösung in Betracht ziehen.

## Technische Details

### API-Endpunkte

Das Backend stellt folgende API-Endpunkte bereit:

- `GET /api/weeks`: Alle Wochen abrufen
- `GET /api/weeks/:id`: Spezifische Woche mit Daten abrufen
- `POST /api/weeks`: Neue Woche speichern
- `PUT /api/weeks/:id`: Woche aktualisieren
- `DELETE /api/weeks/:id`: Woche löschen
- `POST /api/weeks/:id/corrections`: Korrektur hinzufügen
- `PUT /api/weeks/:id/corrections/:correctionId`: Korrektur aktualisieren
- `DELETE /api/weeks/:id/corrections/:correctionId`: Korrektur löschen

### Netzwerkkonfiguration

Die Container kommunizieren über ein internes Docker-Netzwerk. Nur der Frontend-Container ist über Port 80 von außen erreichbar. Der Backend-Container ist nur über das interne Netzwerk zugänglich.

## Limitierungen

- Die Lösung ist für eine einzelne Instanz konzipiert und nicht für horizontale Skalierung ausgelegt
- SQLite ist für gleichzeitige Schreibzugriffe limitiert
- Keine integrierte Benutzerauthentifizierung

## Fazit

Diese Docker-basierte Lösung bietet alle Funktionen des ursprünglichen IoT-Dashboards, ohne externe Kosten zu verursachen. Die Daten werden lokal gespeichert und sind für bis zu einem Jahr verfügbar. Die Lösung ist einfach zu installieren und zu warten.
