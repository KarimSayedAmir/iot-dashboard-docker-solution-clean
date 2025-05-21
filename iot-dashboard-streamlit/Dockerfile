FROM python:3.9-slim

WORKDIR /app

# Kopiere requirements.txt zuerst, um den Cache-Layer für die Abhängigkeiten effizient zu nutzen
COPY requirements.txt .

# Installiere Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den restlichen Code
COPY . .

# Port, auf dem Streamlit läuft
EXPOSE 8501

# Erstelle Verzeichnisse für Daten und Uploads
RUN mkdir -p data/templates
RUN mkdir -p uploads

# Berechtigungen setzen
RUN chmod -R 777 data
RUN chmod -R 777 uploads

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Streamlit-App starten
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"] 