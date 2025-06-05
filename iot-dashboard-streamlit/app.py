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

# Middleware für iframe-Unterstützung nicht mehr notwendig, da wir die Einstellungen in config.toml konfigurieren
# import middleware

# Module importieren
from modules.data_processing import (
    parse_csv_data, 
    filter_by_time_range, 
    calculate_aggregates, 
    identify_outliers, 
    correct_outliers,
    calculate_pump_runtime,
    calculate_flow_with_time,
    clean_dataset,
    remove_outliers,
    clean_flow_data
)
from modules.visualization import (
    create_time_series_plot, 
    create_bar_chart, 
    create_heatmap,
    create_dashboard
)
from modules.pdf_export import export_current_view

# Funktion zur Erstellung aller Visualisierungen mit bereinigten oder unbereinigten Daten
def update_all_visualizations(data, current_figures, selected_variables, time_range, thresholds, is_cleaned=False):
    """
    Aktualisiert alle Visualisierungen mit den angegebenen Daten.
    
    Args:
        data: DataFrame mit den zu verwendenden Daten
        current_figures: Dictionary mit den aktuellen Visualisierungen
        selected_variables: Liste der ausgewählten Variablen
        time_range: Zeitraum für die Visualisierung
        thresholds: Grenzwerte für die Visualisierung
        is_cleaned: Ob die Daten bereits bereinigt sind
    
    Returns:
        Aktualisiertes Dictionary mit den Visualisierungen
    """
    # Dictionary für aktualisierte Visualisierungen
    updated_figures = current_figures.copy()
    
    cleaned_suffix = " (bereinigt)" if is_cleaned else ""
    
    # Dashboard aktualisieren
    primary_vars = [var for var in selected_variables if var not in ['Flow_Rate_2', 'ARA_Flow']]
    flow_vars = [var for var in ['Flow_Rate_2', 'ARA_Flow'] if var in selected_variables]
    
    dashboard_fig = create_dashboard(
        data,
        primary_vars,
        flow_vars,
        title=f"IoT-Anlagen Dashboard{cleaned_suffix}",
        time_range=time_range,
        thresholds=thresholds
    )
    updated_figures["Dashboard-Übersicht"] = dashboard_fig
    
    # Zeitreihenanalyse aktualisieren
    time_series_fig = create_time_series_plot(
        data,
        selected_variables,
        title=f"Zeitreihenanalyse{cleaned_suffix}",
        height=500,
        thresholds=thresholds
    )
    updated_figures["Zeitreihenanalyse"] = time_series_fig
    
    # Heatmap aktualisieren, wenn vorhanden
    if "Heatmap" in current_figures:
        # Wir verwenden die erste ausgewählte Variable für die Heatmap
        if selected_variables:
            heatmap_var = selected_variables[0]
            heatmap_fig = create_heatmap(
                data,
                heatmap_var,
                title=f"Tageszeitliche Verteilung: {heatmap_var}{cleaned_suffix}",
                height=500
            )
            updated_figures["Heatmap"] = heatmap_fig
    
    # Flow-Visualisierung aktualisieren
    flow_cols = [col for col in data.columns if 'flow' in col.lower() or 'Flow' in col or 'Rate' in col]
    if flow_cols:
        flow_fig = create_time_series_plot(
            data,
            flow_cols,
            title=f"Flow-Werte im Zeitverlauf{cleaned_suffix}",
            height=500
        )
        updated_figures["Flow-Visualisierung"] = flow_fig
    
    return updated_figures

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
    # Standardgrenzwerte definieren
    st.session_state.thresholds = {
        'PH': 8.5,           # pH-Wert Standardgrenzwert
        'Truebung': 20.0,    # Trübung Standardgrenzwert (mg/l)
        'pH': 8.5            # Alternative Schreibweise für pH
    }
if 'available_templates' not in st.session_state:
    st.session_state.available_templates = []
if 'pump_variables' not in st.session_state:
    st.session_state.pump_variables = []
