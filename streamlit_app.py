"""
IoT-Dashboard Streamlit App - Haupteinstiegspunkt für Streamlit Cloud
"""

import os
import sys
import streamlit as st

# Konfigurationen für Thingsboard-Einbettung (anstelle der Middleware)
# Diese werden direkt in die config.toml eingetragen und sollten ausreichen

# Füge das Unterverzeichnis dem Python-Pfad hinzu
sys.path.append("iot-dashboard-streamlit")

# Setze URL-Parameter für die Einbettung
if "embed" not in st.query_params:
    st.query_params["embed"] = "true"

# Die App direkt aus dem Unterordner starten
# Wir nutzen eine einfachere Methode zum Importieren der Hauptapp

# Option 1: Import mit execfile-ähnlicher Funktion
def run_app_file(file_path):
    """Führt eine Python-Datei im aktuellen Kontext aus."""
    with open(file_path, 'r') as file:
        app_code = file.read()
    
    # Pfad zum Verzeichnis der App
    app_dir = os.path.dirname(os.path.abspath(file_path))
    original_dir = os.getcwd()
    
    try:
        # Wechsle ins App-Verzeichnis und führe den Code aus
        os.chdir(app_dir)
        exec(app_code, globals())
    finally:
        # Zurück zum ursprünglichen Verzeichnis
        os.chdir(original_dir)

# Starte die Hauptapp
app_path = os.path.join("iot-dashboard-streamlit", "app.py")
run_app_file(app_path) 