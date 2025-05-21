# Integration des IoT-Dashboards in Thingsboard

Diese Dokumentation beschreibt, wie das Streamlit-basierte IoT-Dashboard in Thingsboard eingebettet werden kann.

## Voraussetzungen

1. Eine laufende Streamlit-App (lokal oder auf Streamlit Cloud)
2. Zugriff auf Thingsboard mit Berechtigung zum Erstellen von Dashboards/Widgets

## Konfiguration der Streamlit-App

Die Streamlit-App wurde bereits konfiguriert, um die Einbettung in iframes zu erlauben. Die folgenden Anpassungen wurden vorgenommen:

### 1. Konfiguration in `.streamlit/config.toml`

```toml
[server]
enableCORS = false
enableXsrfProtection = false
allowIframeEmbedding = true

[ui]
hideTopBar = true
hideSidebarNav = true
```

### 2. Middleware für iframe-Header

Die Datei `middleware.py` wurde erstellt, um die X-Frame-Options-Header anzupassen und die Einbettung zu ermöglichen:

```python
from streamlit.web.server.server import Server, StaticFileHandler, _RetrieveStaticFile, StaticFileHandler, websocket_handler, TORNADO_SETTINGS
import streamlit as st
import tornado.web

# Original Methode speichern
original_handle = StaticFileHandler.set_default_headers

# Neue Methode definieren, um die frame-Header anzupassen
def set_default_headers_with_frame_options(self):
    original_handle(self)
    # X-Frame-Options-Header entfernen oder auf "ALLOWALL" setzen
    self.clear_header("X-Frame-Options")
    # Content Security Policy anpassen, um frame-src zu erlauben
    self.set_header("Content-Security-Policy", "frame-ancestors *;")

# Die Methode überschreiben
StaticFileHandler.set_default_headers = set_default_headers_with_frame_options
```

### 3. Import der Middleware in `app.py`

Die Middleware wird in der Hauptdatei `app.py` importiert:

```python
# Middleware für iframe-Unterstützung importieren
import middleware
```

## Einbettung in Thingsboard

### Schritt 1: HTML-Widget in Thingsboard erstellen

1. Melden Sie sich in Thingsboard an
2. Navigieren Sie zu Ihrem Dashboard
3. Klicken Sie auf "Bearbeiten" und dann auf "Widget hinzufügen"
4. Wählen Sie "Cards" → "HTML Card"
5. Konfigurieren Sie das Widget mit folgendem HTML-Code:

```html
<div style="width:100%; height:100%;">
    <iframe 
        src="https://your-streamlit-app-url.streamlit.app/?embed=true" 
        width="100%" 
        height="100%" 
        frameborder="0" 
        style="border:0;" 
        allowfullscreen>
    </iframe>
</div>
```

6. Ersetzen Sie `https://your-streamlit-app-url.streamlit.app/` durch die URL Ihrer Streamlit-App
7. Klicken Sie auf "Hinzufügen" und speichern Sie das Dashboard

### Schritt 2: Widget-Größe anpassen

1. Ziehen Sie das Widget auf die gewünschte Größe
2. Empfohlen: Nutzen Sie die volle Dashboard-Breite, um die App optimal anzuzeigen

### Schritt 3: Autorisierung (falls erforderlich)

Falls Ihre Streamlit-App eine Autorisierung erfordert, müssen Sie sicherstellen, dass:

1. Die Autorisierung im iframe funktioniert
2. Oder die App ist öffentlich zugänglich (empfohlen für Thingsboard-Integration)

## Fehlerbehebung

### Die App wird im iframe nicht angezeigt

- Überprüfen Sie die Streamlit-URL und stellen Sie sicher, dass `?embed=true` angehängt ist
- Stellen Sie sicher, dass die Middleware korrekt geladen wird
- Überprüfen Sie die Netzwerk-Konsole im Browser auf Fehler

### Scrolling-Probleme

Falls der Content nicht richtig scrollt, erweitern Sie den HTML-Code um:

```html
<div style="width:100%; height:100%; overflow: hidden;">
    <iframe 
        src="https://your-streamlit-app-url.streamlit.app/?embed=true" 
        width="100%" 
        height="100%" 
        frameborder="0" 
        style="border:0; overflow: auto;" 
        allowfullscreen>
    </iframe>
</div>
```

## Erweiterte Integration

Für eine erweiterte Integration können Sie die Streamlit-App mit Thingsboard über URL-Parameter kommunizieren lassen:

```
https://your-streamlit-app-url.streamlit.app/?embed=true&deviceId=YOUR_DEVICE_ID
```

Und in der Streamlit-App können Sie diese Parameter auslesen:

```python
import streamlit as st

# URL-Parameter auslesen
device_id = st.query_params.get("deviceId", None)
if device_id:
    st.write(f"Anzeige für Gerät: {device_id}")
``` 