if 'pump_runtimes' not in st.session_state:
    st.session_state.pump_runtimes = {}
if 'auto_detect_pumps' not in st.session_state:
    st.session_state.auto_detect_pumps = True
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'cleaned_aggregates' not in st.session_state:
    st.session_state.cleaned_aggregates = None
if 'data_cleaned' not in st.session_state:
    st.session_state.data_cleaned = False

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
            raw_data = parse_csv_data(uploaded_file)
            
            # Automatische Datenbereinigung für Flow-Daten direkt beim Import
            st.info("Führe automatische Datenbereinigung durch...")
            
            # Automatisch alle negativen Flow-Werte korrigieren
            cleaned_data = clean_flow_data(raw_data, min_threshold=0.0, max_outlier_factor=2.0)
            
            # Bereingte Daten als Hauptdaten verwenden
            st.session_state.data = cleaned_data
            st.success(f"Datei erfolgreich geladen und bereinigt: {uploaded_file.name}")
            
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
                
            # Setze Flag, dass Daten bereits bereinigt wurden
            st.session_state.data_cleaned = True
            
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
        # Filtere die Daten nach dem ausgewählten Zeitraum
        filtered_data = filter_by_time_range(
            st.session_state.data, 
            st.session_state.time_range,
            st.session_state.custom_start_date,
            st.session_state.custom_end_date
        )
        
        # Überprüfe und bereinige negative Flow-Werte
        has_negative_flows = False
        for col in filtered_data.columns:
            if 'flow' in col.lower() or 'Flow' in col or 'Rate' in col:
                if (filtered_data[col] < 0).sum() > 0:
                    has_negative_flows = True
                    break
        
        # Wenn negative Flow-Werte gefunden wurden, bereinige sie
        if has_negative_flows:
            st.warning("Es wurden negative Flow-Werte gefunden. Diese werden automatisch bereinigt.")
            filtered_data = clean_flow_data(filtered_data, min_threshold=0.0, max_outlier_factor=2.0)
        
        # Speichere die gefilterten und bereinigten Daten
        st.session_state.filtered_data = filtered_data
    
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
            st.subheader("Grenzwerte definieren")
            st.info("Definieren Sie Grenzwerte für die ausgewählten Variablen. Werte, die diese Grenzen überschreiten, werden in den Visualisierungen hervorgehoben.")
            
            # Für jede ausgewählte Variable Eingabefeld für Grenzwert anzeigen
            for var in st.session_state.selected_variables:
                if var in st.session_state.data.columns:
                    # Standardwert ermitteln
                    default_value = None
                    
                    # Für pH-Wert den Standardwert 8.5 verwenden
                    if 'ph' in var.lower() or 'PH' in var:
                        default_value = 8.5
                        var_name = f"{var} (pH-Wert)"
                    # Für Trübung den Standardwert 20.0 mg/l verwenden
                    elif 'trueb' in var.lower() or 'trüb' in var.lower():
                        default_value = 20.0
                        var_name = f"{var} (Trübung in mg/l)"
                    else:
                        # Maximal- und Minimalwerte für die Variable berechnen
                        min_val = float(st.session_state.data[var].min())
                        max_val = float(st.session_state.data[var].max())
                        # Standardwert: 80% des Maximalwerts wenn kein spezieller Standardwert definiert
                        default_value = st.session_state.thresholds.get(var, max_val * 0.8)
                        var_name = var
                    
                    # Eingabefeld mit Nummer anzeigen
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Aktuellen Grenzwert aus dem Session State holen oder Standardwert verwenden
                        current_threshold = st.session_state.thresholds.get(var, default_value)
                        
                        # Nummerneingabefeld für den Grenzwert anzeigen
                        threshold = st.number_input(
                            f"Maximalwert für {var_name}:",
                            min_value=float(0),
                            max_value=float(1000),
                            value=float(current_threshold),
                            step=0.1,
                            format="%.2f"
                        )
                    
                    with col2:
                        # Info-Button mit Einheiten
                        if 'ph' in var.lower() or 'PH' in var:
                            st.info("Einheit: pH")
                        elif 'trueb' in var.lower() or 'trüb' in var.lower():
                            st.info("Einheit: mg/l")
                        elif 'flow' in var.lower() or 'Flow' in var:
                            if 'Rate' in var:
                                st.info("Einheit: m³/h")
                            else:
                                st.info("Einheit: m³")
                        elif 'temp' in var.lower() or 'Temp' in var:
                            st.info("Einheit: °C")
                    
                    # Grenzwert im Session State speichern
                    st.session_state.thresholds[var] = threshold

