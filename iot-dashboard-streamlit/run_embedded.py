#!/usr/bin/env python3
"""
Startet die Streamlit-App mit konfigurierter Middleware für iframe-Einbettung
"""

import os
import sys
import subprocess
import streamlit.web.bootstrap
import middleware

def run_streamlit_app():
    """
    Startet die Streamlit-App mit angepassten Parametern für die Einbettung
    """
    print("Starte Streamlit mit Middleware für iframe-Einbettung...")
    
    # Sicherstellen, dass Middleware geladen ist
    print("Middleware Status:", "Geladen" if "middleware" in sys.modules else "Nicht geladen")
    
    # App-Pfad ermitteln
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "app.py")
    
    # Streamlit-Kommando zusammenstellen
    args = [
        "streamlit", "run", 
        app_path,
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--server.allowIframeEmbedding=true"
    ]
    
    # Streamlit starten
    subprocess.run(args)

if __name__ == "__main__":
    run_streamlit_app() 