"""
IoT-Anlagen Dashboard (Streamlit-Version)
Hauptanwendungsdatei
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import io
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

# Middleware für iframe-Unterstützung importieren
import middleware

# Module importieren
from modules.data_processing import (
    parse_csv_data, 
    filter_by_time_range, 
    calculate_aggregates, 
    identify_outliers, 
    correct_outliers,
    calculate_pump_runtime,
    calculate_flow_with_time
)
from modules.visualization import (
    create_time_series_plot, 
    create_bar_chart, 
    create_heatmap,
    create_dashboard
)

# Titel und Konfiguration der App
st.set_page_config(
    page_title="IoT-Anlagen Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL-Parameter für Thingsboard-Integration auslesen
def get_url_params():
    """
    Liest URL-Parameter aus der Streamlit-Query aus, die für die Integration mit Thingsboard verwendet werden können
    Returns:
        dict: Dictionary mit URL-Parametern
    """
    params = {}
    
    # Query-Parameter auslesen
    query_params = st.query_params.to_dict()
    
    # Spezielle Parameter prüfen
    params["embed"] = query_params.get("embed", "false") == "true"
    params["device_id"] = query_params.get("deviceId", None)
    params["template"] = query_params.get("template", None)
    
    return params

# URL-Parameter auslesen
url_params = get_url_params()

# Automatisch Template laden, wenn in URL-Parametern angegeben
if url_params.get("template"):
    template_name = url_params.get("template")
    template_path = os.path.join('data/templates', f"{template_name}.json")
    if os.path.exists(template_path):
        loaded_data = load_template(template_path)
        if isinstance(loaded_data, dict):
            if "thresholds" in loaded_data:
                st.session_state.thresholds = loaded_data["thresholds"]
            if "pump_variables" in loaded_data:
                st.session_state.pump_variables = loaded_data["pump_variables"]

# Funktion zum Speichern eines Templates
def save_template(template_name: str, template_data: Dict):
    """
    Speichert die aktuellen Einstellungen als Template
    
    Args:
        template_name: Name des Templates
        template_data: Daten des Templates (Grenzwerte)
    """
    # Stellen Sie sicher, dass der data-Ordner existiert
    os.makedirs('data/templates', exist_ok=True)
    
    # Template-Datei erstellen
    template_path = os.path.join('data/templates', f"{template_name}.json")
    
    # Template speichern
    with open(template_path, 'w') as f:
        json.dump(template_data, f)
    
    return template_path

# Funktion zum Laden eines Templates
def load_template(template_path: str) -> Dict:
    """
    Lädt ein Template aus einer Datei
    
    Args:
        template_path: Pfad zur Template-Datei
        
    Returns:
        Geladene Template-Daten
    """
    if not os.path.exists(template_path):
        return {}
    
    with open(template_path, 'r') as f:
        template_data = json.load(f)
    
    return template_data

# Seitentitel
st.title("IoT-Anlagen Dashboard")
st.markdown("Analyse und Visualisierung von IoT-Sensor-Daten")

# Initialisiere Session State
if 'data' not in st.session_state:
    st.session_state.data = None
if 'aggregates' not in st.session_state:
    st.session_state.aggregates = None
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = None
if 'time_range' not in st.session_state:
    st.session_state.time_range = 'week'
if 'selected_variables' not in st.session_state:
    st.session_state.selected_variables = []
if 'custom_start_date' not in st.session_state:
    st.session_state.custom_start_date = None
if 'custom_end_date' not in st.session_state:
    st.session_state.custom_end_date = None
if 'thresholds' not in st.session_state:
    st.session_state.thresholds = {}
if 'available_templates' not in st.session_state:
    st.session_state.available_templates = []
if 'pump_variables' not in st.session_state:
    st.session_state.pump_variables = []
if 'pump_runtimes' not in st.session_state:
    st.session_state.pump_runtimes = {}
if 'auto_detect_pumps' not in st.session_state:
    st.session_state.auto_detect_pumps = True

# Sidebar für Datenupload und Filter
with st.sidebar:
    # Wenn im Embed-Modus, zeige einen Hinweis an
    if url_params.get("embed"):
        st.info("Dashboard im Embed-Modus")
        if url_params.get("device_id"):
            st.success(f"Gerät: {url_params.get('device_id')}")
        st.markdown("---")
    
    st.header("Daten und Filter")
    
    # CSV-Upload
    uploaded_file = st.file_uploader("CSV-Datei hochladen", type="csv")
    
    if uploaded_file is not None:
        # Versuche, die Datei zu lesen
        try:
            st.session_state.data = parse_csv_data(uploaded_file)
            st.success(f"Datei erfolgreich geladen: {uploaded_file.name}")
            
            # Berechne Aggregate
            st.session_state.aggregates = calculate_aggregates(st.session_state.data)
            
            # Filtere nach Zeitraum
            st.session_state.filtered_data = filter_by_time_range(
                st.session_state.data, 
                st.session_state.time_range,
                st.session_state.custom_start_date,
                st.session_state.custom_end_date
            )
            
            # Standardmäßig die ersten 4 numerischen Variablen auswählen
            numeric_cols = st.session_state.data.select_dtypes(include=['number']).columns.tolist()
            st.session_state.selected_variables = numeric_cols[:min(4, len(numeric_cols))]
            
            # Berechne Pumpenlaufzeiten, wenn Pumpenvariablen ausgewählt sind
            if st.session_state.pump_variables and st.session_state.filtered_data is not None:
                st.session_state.pump_runtimes = calculate_pump_runtime(
                    st.session_state.filtered_data,
                    st.session_state.pump_variables
                )
                
                # Aktualisiere die Aggregate mit den Pumpenlaufzeiten
                st.session_state.aggregates = calculate_aggregates(
                    st.session_state.filtered_data,
                    st.session_state.pump_runtimes
                )
            
        except Exception as e:
            st.error(f"Fehler beim Laden der Datei: {e}")
    
    # Zeitraum auswählen
    st.subheader("Zeitraum")
    time_range = st.radio(
        "Zeitraum auswählen:",
        ["Tag", "Woche", "Benutzerdefiniert"],
        index=1
    )
    
    # Zuordnung von Auswahltext zu internem Wert
    time_range_map = {"Tag": "day", "Woche": "week", "Benutzerdefiniert": "custom"}
    st.session_state.time_range = time_range_map[time_range]
    
    # Benutzerdefinierter Zeitraum
    if st.session_state.time_range == "custom":
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Von:", 
                value=datetime.now() - timedelta(days=7),
                max_value=datetime.now())
        
        with col2:
            end_date = st.date_input("Bis:",
                value=datetime.now(),
                max_value=datetime.now(),
                min_value=start_date)
        
        st.session_state.custom_start_date = start_date.strftime("%Y-%m-%d")
        st.session_state.custom_end_date = end_date.strftime("%Y-%m-%d")
    
    # Aktualisiere die gefilterten Daten, wenn die Daten und der Zeitraum verfügbar sind
    if st.session_state.data is not None:
        st.session_state.filtered_data = filter_by_time_range(
            st.session_state.data, 
            st.session_state.time_range,
            st.session_state.custom_start_date,
            st.session_state.custom_end_date
        )
    
    # Variablenauswahl
    if st.session_state.data is not None:
        st.subheader("Variablen")
        
        numeric_cols = st.session_state.data.select_dtypes(include=['number']).columns.tolist()
        
        st.session_state.selected_variables = st.multiselect(
            "Variablen auswählen:",
            numeric_cols,
            default=st.session_state.selected_variables
        )
        
        # Neue Sektion für Pumpen-Variablen
        st.subheader("Pumpen-Konfiguration")
        
        # Automatische Pumpenerkennung
        auto_detect = st.checkbox("Pumpen automatisch erkennen", value=st.session_state.auto_detect_pumps)
        st.session_state.auto_detect_pumps = auto_detect
        
        # Automatische Erkennung von Pumpenvariablen
        auto_detected_pumps = []
        if st.session_state.auto_detect_pumps:
            for col in st.session_state.data.columns:
                if "Pump_" in col or "Pump" in col and "_" in col:
                    auto_detected_pumps.append(col)
                    
            if auto_detected_pumps:
                st.success(f"Pumpen erkannt: {', '.join(auto_detected_pumps)}")
                
                # Information zu den Pumpen anzeigen
                pump_info = {
                    "Pump_58": "Pumpe 1 (Gerät 0058)",
                    "Pump_59": "Pumpe 2 (Gerät 0059)"
                }
                
                for pump in auto_detected_pumps:
                    if pump in pump_info:
                        st.info(f"{pump}: {pump_info[pump]}")
        
        st.info("Wählen Sie die Variablen aus, die den Status der Pumpen repräsentieren. Die Laufzeiten werden automatisch in Stunden berechnet.")
        
        # Erweitere die Liste der möglichen Pumpenvariablen um alle Spalten, die Boolean-Werte oder numerische Werte enthalten könnten
        pump_cols = numeric_cols.copy()
        
        # Füge auch boolean-Spalten hinzu (für true/false Pumpenwerte)
        boolean_cols = st.session_state.data.select_dtypes(include=['bool']).columns.tolist()
        for col in boolean_cols:
            if col not in pump_cols:
                pump_cols.append(col)
        
        # Füge auch Spalten mit "Pump" im Namen hinzu, falls sie noch nicht enthalten sind
        for col in st.session_state.data.columns:
            if "Pump" in col and col not in pump_cols:
                pump_cols.append(col)
        
        # Wenn auto-detect aktiv ist, setze die erkannten Pumpen als Standardauswahl
        default_pumps = auto_detected_pumps if st.session_state.auto_detect_pumps and auto_detected_pumps else st.session_state.pump_variables
        
        st.session_state.pump_variables = st.multiselect(
            "Pumpenvariablen auswählen:",
            pump_cols,
            default=default_pumps
        )
        
        # Berechne Pumpenlaufzeiten, wenn Pumpenvariablen ausgewählt sind
        if st.session_state.pump_variables and st.session_state.filtered_data is not None:
            st.session_state.pump_runtimes = calculate_pump_runtime(
                st.session_state.filtered_data,
                st.session_state.pump_variables
            )
            
            # Aktualisiere die Aggregate mit den Pumpenlaufzeiten
            st.session_state.aggregates = calculate_aggregates(
                st.session_state.filtered_data,
                st.session_state.pump_runtimes
            )
        
        # Neuer Abschnitt für Grenzwerte
        st.subheader("Grenzwerte & Vorlagen")
        
        # Template-Verwaltung
        os.makedirs('data/templates', exist_ok=True)
        template_files = [f for f in os.listdir('data/templates') if f.endswith('.json')]
        st.session_state.available_templates = template_files
        
        template_action = st.radio(
            "Template-Verwaltung:",
            ["Neues Template erstellen", "Template laden"],
            index=0
        )
        
        if template_action == "Neues Template erstellen":
            template_name = st.text_input("Name des Templates", value="Mein-Template")
            
            save_clicked = st.button("Template speichern")
            if save_clicked:
                if template_name:
                    # Erweiterung des Template-Daten-Formats um Pumpenvariablen
                    template_data = {
                        "thresholds": st.session_state.thresholds,
                        "pump_variables": st.session_state.pump_variables
                    }
                    save_path = save_template(template_name, template_data)
                    st.success(f"Template gespeichert: {save_path}")
                    # Template-Liste aktualisieren
                    template_files = [f for f in os.listdir('data/templates') if f.endswith('.json')]
                    st.session_state.available_templates = template_files
                else:
                    st.warning("Bitte geben Sie einen Namen für das Template an.")
        else:
            if st.session_state.available_templates:
                selected_template = st.selectbox(
                    "Template auswählen:",
                    st.session_state.available_templates
                )
                
                load_clicked = st.button("Template laden")
                if load_clicked:
                    template_path = os.path.join('data/templates', selected_template)
                    loaded_data = load_template(template_path)
                    
                    # Lade Grenzwerte und Pumpenvariablen aus dem Template
                    if isinstance(loaded_data, dict):
                        if "thresholds" in loaded_data:
                            st.session_state.thresholds = loaded_data["thresholds"]
                        if "pump_variables" in loaded_data:
                            st.session_state.pump_variables = loaded_data["pump_variables"]
                        st.success(f"Template geladen: {selected_template}")
                    else:
                        # Für Abwärtskompatibilität mit älteren Templates
                        st.session_state.thresholds = loaded_data
                        st.success(f"Template geladen (nur Grenzwerte): {selected_template}")
            else:
                st.info("Keine Templates verfügbar. Erstellen Sie zuerst ein Template.")
        
        # Grenzwerte für ausgewählte Variablen
        if st.session_state.selected_variables:
            st.subheader("Maximalwerte definieren")
            st.info("Definieren Sie Maximalwerte für die ausgewählten Variablen. Werte, die diese Grenzen überschreiten, werden in den Visualisierungen hervorgehoben.")
            
            # Für jede ausgewählte Variable einen Slider anzeigen
            for var in st.session_state.selected_variables:
                if var in st.session_state.data.columns:
                    # Maximal- und Minimalwerte für die Variable berechnen
                    min_val = float(st.session_state.data[var].min())
                    max_val = float(st.session_state.data[var].max())
                    
                    # Aktuellen Grenzwert aus dem Session State holen oder Standardwert verwenden
                    current_threshold = st.session_state.thresholds.get(var, max_val * 0.8)
                    
                    # Slider für den Grenzwert anzeigen
                    threshold = st.slider(
                        f"Maximalwert für {var}:",
                        min_value=min_val,
                        max_value=max_val,
                        value=float(current_threshold),
                        step=(max_val - min_val) / 100,
                        format="%.2f"
                    )
                    
                    # Grenzwert im Session State speichern
                    st.session_state.thresholds[var] = threshold

# Hauptbereich für Visualisierungen
if st.session_state.data is not None and st.session_state.filtered_data is not None:
    # Tabs für verschiedene Ansichten
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Detailansicht", "Datenanalyse", "Pumpen-Übersicht", "Flow-Berechnungen"])
    
    with tab1:
        st.header("Dashboard-Übersicht")
        
        # Dashboard mit Telemetriedaten und Gesamtmengen
        primary_vars = [var for var in st.session_state.selected_variables if var not in ['Flow_Rate_2', 'ARA_Flow']]
        flow_vars = [var for var in ['Flow_Rate_2', 'ARA_Flow'] if var in st.session_state.selected_variables]
        
        if primary_vars or flow_vars:
            dashboard_fig = create_dashboard(
                st.session_state.filtered_data,
                primary_vars,
                flow_vars,
                title="IoT-Anlagen Dashboard",
                time_range=st.session_state.time_range,
                thresholds=st.session_state.thresholds  # Grenzwerte übergeben
            )
            
            st.plotly_chart(dashboard_fig, use_container_width=True)
        else:
            st.warning("Bitte wählen Sie mindestens eine Variable für die Visualisierung aus.")
        
        # Wöchentliche Zusammenfassung als Metriken anzeigen
        if st.session_state.aggregates and "weeklyAggregates" in st.session_state.aggregates:
            st.subheader("Wöchentliche Zusammenfassung")
            
            metrics = st.session_state.aggregates["weeklyAggregates"]
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Verwende den aktuellen Wert aus den Pumpenlaufzeiten, wenn verfügbar
                if 'pump_runtimes' in st.session_state and st.session_state.pump_runtimes:
                    pump_duration = st.session_state.pump_runtimes.get("total_runtime", 0)
                else:
                    pump_duration = metrics.get('pumpDuration', 0)
                st.metric("Pumpdauer", f"{pump_duration:.1f} Stunden")
            
            with col2:
                # Gesamtmenge der ARA mit detaillierterer Anzeige
                ara_flow = metrics.get('totalFlowARA', 0)
                st.metric("Gesamtmenge ARA", f"{ara_flow:.2f} m³", help="Gesamtmenge aus ARA_Flow")
            
            with col3:
                # Gesamtmenge der Geräte 58 und 59 kombiniert
                combined_flow = metrics.get('totalFlow5859', 0)
                st.metric("Gesamtmenge Geräte 58+59", f"{combined_flow:.2f} m³", help="Kombinierte Gesamtmenge aller Geräte 58 und 59 Flows")
                
            # Zweite Reihe von Metriken für zusätzliche Flow-Daten, falls vorhanden
            if 'totalFlow58' in metrics or 'totalFlow59' in metrics or 'totalFlowGalgenkanal' in metrics:
                col4, col5, col6 = st.columns(3)
                
                with col4:
                    if 'totalFlow58' in metrics:
                        st.metric("Gerät 0058 Gesamt", f"{metrics['totalFlow58']:.2f} m³", help="Gesamtmenge aus Flow_58")
                
                with col5:
                    if 'totalFlow59' in metrics:
                        st.metric("Gerät 0059 (Flow_59)", f"{metrics['totalFlow59']:.2f} m³", help="Gesamtmenge aus Flow_59")
                        
                with col6:
                    if 'totalFlowGalgenkanal' in metrics:
                        st.metric("Gerät 0059 (Rate)", f"{metrics.get('totalFlowGalgenkanal', 0):.2f} m³", help="Gesamtmenge aus Flow_Rate_59")
    
    with tab2:
        st.header("Detailansicht")
        
        # Detaillierte Zeitreihenanalyse
        st.subheader("Zeitreihenanalyse")
        
        if st.session_state.selected_variables:
            time_series_fig = create_time_series_plot(
                st.session_state.filtered_data,
                st.session_state.selected_variables,
                title=f"Zeitreihenanalyse ({time_range})",
                height=500,
                thresholds=st.session_state.thresholds  # Grenzwerte übergeben
            )
            
            st.plotly_chart(time_series_fig, use_container_width=True)
        else:
            st.warning("Bitte wählen Sie mindestens eine Variable für die Visualisierung aus.")
        
        # Heatmap für ausgewählte Variable
        st.subheader("Tageszeit-Analyse")
        
        if st.session_state.selected_variables:
            selected_var_for_heatmap = st.selectbox(
                "Variable für Heatmap auswählen:",
                st.session_state.selected_variables
            )
            
            heatmap_fig = create_heatmap(
                st.session_state.filtered_data,
                selected_var_for_heatmap,
                title=f"Tageszeitliche Verteilung: {selected_var_for_heatmap}",
                height=500,
                thresholds=st.session_state.thresholds
            )
            
            st.plotly_chart(heatmap_fig, use_container_width=True)
    
    with tab3:
        st.header("Datenanalyse")
        
        # Ausreißererkennung
        st.subheader("Ausreißererkennung")
        
        if st.session_state.selected_variables:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_var_for_outliers = st.selectbox(
                    "Variable für Ausreißererkennung:",
                    st.session_state.selected_variables
                )
            
            with col2:
                outlier_method = st.radio(
                    "Methode:",
                    ["IQR", "Z-Score"],
                    index=0,
                    horizontal=True
                )
                
                # Zuordnung von Auswahltext zu internem Wert
                method_map = {"IQR": "iqr", "Z-Score": "zscore"}
                outlier_method = method_map[outlier_method]
            
            if st.button("Ausreißer erkennen"):
                outlier_indices = identify_outliers(
                    st.session_state.filtered_data,
                    selected_var_for_outliers,
                    method=outlier_method
                )
                
                if outlier_indices:
                    st.warning(f"{len(outlier_indices)} Ausreißer in '{selected_var_for_outliers}' erkannt.")
                    
                    # Zeige Ausreißer im Diagramm
                    fig = go.Figure()
                    
                    # Alle Datenpunkte
                    fig.add_trace(
                        go.Scatter(
                            x=st.session_state.filtered_data['Time'],
                            y=st.session_state.filtered_data[selected_var_for_outliers],
                            mode='lines+markers',
                            name=selected_var_for_outliers,
                            line=dict(color='blue', width=1),
                            marker=dict(size=5, color='blue'),
                        )
                    )
                    
                    # Ausreißer hervorheben
                    outliers = st.session_state.filtered_data.loc[outlier_indices]
                    fig.add_trace(
                        go.Scatter(
                            x=outliers['Time'],
                            y=outliers[selected_var_for_outliers],
                            mode='markers',
                            name='Ausreißer',
                            marker=dict(size=10, color='red', symbol='x'),
                        )
                    )
                    
                    fig.update_layout(
                        title=f"Ausreißer in '{selected_var_for_outliers}'",
                        xaxis_title="Zeit",
                        yaxis_title="Wert",
                        height=500,
                        template="plotly_white"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Option zum Korrigieren der Ausreißer
                    if st.button("Ausreißer korrigieren"):
                        correction_method = st.radio(
                            "Korrekturmethode:",
                            ["Mittelwert", "Median", "Nächster Nachbar", "Entfernen"],
                            index=0,
                            horizontal=True
                        )
                        
                        # Zuordnung von Auswahltext zu internem Wert
                        method_map = {
                            "Mittelwert": "mean", 
                            "Median": "median", 
                            "Nächster Nachbar": "nearest", 
                            "Entfernen": "remove"
                        }
                        correction_method = method_map[correction_method]
                        
                        # Ausreißer korrigieren
                        corrected_data = correct_outliers(
                            st.session_state.filtered_data,
                            selected_var_for_outliers,
                            outlier_indices,
                            method=correction_method
                        )
                        
                        # Aktualisiere die Daten
                        st.session_state.filtered_data = corrected_data
                        
                        st.success(f"{len(outlier_indices)} Ausreißer in '{selected_var_for_outliers}' korrigiert.")
                else:
                    st.success(f"Keine Ausreißer in '{selected_var_for_outliers}' erkannt.")
        
        # Rohdaten anzeigen
        st.subheader("Rohdaten")
        
        if st.checkbox("Rohdaten anzeigen"):
            st.dataframe(st.session_state.filtered_data, use_container_width=True)
            
            # Daten herunterladen
            csv_data = st.session_state.filtered_data.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="CSV herunterladen",
                data=csv_data,
                file_name="iot_data_filtered.csv",
                mime="text/csv"
            )
    
    # Neuer Tab für Pumpen-Übersicht
    with tab4:
        st.header("Pumpen-Laufzeiten")
        
        if st.session_state.pump_variables:
            # Laufzeiten anzeigen
            st.subheader("Laufzeiten im ausgewählten Zeitraum")
            
            # Laufzeiten berechnen, falls noch nicht erfolgt
            if not st.session_state.pump_runtimes:
                st.session_state.pump_runtimes = calculate_pump_runtime(
                    st.session_state.filtered_data,
                    st.session_state.pump_variables
                )
            
            # Metriken für einzelne Pumpen
            st.subheader("Laufzeiten der einzelnen Pumpen")
            
            # Pumpen-Labels mit nützlichen Informationen anreichern
            pump_display_names = {}
            for pump_var in st.session_state.pump_variables:
                if pump_var == "Pump_58":
                    pump_display_names[pump_var] = "Pumpe 1 (Gerät 0058)"
                elif pump_var == "Pump_59":
                    pump_display_names[pump_var] = "Pumpe 2 (Gerät 0059)"
                else:
                    pump_display_names[pump_var] = pump_var
            
            # Anzahl der Pumpen bestimmen, um passende Anzahl von Spalten zu erstellen
            num_pumps = len(st.session_state.pump_variables)
            cols = st.columns(min(num_pumps, 3))  # Maximal 3 Spalten
            
            # Für jede Pumpe eine Metrik anzeigen
            for i, pump_var in enumerate(st.session_state.pump_variables):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    runtime_hours = st.session_state.pump_runtimes.get(pump_var, 0)
                    display_name = pump_display_names.get(pump_var, pump_var)
                    st.metric(f"{display_name}", f"{runtime_hours:.2f} Stunden")
            
            # Gesamtlaufzeit aller Pumpen
            st.subheader("Gesamtlaufzeit")
            total_runtime = st.session_state.pump_runtimes.get("total_runtime", 0)
            st.metric("Gesamtlaufzeit aller Pumpen", f"{total_runtime:.2f} Stunden")
            
            # Balkendiagramm der Laufzeiten
            st.subheader("Laufzeiten-Vergleich")
            
            # Daten für das Balkendiagramm vorbereiten
            pump_labels = [pump_display_names.get(var, var) for var in st.session_state.pump_variables]
            pump_values = [st.session_state.pump_runtimes.get(var, 0) for var in st.session_state.pump_variables]
            
            # Balkendiagramm erstellen
            fig = go.Figure(data=[
                go.Bar(
                    x=pump_labels,
                    y=pump_values,
                    text=[f"{val:.2f} h" for val in pump_values],
                    textposition='auto',
                    marker_color='royalblue'
                )
            ])
            
            fig.update_layout(
                title="Laufzeiten der Pumpen im Vergleich",
                xaxis_title="Pumpe",
                yaxis_title="Laufzeit (Stunden)",
                height=400,
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Zeitlicher Verlauf der Pumpenaktivitäten (nur wenn binäre 0/1-Daten)
            if st.session_state.filtered_data is not None:
                st.subheader("Zeitlicher Verlauf der Pumpenaktivitäten")
                
                # Zeitreihen-Diagramm für die Pumpenaktivitäten
                time_series_fig = create_time_series_plot(
                    st.session_state.filtered_data,
                    st.session_state.pump_variables,
                    title=f"Pumpenaktivitäten im Zeitverlauf ({time_range})",
                    height=500
                )
                
                st.plotly_chart(time_series_fig, use_container_width=True)
        else:
            st.info("Bitte wählen Sie in der Sidebar die Variablen aus, die die Pumpen repräsentieren.")
            
            # Beispiel anzeigen, wie Pumpendaten aussehen könnten
            st.subheader("Beispiel für Pumpendaten")
            st.markdown("""
            Pumpendaten sind typischerweise:
            - Binäre Signale (0 = aus, 1 = an)
            - Dauer- oder Statusvariablen der Pumpen
            - Variablen mit "Pump", "P" oder ähnlichen Bezeichnungen
            
            Wählen Sie diese in der Sidebar unter "Pumpen-Konfiguration" aus.
            """)

    # Neuer Tab für Flow-Berechnungen
    with tab5:
        st.header("Flow-Berechnungen")
        
        # Identifiziere alle Flow-bezogenen Spalten
        flow_cols = [col for col in st.session_state.data.columns if 'Flow' in col or 'flow' in col]
        
        if flow_cols:
            # Zeige eine Info über die erkannten Flow-Spalten an
            st.info(f"Erkannte Flow-Spalten: {', '.join(flow_cols)}")
            
            # Berechne Gesamtmengen für jeden Flow
            flow_totals = {}
            for col in flow_cols:
                # Verwende die verbesserte Berechnungsmethode mit Zeitberücksichtigung
                flow_totals[col] = calculate_flow_with_time(st.session_state.filtered_data, col)
            
            # Zeige Gesamtmengen als Metriken an
            st.subheader("Gesamtmengen im ausgewählten Zeitraum")
            
            # Flow-Spalten mit spezifischen Namen (z.B. für die Geräte 58 und 59)
            device_flows = {
                "Flow_Rate_59": "Gerät 0059 (Rate)",
                "ARA_Flow": "Gesamtmenge ARA",
                "Flow_58": "Gerät 0058",
                "Flow_59": "Gerät 0059 (Flow)"
            }
            
            # Berechne die kombinierte Gesamtmenge aus den Flow_58, Flow_59 und Flow_Rate_59
            combined_flow = 0
            for col in flow_cols:
                if 'Flow_58' in col or 'Flow_59' in col or 'Flow_Rate_59' in col:
                    combined_flow += flow_totals.get(col, 0)
            
            # Zeige die kombinierte Gesamtmenge zuerst an
            st.info(f"Kombinierte Gesamtmenge Geräte 58+59: {combined_flow:.2f} m³")
            
            # Erstelle zwei Spalten für die Metriken
            cols = st.columns(len(flow_cols))
            
            # Zeige die Metriken für jede Flow-Spalte
            for i, col in enumerate(flow_cols):
                with cols[i]:
                    # Verwende den angepassten Namen, falls vorhanden
                    display_name = device_flows.get(col, f"Gesamtmenge {col}")
                    st.metric(display_name, f"{flow_totals[col]:.2f} m³")
            
            # Visualisierung der Flow-Daten
            st.subheader("Flow-Visualisierung")
            
            # Zeitreihen-Diagramm für die Flow-Werte
            flow_fig = create_time_series_plot(
                st.session_state.filtered_data,
                flow_cols,
                title=f"Flow-Werte im Zeitverlauf ({st.session_state.time_range})",
                height=500
            )
            
            st.plotly_chart(flow_fig, use_container_width=True)
            
            # Balkendiagramm für die Gesamtmengen
            flow_labels = [device_flows.get(col, col) for col in flow_cols]
            flow_values = [flow_totals[col] for col in flow_cols]
            
            # Füge die kombinierte Gesamtmenge zum Balkendiagramm hinzu
            flow_labels.append("Geräte 58+59 Kombiniert")
            flow_values.append(combined_flow)
            
            # Balkendiagramm erstellen
            bar_fig = go.Figure(data=[
                go.Bar(
                    x=flow_labels,
                    y=flow_values,
                    text=[f"{val:.2f} m³" for val in flow_values],
                    textposition='auto',
                    marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(flow_labels)]
                )
            ])
            
            bar_fig.update_layout(
                title="Gesamtmengen der Flow-Werte im Vergleich",
                xaxis_title="Flow-Variable",
                yaxis_title="Gesamtmenge (m³)",
                height=400,
                template="plotly_white"
            )
            
            st.plotly_chart(bar_fig, use_container_width=True)
            
            # Tägliche Statistiken
            st.subheader("Tägliche Flow-Statistiken")
            
            # Tägliche Aggregate berechnen mit verbesserter Methode
            # Gruppieren nach Datum
            unique_dates = st.session_state.filtered_data['Time'].dt.date.unique()
            daily_sums = pd.DataFrame({'Date': unique_dates})
            
            # Für jedes Datum und jede Flow-Spalte die verbesserte Berechnungsmethode anwenden
            for col in flow_cols:
                daily_values = []
                
                for date in unique_dates:
                    # Daten für den aktuellen Tag filtern
                    day_data = st.session_state.filtered_data[st.session_state.filtered_data['Time'].dt.date == date]
                    # Verbesserte Berechnungsmethode anwenden
                    flow_value = calculate_flow_with_time(day_data, col)
                    daily_values.append(flow_value)
                
                # Werte zur DataFrame hinzufügen
                daily_sums[col] = daily_values
            
            # Tabelle mit täglichen Summen anzeigen
            st.dataframe(daily_sums, use_container_width=True)
            
            # Visualisierung der täglichen Summen
            st.subheader("Tägliche Flow-Mengen")
            
            # Für jede Flow-Variable ein Liniendiagramm erstellen
            daily_fig = go.Figure()
            
            for col in flow_cols:
                daily_fig.add_trace(
                    go.Scatter(
                        x=daily_sums['Date'],
                        y=daily_sums[col],
                        mode='lines+markers',
                        name=device_flows.get(col, col),
                        hovertemplate="%{y:.2f} m³<extra>%{x}</extra>"
                    )
                )
            
            daily_fig.update_layout(
                title="Tägliche Flow-Mengen",
                xaxis_title="Datum",
                yaxis_title="Menge (m³)",
                height=400,
                template="plotly_white",
                hovermode="x unified"
            )
            
            st.plotly_chart(daily_fig, use_container_width=True)
            
        else:
            st.warning("Keine Flow-bezogenen Spalten in den Daten gefunden.")

else:
    # Keine Daten vorhanden
    st.info("Bitte laden Sie eine CSV-Datei hoch, um mit der Analyse zu beginnen.")
    
    # Beispiel-Datei anzeigen
    if st.checkbox("Beispieldaten anzeigen"):
        # Beispiel-CSV-Daten generieren
        example_data = pd.DataFrame({
            'Time': pd.date_range(start='2023-01-01', periods=100, freq='H'),
            'PH_58': np.random.normal(7.5, 0.5, 100),
            'Trübung_Zulauf': np.random.normal(35, 10, 100),
            'Water_Level': np.random.normal(120, 15, 100),
            'Flow_Rate_2': np.random.normal(250, 50, 100),
            'ARA_Flow': np.random.normal(180, 40, 100),
            'Pump_1': np.random.randint(0, 2, 100),  # Beispiel für Pumpenstatus (0/1)
            'Pump_2': np.random.randint(0, 2, 100)   # Beispiel für Pumpenstatus (0/1)
        })
        
        st.dataframe(example_data.head(10), use_container_width=True)
        
        # Beispiel-Datei zum Download anbieten
        csv_example = example_data.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="Beispieldaten herunterladen",
            data=csv_example,
            file_name="iot_data_example.csv",
            mime="text/csv"
        )

# Fußzeile
st.markdown("---")
st.markdown("OWIPEX IoT-Anlagen Dashboard • Powered by Streamlit") 