# Hauptbereich für Visualisierungen
if st.session_state.data is not None and st.session_state.filtered_data is not None:
    # Tabs für verschiedene Ansichten
    tab_names = ["Dashboard", "Detailansicht", "Datenanalyse", "Pumpen-Übersicht", "Flow-Berechnungen", "Datenbereinigung & Export"]
    current_tab = st.tabs(tab_names)
    
    # Store figures for PDF export
    current_figures = {}
    
    # Sicherstellen, dass wir keine negativen Flow-Werte in den Visualisierungen haben
    visualization_data = st.session_state.filtered_data.copy()
    any_negative_flows = False
    for col in visualization_data.columns:
        if 'flow' in col.lower() or 'Flow' in col or 'Rate' in col:
            neg_count = (visualization_data[col] < 0).sum()
            if neg_count > 0:
                any_negative_flows = True
                break
    
    # Wenn negative Flow-Werte gefunden wurden, diese bereinigen
    if any_negative_flows:
        print("Negative Flow-Werte in den Visualisierungsdaten gefunden. Automatische Bereinigung wird durchgeführt.")
        visualization_data = clean_flow_data(visualization_data, min_threshold=0.0, max_outlier_factor=2.0)
    
    with current_tab[0]:
        st.header("Dashboard-Übersicht")
        
        # Dashboard mit Telemetriedaten und Gesamtmengen
        primary_vars = [var for var in st.session_state.selected_variables if var not in ['Flow_Rate_2', 'ARA_Flow']]
        flow_vars = [var for var in ['Flow_Rate_2', 'ARA_Flow'] if var in st.session_state.selected_variables]
        
        if primary_vars or flow_vars:
            dashboard_fig = create_dashboard(
                visualization_data,  # Immer bereinigte Daten verwenden
                primary_vars,
                flow_vars,
                title="IoT-Anlagen Dashboard",
                time_range=st.session_state.time_range,
                thresholds=st.session_state.thresholds
            )
            
            st.plotly_chart(dashboard_fig, use_container_width=True)
            current_figures["Dashboard-Übersicht"] = dashboard_fig
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
    
    with current_tab[1]:
        st.header("Detailansicht")
        
        # Detaillierte Zeitreihenanalyse
        st.subheader("Zeitreihenanalyse")
        
        if st.session_state.selected_variables:
            time_series_fig = create_time_series_plot(
                visualization_data,
                st.session_state.selected_variables,
                title=f"Zeitreihenanalyse ({st.session_state.time_range})",
                height=500,
                thresholds=st.session_state.thresholds
            )
            
            st.plotly_chart(time_series_fig, use_container_width=True)
            current_figures["Zeitreihenanalyse"] = time_series_fig
        
        # Heatmap für ausgewählte Variable
        st.subheader("Tageszeit-Analyse")
        
        if st.session_state.selected_variables:
            selected_var_for_heatmap = st.selectbox(
                "Variable für Heatmap auswählen:",
                st.session_state.selected_variables
            )
            
            heatmap_fig = create_heatmap(
                visualization_data,
                selected_var_for_heatmap,
                title=f"Tageszeitliche Verteilung: {selected_var_for_heatmap}",
                height=500,
                thresholds=st.session_state.thresholds
            )
            
            st.plotly_chart(heatmap_fig, use_container_width=True)
            current_figures["Heatmap"] = heatmap_fig
    
    with current_tab[2]:
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
                    visualization_data,
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
                            x=visualization_data['Time'],
                            y=visualization_data[selected_var_for_outliers],
                            mode='lines+markers',
                            name=selected_var_for_outliers,
                            line=dict(color='blue', width=1),
                            marker=dict(size=5, color='blue'),
                        )
                    )
                    
                    # Ausreißer hervorheben
                    outliers = visualization_data.loc[outlier_indices]
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
                            visualization_data,
                            selected_var_for_outliers,
                            outlier_indices,
                            method=correction_method
                        )
                        
                        # Aktualisiere die Daten
                        visualization_data = corrected_data
                        
                        st.success(f"{len(outlier_indices)} Ausreißer in '{selected_var_for_outliers}' korrigiert.")
                else:
                    st.success(f"Keine Ausreißer in '{selected_var_for_outliers}' erkannt.")
        
        # Rohdaten anzeigen
        st.subheader("Rohdaten")
        
        if st.checkbox("Rohdaten anzeigen"):
            st.dataframe(visualization_data, use_container_width=True)
            
            # Daten herunterladen
            csv_data = visualization_data.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="CSV herunterladen",
                data=csv_data,
                file_name="iot_data_filtered.csv",
                mime="text/csv"
            )
    
    # Neuer Tab für Pumpen-Übersicht
    with current_tab[3]:
        st.header("Pumpen-Laufzeiten")
        
        if st.session_state.pump_variables:
            # Laufzeiten anzeigen
            st.subheader("Laufzeiten im ausgewählten Zeitraum")
            
            # Laufzeiten berechnen, falls noch nicht erfolgt
            if not st.session_state.pump_runtimes:
                st.session_state.pump_runtimes = calculate_pump_runtime(
                    visualization_data,
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
            pump_fig = go.Figure(data=[
                go.Bar(
                    x=pump_labels,
                    y=pump_values,
                    text=[f"{val:.2f} h" for val in pump_values],
                    textposition='auto',
                    marker_color='royalblue'
                )
            ])
            
            pump_fig.update_layout(
                title="Laufzeiten der Pumpen im Vergleich",
                xaxis_title="Pumpe",
                yaxis_title="Laufzeit (Stunden)",
                height=400,
                template="plotly_white"
            )
            
            st.plotly_chart(pump_fig, use_container_width=True)
            
            # Zeitlicher Verlauf der Pumpenaktivitäten (nur wenn binäre 0/1-Daten)
            if visualization_data is not None:
                st.subheader("Zeitlicher Verlauf der Pumpenaktivitäten")
                
                # Zeitreihen-Diagramm für die Pumpenaktivitäten
                time_series_fig = create_time_series_plot(
                    visualization_data,
                    st.session_state.pump_variables,
                    title=f"Pumpenaktivitäten im Zeitverlauf ({st.session_state.time_range})",
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
    with current_tab[4]:
        st.header("Flow-Berechnungen")
        
        # Identifiziere alle Flow-bezogenen Spalten
        flow_cols = [col for col in visualization_data.columns if 'Flow' in col or 'flow' in col]
        
        if flow_cols:
            # Zeige eine Info über die erkannten Flow-Spalten an
            st.info(f"Erkannte Flow-Spalten: {', '.join(flow_cols)}")
            
            # Berechne Gesamtmengen für jeden Flow
            flow_totals = {}
            for col in flow_cols:
                # Verwende die verbesserte Berechnungsmethode mit Zeitberücksichtigung
                flow_totals[col] = calculate_flow_with_time(visualization_data, col)
            
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
            
            # Flow-Visualisierung
            flow_fig = create_time_series_plot(
                visualization_data,
                flow_cols,
                title=f"Flow-Werte im Zeitverlauf ({st.session_state.time_range})",
                height=500
            )
            
            st.plotly_chart(flow_fig, use_container_width=True)
            current_figures["Flow-Visualisierung"] = flow_fig
            
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
            unique_dates = visualization_data['Time'].dt.date.unique()
            daily_sums = pd.DataFrame({'Date': unique_dates})
            
            # Für jedes Datum und jede Flow-Spalte die verbesserte Berechnungsmethode anwenden
            for col in flow_cols:
                daily_values = []
                
                for date in unique_dates:
                    # Daten für den aktuellen Tag filtern
                    day_data = visualization_data[visualization_data['Time'].dt.date == date]
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

    with current_tab[5]:
        st.header("Datenbereinigung & Export")
        st.markdown("Hier können Sie die Daten bereinigen und als PDF exportieren.")
        
        # Zwei Spalten für Export und Datenbereinigung
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Datenbereinigungsoptionen")
            
            # Option zum Aktivieren der Datenbereinigung
            enable_cleaning = st.checkbox("Datenbereinigung aktivieren", value=True)
            
            if enable_cleaning:
                # Optionen für die Datenbereinigung
                cleaning_options = st.expander("Bereinigungsoptionen anzeigen", expanded=True)
                
                with cleaning_options:
                    # Negative Flow-Werte korrigieren
                    clean_negative_flow = st.checkbox("Negative Flow-Werte auf 0 setzen", value=True)
                    
                    # Lücken interpolieren
                    interpolate_gaps = st.checkbox("Datenlücken interpolieren", value=True)
                    
                    # Spezielle Flow-Bereinigung
                    special_flow_cleaning = st.checkbox("Erweiterte Flow-Daten Bereinigung", value=True)
                    
                    if special_flow_cleaning:
                        col1, col2 = st.columns(2)
                        with col1:
                            min_threshold = st.number_input("Minimalwert für Flow-Daten:", 
                                                          value=0.0, 
                                                          step=0.1, 
                                                          help="Alle Werte unterhalb dieses Schwellenwerts werden ersetzt")
                        with col2:
                            max_outlier_factor = st.number_input("Ausreißer-Faktor:", 
                                                               value=2.0, 
                                                               min_value=1.1, 
                                                               max_value=10.0, 
                                                               step=0.1,
                                                               help="Werte über dem X-fachen des Medians werden als Ausreißer behandelt")
                    
                    # Ausreißer entfernen
                    remove_outliers_option = st.checkbox("Allgemeine Ausreißerentfernung", value=False)
                    
                    if remove_outliers_option:
                        # Methode zur Ausreißererkennung
                        outlier_method = st.selectbox(
                            "Methode zur Ausreißererkennung:",
                            options=["iqr", "zscore", "percentile"],
                            format_func=lambda x: {
                                "iqr": "IQR (Interquartilsabstand)",
                                "zscore": "Z-Score",
                                "percentile": "Perzentil-basiert (1% - 99%)"
                            }.get(x, x)
                        )
                        
                        # Schwellenwert für die Ausreißererkennung
                        if outlier_method == "iqr":
                            threshold = st.slider("IQR-Multiplikator:", 1.0, 3.0, 1.5, 0.1)
                        elif outlier_method == "zscore":
                            threshold = st.slider("Z-Score Schwellenwert:", 2.0, 5.0, 3.0, 0.1)
                        else:
                            threshold = 0  # Wird bei Perzentil-Methode nicht verwendet
                        
                        # Wie Ausreißer ersetzt werden sollen
                        replace_with = st.selectbox(
                            "Ausreißer ersetzen durch:",
                            options=["interpolate", "mean", "median", "nan", "0"],
                            format_func=lambda x: {
                                "interpolate": "Interpolierte Werte",
                                "mean": "Mittelwert",
                                "median": "Median",
                                "nan": "NaN (fehlende Werte)",
                                "0": "Null"
                            }.get(x, x)
                        )
                        
                        # Variablen auswählen, für die Ausreißer entfernt werden sollen
                        if visualization_data is not None:
                            numeric_cols = visualization_data.select_dtypes(include=['number']).columns.tolist()
                            outlier_variables = st.multiselect(
                                "Variablen für die Ausreißerentfernung:",
                                options=numeric_cols,
                                default=st.session_state.selected_variables
                            )
                
                # Button zum Anwenden der Bereinigung
                if st.button("Daten bereinigen", key="clean_data"):
                    if visualization_data is not None:
                        # Daten bereinigen
                        cleaned_data = visualization_data.copy()
                        
                        # Zuerst negative Flow-Werte korrigieren und Lücken interpolieren
                        if clean_negative_flow or interpolate_gaps:
                            st.info("Bereinige Basisdaten...")
                            cleaned_data = clean_dataset(
                                cleaned_data,
                                clean_negative_flow=clean_negative_flow,
                                interpolate_gaps=interpolate_gaps
                            )
                        
                            # Spezielle Flow-Daten Bereinigung
                            if special_flow_cleaning:
                                st.info("Führe erweiterte Flow-Daten Bereinigung durch...")
                                cleaned_data = clean_flow_data(
                                    cleaned_data,
                                    min_threshold=min_threshold if 'min_threshold' in locals() else 0.0,
                                    max_outlier_factor=max_outlier_factor if 'max_outlier_factor' in locals() else 2.0
                                )
                        
                        # Dann Ausreißer entfernen, wenn aktiviert
                        if remove_outliers_option:
                            st.info("Entferne allgemeine Ausreißer...")
                            cleaned_data = remove_outliers(
                                cleaned_data,
                                method=outlier_method,
                                variables=outlier_variables if 'outlier_variables' in locals() else None,
                                threshold=threshold,
                                replace_with=replace_with
                            )
                        
                        # WICHTIG: Ersetze alle relevanten Daten in der Session mit den bereinigten Daten
                        st.session_state.data = st.session_state.data.copy()  # Original-Daten für Referenz behalten
                        st.session_state.filtered_data = cleaned_data  # Gefilterte Daten ersetzen
                        st.session_state.cleaned_data = cleaned_data  # Bereinigte Daten speichern
                        
                        # Aggregate neu berechnen
                        st.session_state.aggregates = calculate_aggregates(cleaned_data)  # Direkt Hauptaggregate ersetzen
                        st.session_state.cleaned_aggregates = st.session_state.aggregates  # Kopie für Referenz
                        
                        # Alle Visualisierungen mit bereinigten Daten aktualisieren
                        st.info("Aktualisiere alle Visualisierungen...")
                        
                        # Aktualisiere alle Visualisierungen mit der neuen Funktion
                        current_figures = update_all_visualizations(
                            cleaned_data,
                            current_figures,
                            st.session_state.selected_variables,
                            st.session_state.time_range,
                            st.session_state.thresholds,
                            is_cleaned=True
                        )
                        
                        # Erfolg anzeigen
                        st.success("Daten wurden erfolgreich bereinigt! Alle Visualisierungen wurden aktualisiert.")
                        
                        # Zeige die Visualisierung direkt im Bereich an
                        if "Flow-Visualisierung" in current_figures:
                            st.subheader("Bereinigte Flow-Visualisierung")
                            st.plotly_chart(current_figures["Flow-Visualisierung"], use_container_width=True)
                        
                        # Zeige Statistiken zu den bereinigten Daten an
                        flow_cols = [col for col in cleaned_data.columns if 'flow' in col.lower() or 'Flow' in col or 'Rate' in col]
                        if flow_cols and "Flow-Visualisierung" in current_figures:
                            st.subheader("Statistik der bereinigten Flow-Daten")
                            stats_cols = st.columns(len(flow_cols))
                            for i, col in enumerate(flow_cols):
                                with stats_cols[i]:
                                    st.metric(
                                        label=f"{col} Median", 
                                        value=f"{cleaned_data[col].median():.2f} m³/h"
                                    )
                                    st.metric(
                                        label=f"{col} Max", 
                                        value=f"{cleaned_data[col].max():.2f} m³/h"
                                    )
                                    st.metric(
                                        label=f"{col} Min", 
                                        value=f"{cleaned_data[col].min():.2f} m³/h"
                                    )
                                    
                        # Flag setzen, dass Daten bereinigt wurden und Session-State-Aktualisierung erzwingen
                        st.session_state.data_cleaned = True
                        
                        # Seite neu laden, um sicherzustellen, dass alle Tabs die bereinigten Daten verwenden
                        st.rerun()
                    else:
                        st.warning("Keine Daten zum Bereinigen vorhanden.")
            
        with col2:
            st.subheader("PDF Export")
            
            # Zeige an, welche Visualisierungen exportiert werden
            if current_figures:
                st.info(f"Folgende Visualisierungen werden exportiert: {', '.join(current_figures.keys())}")
                
                # Status der Datenbereinigung anzeigen
                data_cleaned_status = st.session_state.get("data_cleaned", False)
                
                if data_cleaned_status:
                    st.success("Die Daten wurden bereinigt. Der Export wird die bereinigten Daten verwenden.")
                else:
                    st.warning("Die Daten wurden noch nicht bereinigt. Klicken Sie auf 'Daten bereinigen', um die Daten vor dem Export zu bereinigen.")
                
                if st.button("PDF Export erstellen"):
                    try:
                        # Verwende die gefilterten Daten
                        export_data = visualization_data.copy()
                        export_aggregates = st.session_state.aggregates
                        
                        # Immer eine finale Prüfung auf negative Flow-Werte durchführen
                        need_final_cleaning = False
                        for col in export_data.columns:
                            if 'Flow' in col or 'flow' in col or 'Rate' in col:
                                neg_count = (export_data[col] < 0).sum()
                                if neg_count > 0:
                                    need_final_cleaning = True
                                    st.warning(f"⚠️ {col}: {neg_count} negative Werte gefunden! Diese werden für den Export korrigiert.")
                        
                        # Falls nötig, führe eine finale Bereinigung durch
                        if need_final_cleaning:
                            export_data = clean_flow_data(export_data, min_threshold=0.0, max_outlier_factor=2.0)
                            st.success("Finale Datenbereinigung für den Export durchgeführt.")
                            
                            # Statistik für bereinigte Daten anzeigen
                            flow_cols = [col for col in export_data.columns if 'flow' in col.lower() or 'Flow' in col or 'Rate' in col]
                            if flow_cols:
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Negative Flow-Werte", "0")
                                with col2:
                                    st.metric("Bereinigter Zeitraum", f"{export_data.index.min().strftime('%d.%m.%Y')} - {export_data.index.max().strftime('%d.%m.%Y')}")
                                with col3:
                                    st.metric("Datenpunkte", f"{len(export_data)}")
                        
                        # Export durchführen
                        pdf_path = export_current_view(
                            export_data,
                            current_figures,
                            st.session_state.selected_variables,
                            export_aggregates
                        )
                        
                        # Create download button for the PDF
                        with open(pdf_path, "rb") as pdf_file:
                            pdf_bytes = pdf_file.read()
                        
                        st.download_button(
                            label="PDF herunterladen",
                            data=pdf_bytes,
                            file_name=pdf_path.split('/')[-1],
                            mime="application/pdf"
                        )
                        
                        st.success(f"PDF wurde erfolgreich erstellt mit {'bereinigten' if data_cleaned_status else 'original'} Daten!")
                        
                        # Clean up the temporary file
                        os.remove(pdf_path)
                    except Exception as e:
                        st.error(f"Fehler beim Erstellen des PDFs: {str(e)}")
            else:
                st.warning("Keine Visualisierungen verfügbar. Bitte wählen Sie zuerst Variablen aus und erstellen Sie Visualisierungen.")

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