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