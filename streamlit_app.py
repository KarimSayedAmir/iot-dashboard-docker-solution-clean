"""
IoT-Dashboard Streamlit App - Haupteinstiegspunkt für Streamlit Cloud
"""

import os
import sys

# Füge das Unterverzeichnis dem Python-Pfad hinzu
sys.path.append("iot-dashboard-streamlit")

# Importiere die Middleware für iframe-Unterstützung
try:
    import middleware
except ImportError:
    # Wenn die Middleware nicht gefunden wird, kopiere sie direkt
    middleware_code = """
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

# Ausgabe für Debugging
print("Middleware geladen: X-Frame-Options für iframe-Einbettung angepasst")
"""
    # Middleware-Datei im aktuellen Verzeichnis erstellen
    with open("middleware.py", "w") as f:
        f.write(middleware_code)
    
    import middleware

# Die App direkt aus dem Unterordner starten
import runpy
runpy.run_path("iot-dashboard-streamlit/app.py") 