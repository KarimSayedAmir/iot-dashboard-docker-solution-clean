"""
Visualisierungsmodul für das IoT-Dashboard.
Enthält Funktionen zur Erstellung von Plots und Diagrammen.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import numpy as np

# Define units for each measurement type
UNITS = {
    'Truebung': 'mg/l',
    'Trübung': 'mg/l',
    'Flow_Rate': 'm³/h',
    'Flow_Rate_2': 'm³/h',
    'Flow_Rate_58': 'm³/h',
    'Flow_Rate_59': 'm³/h',
    'ARA_Flow': 'm³/h',
    'Flow_58': 'm³',
    'Flow_59': 'm³',
    'PH': 'pH',
    'pH': 'pH',
    'Temperature': '°C',
    'Temp': '°C',
    'total_flow': 'm³'
}

def get_unit_for_variable(variable_name: str) -> str:
    """Get the appropriate unit for a variable."""
    # Check for exact matches first
    if variable_name in UNITS:
        return UNITS[variable_name]
    
    # Check for partial matches
    for key in UNITS:
        if key.lower() in variable_name.lower():
            return UNITS[key]
    
    return ''

def create_time_series_plot(data: pd.DataFrame,
                          variables: List[str],
                          title: str = "Zeitreihenanalyse",
                          height: int = 600,
                          thresholds: Dict = None,
                          pump_variables: List[str] = None) -> go.Figure:
    """Create a time series plot for selected variables."""
    # Daten kopieren und bereinigen
    plot_data = data.copy()
    
    # Wenn keine Zeitstempel-Spalte vorhanden ist, aktuelle Zeit verwenden
    if 'Time' not in plot_data.columns and isinstance(plot_data.index, pd.DatetimeIndex):
        plot_data['Time'] = plot_data.index
    
    # Figure erstellen
    fig = go.Figure()
    
    # Farbschema für die Linien
    color_map = {
        'Pump_58': '#E63946',  # Rot
        'Pump_59': '#457B9D',  # Blau
        'Flow_Rate_58': '#F4A261',  # Orange
        'Flow_Rate_59': '#2A9D8F',  # Grün
        'ARA_Flow': '#023E8A'   # Dunkelblau
    }
    
    # Prüfen, ob Variablen existieren
    plot_vars = []
    for var in variables:
        if var in plot_data.columns:
            plot_vars.append(var)
    
    for var in plot_vars:
        # Get the unit for the variable
        unit = get_unit_for_variable(var)
        # Add unit to the name if available
        var_name = f"{var} [{unit}]" if unit else var
        
        # Boolean- oder String-Werte in numerische Werte konvertieren (speziell für Pumpen)
        if pump_variables is not None and var in pump_variables:
            # Wenn die Variable eine Pumpenvariable ist
            
            # Anzeigenamen für die Legende anpassen
            display_name = var_name
            if var == "Pump_58":
                display_name = "Pumpe 1 (Gerät 0058)"
            elif var == "Pump_59":
                display_name = "Pumpe 2 (Gerät 0059)"
            
            if plot_data[var].dtype == 'bool':
                # Boolean-Werte in 0 und 1 konvertieren
                plot_data[var] = plot_data[var].astype(int)
                
                # Spezielle Darstellung für Pumpenaktivität
                fig.add_trace(
                    go.Scatter(
                        x=plot_data['Time'],
                        y=plot_data[var],
                        mode='lines',
                        name=display_name,
                        line=dict(color=color_map.get(var, 'blue'), width=2)
                    )
                )
            else:
                # Normale Darstellung für numerische Werte
                fig.add_trace(
                    go.Scatter(
                        x=plot_data['Time'],
                        y=plot_data[var],
                        mode='lines',
                        name=display_name
                    )
                )
        else:
            # Standardverhalten für andere Variablen
            fig.add_trace(
                go.Scatter(
                    x=plot_data['Time'],
                    y=plot_data[var],
                    mode='lines',
                    name=var_name
                )
            )
        
        # Grenzwerte hinzufügen, wenn vorhanden
        if thresholds and var in thresholds:
            # Grenzwert-Linie mit verbesserter Sichtbarkeit
            fig.add_trace(
                go.Scatter(
                    x=[plot_data['Time'].iloc[0], plot_data['Time'].iloc[-1]],
                    y=[thresholds[var], thresholds[var]],
                    mode='lines',
                    name=f"Grenzwert: {thresholds[var]:.2f} {unit}",
                    line=dict(color='red', width=2, dash='dash'),
                    fill='tonexty',  # Füllung zwischen Linie und oberem Rand
                    fillcolor='rgba(255, 0, 0, 0.1)'  # Leichte rote Färbung
                )
            )
            
            # Text-Label für den Grenzwert
            fig.add_annotation(
                x=plot_data['Time'].iloc[-1],
                y=thresholds[var],
                text=f"Grenzwert: {thresholds[var]:.2f} {unit}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='red',
                bgcolor='white',
                bordercolor='red'
            )
    
    fig.update_layout(
        title=title,
        xaxis_title="Zeit",
        yaxis_title="Wert",
        height=height,
        showlegend=True,
        hovermode='x unified',
        margin=dict(t=100),  # Mehr Platz oben für Annotationen
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_bar_chart(data: pd.DataFrame,
                    variables: List[str],
                    title: str = "Aggregierte Daten",
                    height: int = 500,
                    aggregate_func: str = 'sum',
                    thresholds: Dict[str, float] = None) -> go.Figure:
    """
    Erstellt ein Balkendiagramm für die angegebenen Variablen.
    
    Args:
        data: DataFrame mit den Daten
        variables: Liste der darzustellenden Variablen
        title: Titel des Diagramms
        height: Höhe des Diagramms in Pixeln
        aggregate_func: Aggregationsfunktion ('sum', 'mean', 'max', 'min')
        thresholds: Dictionary mit Grenzwerten für Variablen {variable_name: threshold_value}
        
    Returns:
        Plotly-Figur mit dem Balkendiagramm
    """
    if data.empty or not variables:
        # Leeres Diagramm zurückgeben
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title="Variable",
            yaxis_title="Wert",
            height=height,
            template="plotly_white"
        )
        fig.add_annotation(
            text="Keine Daten verfügbar",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Grenzwerte initialisieren
    if thresholds is None:
        thresholds = {}
    
    # Farben für die verschiedenen Variablen
    color_map = {
        'PH_58': '#0066cc',
        'Trübung_Zulauf': '#ff9900',
        'Water_Level': '#00cc66',
        'Flow_Rate_2': '#cc0066',
        'ARA_Flow': '#9933cc',
        'Pumpdauer': '#ff6600'
    }
    
    # Filtern der Daten für die angegebenen Variablen
    plot_vars = [var for var in variables if var in data.columns]
    
    if not plot_vars:
        # Keine Daten für die ausgewählten Variablen
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title="Variable",
            yaxis_title="Wert",
            height=height,
            template="plotly_white"
        )
        fig.add_annotation(
            text="Keine Daten für die ausgewählten Variablen verfügbar",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Aggregieren der Daten
    if aggregate_func == 'sum':
        agg_data = data[plot_vars].sum()
    elif aggregate_func == 'mean':
        agg_data = data[plot_vars].mean()
    elif aggregate_func == 'max':
        agg_data = data[plot_vars].max()
    elif aggregate_func == 'min':
        agg_data = data[plot_vars].min()
    else:
        print(f"Unbekannte Aggregationsfunktion: {aggregate_func}. Verwende 'sum'.")
        agg_data = data[plot_vars].sum()
    
    # Erstellen des Diagramms
    fig = go.Figure()
    
    for i, var in enumerate(plot_vars):
        # Get the unit for the variable
        unit = get_unit_for_variable(var)
        # Add unit to the name if available
        var_name = f"{var} [{unit}]" if unit else var
        
        # Farbe auswählen
        color = color_map.get(var, px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)])
        
        # Balken hinzufügen
        fig.add_trace(
            go.Bar(
                x=[var_name],
                y=[agg_data[var]],
                name=var_name,
                marker_color=color,
                text=[f"{agg_data[var]:.2f}"],
                textposition="auto"
            )
        )
    
    # Layout anpassen
    fig.update_layout(
        title=title,
        xaxis_title="Variable",
        yaxis_title=f"{aggregate_func.capitalize()} [{unit}]" if unit else f"{aggregate_func.capitalize()}",
        height=height,
        template="plotly_white",
        showlegend=False
    )
    
    return fig

def create_heatmap(data: pd.DataFrame,
                  variable: str,
                  title: str = "Heatmap der Daten",
                  height: int = 500,
                  thresholds: Dict[str, float] = None) -> go.Figure:
    """
    Erstellt eine Heatmap für eine Variable nach Stunde und Tag.
    
    Args:
        data: DataFrame mit den Daten
        variable: Name der darzustellenden Variable
        title: Titel des Diagramms
        height: Höhe des Diagramms in Pixeln
        thresholds: Dictionary mit Grenzwerten für Variablen {variable_name: threshold_value}
        
    Returns:
        Plotly-Figur mit der Heatmap
    """
    if data.empty or variable not in data.columns:
        # Leeres Diagramm zurückgeben
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title="Stunde",
            yaxis_title="Tag",
            height=height,
            template="plotly_white"
        )
        fig.add_annotation(
            text="Keine Daten verfügbar",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Grenzwerte initialisieren
    if thresholds is None:
        thresholds = {}
    
    # Kopie der Daten erstellen
    plot_data = data.copy()
    
    # Stunde und Tag aus dem Zeitstempel extrahieren
    if not pd.api.types.is_datetime64_any_dtype(plot_data['Time']):
        try:
            plot_data['Time'] = pd.to_datetime(plot_data['Time'])
        except:
            print("Fehler beim Konvertieren der Zeitstempel für die Heatmap.")
            return go.Figure()
    
    plot_data['Hour'] = plot_data['Time'].dt.hour
    plot_data['Day'] = plot_data['Time'].dt.day_name()
    
    # Daten nach Stunde und Tag gruppieren
    heatmap_data = plot_data.groupby(['Day', 'Hour'])[variable].mean().reset_index()
    
    # Pivot-Tabelle erstellen
    heatmap_pivot = heatmap_data.pivot(index='Day', columns='Hour', values=variable)
    
    # Reihenfolge der Tage festlegen
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_pivot = heatmap_pivot.reindex(days_order)
    
    # Standardfarbskala - IMMER eine sichere vordefinierte Skala verwenden
    colorscale = 'Viridis'
    
    # Überprüfe auf Grenzwert
    threshold = thresholds.get(variable, None)
    
    try:
        # Maximalen Wert für die Normalisierung berechnen
        max_val = heatmap_pivot.values.max()
        
        # Nur wenn ein Grenzwert definiert ist UND max_val gültig ist, benutzerdefinierte Farbskala versuchen
        if threshold is not None and pd.notnull(max_val) and max_val > 0:
            threshold_float = float(threshold)
            max_val_float = float(max_val)
            
            if max_val_float > 0 and threshold_float > 0:
                # Berechne einen sicheren normalisierten Grenzwert zwischen 0.1 und 0.9
                norm_threshold = min(0.9, max(0.1, threshold_float / max_val_float))
                
                # Nur eine Farbskala mit festen Werten verwenden - keine Berechnungen in der Liste
                colorscale = [
                    [0.0, 'blue'],
                    [norm_threshold, 'yellow'],
                    [1.0, 'red']
                ]
    except Exception as e:
        # Bei jedem Fehler zurück zur sicheren Standardfarbskala
        print(f"Fehler bei der Berechnung der Farbskala: {e}. Verwende Standardfarbskala.")
        colorscale = 'RdYlBu_r'
    
    # Heatmap erstellen - mit try-except für zusätzliche Sicherheit
    try:
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale=colorscale,
            colorbar=dict(
                title=variable,
                titleside="right"
            ),
            hovertemplate="Tag: %{y}<br>Stunde: %{x}<br>Wert: %{z:.2f}<extra></extra>"
        ))
    except Exception as e:
        # Bei Fehler mit der Heatmap, erstelle eine einfachere Version ohne benutzerdefinierte Farbskala
        print(f"Fehler beim Erstellen der Heatmap: {e}. Erstelle vereinfachte Version.")
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            colorscale='Viridis',  # Garantiert sichere Standardfarbskala
            colorbar=dict(title=variable),
            hovertemplate="Tag: %{y}<br>Stunde: %{x}<br>Wert: %{z:.2f}<extra></extra>"
        ))
    
    # Wenn ein Grenzwert definiert ist, Annotation hinzufügen
    if threshold is not None:
        try:
            fig.add_annotation(
                text=f"Grenzwert: {float(threshold):.2f}",
                x=0.5,
                y=-0.15,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(color="red", size=12)
            )
        except:
            # Bei Fehler mit der Annotation, überspringen
            pass
    
    # Layout anpassen
    fig.update_layout(
        title=title,
        xaxis_title="Stunde",
        yaxis_title="Tag",
        height=height,
        template="plotly_white"
    )
    
    return fig

def create_dashboard(data: pd.DataFrame,
                    primary_vars: List[str],
                    flow_vars: List[str],
                    title: str = "Dashboard",
                    time_range: str = "day",
                    thresholds: Dict = None) -> go.Figure:
    """Create a dashboard with multiple plots."""
    # Calculate number of rows needed
    n_rows = len(primary_vars) + (1 if flow_vars else 0)
    
    fig = make_subplots(
        rows=n_rows,
        cols=1,
        subplot_titles=[f"{var} [{get_unit_for_variable(var)}]" if get_unit_for_variable(var) else var 
                       for var in primary_vars + (flow_vars if flow_vars else [])],
        vertical_spacing=0.1
    )
    
    # Color definitions for consistent visualization
    color_map = {
        'Pump_58': '#E63946',  # Rot
        'Pump_59': '#457B9D',  # Blau
        'Flow_Rate_58': '#F4A261',  # Orange
        'Flow_Rate_59': '#2A9D8F',  # Grün
        'ARA_Flow': '#023E8A'   # Dunkelblau
    }
    
    # Add primary variables
    for i, var in enumerate(primary_vars, 1):
        unit = get_unit_for_variable(var)
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data[var],
                name=f"{var} [{unit}]" if unit else var,
                mode='lines',
                line=dict(color=color_map.get(var, None))
            ),
            row=i,
            col=1
        )
        
        # Add threshold line with improved visibility if available
        if thresholds and var in thresholds:
            # Add threshold line
            fig.add_trace(
                go.Scatter(
                    x=[data.index[0], data.index[-1]],
                    y=[thresholds[var], thresholds[var]],
                    mode='lines',
                    name=f"Grenzwert: {thresholds[var]:.2f} {unit}",
                    line=dict(color='red', width=2, dash='dash'),
                    fill='tonexty',  # Fill area above the line
                    fillcolor='rgba(255, 0, 0, 0.1)'  # Light red color
                ),
                row=i,
                col=1
            )
            
            # Add annotation for threshold
            fig.add_annotation(
                x=data.index[-1],
                y=thresholds[var],
                text=f"Grenzwert: {thresholds[var]:.2f} {unit}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor='red',
                bgcolor='white',
                bordercolor='red',
                row=i,
                col=1
            )
    
    # Add flow variables if present
    if flow_vars:
        for var in flow_vars:
            unit = get_unit_for_variable(var)
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data[var],
                    name=f"{var} [{unit}]" if unit else var,
                    mode='lines',
                    line=dict(color=color_map.get(var, None))
                ),
                row=n_rows,
                col=1
            )
            
            # Add threshold for flow variables too
            if thresholds and var in thresholds:
                fig.add_trace(
                    go.Scatter(
                        x=[data.index[0], data.index[-1]],
                        y=[thresholds[var], thresholds[var]],
                        mode='lines',
                        name=f"Grenzwert: {thresholds[var]:.2f} {unit}",
                        line=dict(color='red', width=2, dash='dash'),
                        fill='tonexty',
                        fillcolor='rgba(255, 0, 0, 0.1)'
                    ),
                    row=n_rows,
                    col=1
                )
                
                # Add annotation for flow threshold
                fig.add_annotation(
                    x=data.index[-1],
                    y=thresholds[var],
                    text=f"Grenzwert: {thresholds[var]:.2f} {unit}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor='red',
                    bgcolor='white',
                    bordercolor='red',
                    row=n_rows,
                    col=1
                )
    
    fig.update_layout(
        height=300 * n_rows,
        title=title,
        showlegend=True,
        hovermode='x unified',
        margin=dict(t=100, r=150),  # Extra margin for annotations
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update y-axis titles with units
    for i, var in enumerate(primary_vars + (flow_vars if flow_vars else []), 1):
        unit = get_unit_for_variable(var)
        fig.update_yaxes(title_text=f"Wert [{unit}]" if unit else "Wert", row=i, col=1)
    
    return fig 