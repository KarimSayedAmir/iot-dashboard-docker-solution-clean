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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

# Module importieren
from modules.data_processing import (
    parse_csv_data, 
    filter_by_time_range, 
    calculate_aggregates, 
    identify_outliers, 
    correct_outliers
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

# Sidebar für Datenupload und Filter
with st.sidebar:
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

# Hauptbereich für Visualisierungen
if st.session_state.data is not None and st.session_state.filtered_data is not None:
    # Tabs für verschiedene Ansichten
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Detailansicht", "Datenanalyse"])
    
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
                time_range=st.session_state.time_range
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
                st.metric("Pumpdauer", f"{metrics.get('pumpDuration', 0):.1f} Stunden")
            
            with col2:
                st.metric("Gesamtmenge ARA", f"{metrics.get('totalFlowARA', 0):.2f} m³")
            
            with col3:
                st.metric("Gesamtmenge Galgenkanal", f"{metrics.get('totalFlowGalgenkanal', 0):.2f} m³")
    
    with tab2:
        st.header("Detailansicht")
        
        # Detaillierte Zeitreihenanalyse
        st.subheader("Zeitreihenanalyse")
        
        if st.session_state.selected_variables:
            time_series_fig = create_time_series_plot(
                st.session_state.filtered_data,
                st.session_state.selected_variables,
                title=f"Zeitreihenanalyse ({time_range})",
                height=500
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
                height=500
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
            'ARA_Flow': np.random.normal(180, 40, 100)
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