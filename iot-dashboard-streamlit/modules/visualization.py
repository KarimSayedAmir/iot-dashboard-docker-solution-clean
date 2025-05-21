"""
Visualisierungsmodul für das IoT-Dashboard.
Enthält Funktionen zur Erstellung von Plots und Diagrammen.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Union

def create_time_series_plot(data: pd.DataFrame, 
                           variables: List[str],
                           title: str = "Zeitreihe der Sensordaten",
                           height: int = 500,
                           thresholds: Dict[str, float] = None) -> go.Figure:
    """
    Erstellt ein Zeitreihendiagramm für die angegebenen Variablen.
    
    Args:
        data: DataFrame mit den Daten
        variables: Liste der darzustellenden Variablen
        title: Titel des Diagramms
        height: Höhe des Diagramms in Pixeln
        thresholds: Dictionary mit Grenzwerten für Variablen {variable_name: threshold_value}
        
    Returns:
        Plotly-Figur mit dem Zeitreihendiagramm
    """
    if data.empty:
        # Leeres Diagramm zurückgeben, wenn keine Daten vorhanden sind
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title="Zeit",
            yaxis_title="Wert",
            height=height,
            template="plotly_white"
        )
        return fig
    
    # Kopie der Daten erstellen, um die Originaldaten nicht zu verändern
    plot_data = data.copy()
    
    # Sicherstellen, dass die Zeit-Spalte im richtigen Format ist
    if not pd.api.types.is_datetime64_any_dtype(plot_data['Time']):
        try:
            plot_data['Time'] = pd.to_datetime(plot_data['Time'])
        except:
            print("Fehler beim Konvertieren der Zeitstempel für die Visualisierung.")
    
    # Figur initialisieren
    fig = go.Figure()
    
    # Pumpen-Variablen erkennen (für spezielle Behandlung)
    pump_variables = [var for var in variables if "Pump" in var]
    
    # Für jede Variable eine Trace hinzufügen
    for var in variables:
        if var in plot_data.columns:
            # Boolean- oder String-Werte in numerische Werte konvertieren (speziell für Pumpen)
            if var in pump_variables:
                # Für boolean-Werte
                if plot_data[var].dtype == 'bool':
                    plot_data[var] = plot_data[var].astype(int)
                # Für string-basierte true/false Werte
                elif plot_data[var].dtype == 'object':
                    try:
                        # Prüfen, ob es sich um 'true'/'false' Strings handelt
                        if plot_data[var].astype(str).str.lower().str.contains('true').any() or \
                           plot_data[var].astype(str).str.lower().str.contains('false').any():
                            plot_data[var] = plot_data[var].astype(str).str.lower().str.contains('true').astype(int)
                        else:
                            # Wenn nicht, versuchen als Zahl zu interpretieren
                            plot_data[var] = pd.to_numeric(plot_data[var], errors='coerce').fillna(0)
                    except:
                        print(f"Warnung: Konnte Variable {var} nicht für die Visualisierung konvertieren.")
                
                # Fehlende Werte als 0 interpretieren
                plot_data[var] = plot_data[var].fillna(0)
                
                # Werte > 0 als 1 (AN) interpretieren für die Visualisierung
                plot_data[var] = (plot_data[var] > 0).astype(int)
                
                # Anzeigenamen für die Legende anpassen
                display_name = var
                if var == "Pump_58":
                    display_name = "Pumpe 1 (Gerät 0058)"
                elif var == "Pump_59":
                    display_name = "Pumpe 2 (Gerät 0059)"
                
                # Pumpen als Stufendiagramm darstellen
                fig.add_trace(
                    go.Scatter(
                        x=plot_data['Time'],
                        y=plot_data[var],
                        mode='lines',
                        name=display_name,
                        line=dict(shape='hv', width=2),  # Stufenform für Pumpen
                        line_color="green" if "Pump_58" in var else "blue"  # Farbe anpassen
                    )
                )
            else:
                # Normaler Trace für nicht-Pumpen-Variablen
                fig.add_trace(
                    go.Scatter(
                        x=plot_data['Time'],
                        y=plot_data[var],
                        mode='lines',
                        name=var
                    )
                )
            
            # Grenzwerte als horizontale Linie hinzufügen, falls vorhanden
            if thresholds and var in thresholds:
                fig.add_trace(
                    go.Scatter(
                        x=[plot_data['Time'].min(), plot_data['Time'].max()],
                        y=[thresholds[var], thresholds[var]],
                        mode='lines',
                        name=f"Grenzwert: {var}",
                        line=dict(color='red', width=1, dash='dash')
                    )
                )
    
    # Layout anpassen
    fig.update_layout(
        title=title,
        xaxis_title="Zeit",
        yaxis_title="Wert",
        height=height,
        template="plotly_white",
        hovermode="x unified"
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
        # Farbe auswählen
        color = color_map.get(var, px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)])
        
        # Balken hinzufügen
        fig.add_trace(
            go.Bar(
                x=[var],
                y=[agg_data[var]],
                name=var,
                marker_color=color,
                text=[f"{agg_data[var]:.2f}"],
                textposition="auto"
            )
        )
    
    # Layout anpassen
    fig.update_layout(
        title=title,
        xaxis_title="Variable",
        yaxis_title=f"{aggregate_func.capitalize()}",
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
                    title: str = "IoT-Anlagen Dashboard",
                    time_range: str = 'week',
                    thresholds: Dict[str, float] = None) -> go.Figure:
    """
    Erstellt ein Dashboard mit mehreren Visualisierungen.
    
    Args:
        data: DataFrame mit den Daten
        primary_vars: Liste der primären Variablen (PH, Temperatur, etc.)
        flow_vars: Liste der Durchflussvariablen
        title: Titel des Dashboards
        time_range: Zeitraum ('day', 'week', 'custom')
        thresholds: Dictionary mit Grenzwerten für Variablen {variable_name: threshold_value}
        
    Returns:
        Plotly-Figur mit dem Dashboard
    """
    if data.empty:
        # Leeres Diagramm zurückgeben
        fig = go.Figure()
        fig.update_layout(
            title=title,
            height=700,
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
    
    # Subplots erstellen
    n_rows = 2 if flow_vars else 1
    fig = make_subplots(
        rows=n_rows, cols=1,
        subplot_titles=([f"Telemetrie-Daten ({time_range})"] +
                        ([f"Durchflussraten ({time_range})"] if flow_vars else [])),
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3] if flow_vars else [1]
    )
    
    # Farben für die verschiedenen Variablen
    color_map = {
        'PH_58': '#0066cc',
        'Trübung_Zulauf': '#ff9900',
        'Water_Level': '#00cc66',
        'Flow_Rate_2': '#cc0066',
        'ARA_Flow': '#9933cc',
        'Pumpdauer': '#ff6600'
    }
    
    # Standardfarben für nicht definierte Variablen
    default_colors = px.colors.qualitative.Plotly
    
    # Telemetrie-Daten hinzufügen (oberer Plot)
    for i, var in enumerate(primary_vars):
        if var in data.columns:
            # Farbe auswählen
            color = color_map.get(var, default_colors[i % len(default_colors)])
            
            # Linie hinzufügen
            fig.add_trace(
                go.Scatter(
                    x=data['Time'],
                    y=data[var],
                    mode='lines',
                    name=var,
                    line=dict(color=color, width=2),
                    hovertemplate="%{y:.2f}<extra>%{x}</extra>"
                ),
                row=1, col=1
            )
            
            # Wenn ein Grenzwert definiert ist, Werte oberhalb des Grenzwerts hervorheben
            threshold = thresholds.get(var, None)
            if threshold is not None:
                # Maske für Werte, die den Grenzwert überschreiten
                mask = data[var] > threshold
                
                if mask.any():
                    # Hervorhebung der Werte oberhalb des Grenzwerts
                    fig.add_trace(
                        go.Scatter(
                            x=data.loc[mask, 'Time'],
                            y=data.loc[mask, var],
                            mode='markers',
                            marker=dict(
                                color='red',
                                size=8,
                                symbol='circle',
                                line=dict(
                                    color='black',
                                    width=1
                                )
                            ),
                            name=f"{var} > {threshold:.2f}",
                            hovertemplate="%{y:.2f} (ÜBERSCHREITUNG)<extra>%{x}</extra>"
                        ),
                        row=1, col=1
                    )
                    
                    # Horizontale Linie für den Grenzwert hinzufügen
                    fig.add_shape(
                        type="line",
                        x0=data['Time'].min(),
                        x1=data['Time'].max(),
                        y0=threshold,
                        y1=threshold,
                        line=dict(
                            color="red",
                            width=2,
                            dash="dash",
                        ),
                        row=1, col=1
                    )
    
    # Durchflussraten hinzufügen (unterer Plot, falls vorhanden)
    if flow_vars and n_rows > 1:
        for i, var in enumerate(flow_vars):
            if var in data.columns:
                # Farbe auswählen
                color = color_map.get(var, default_colors[(i + len(primary_vars)) % len(default_colors)])
                
                # Linie hinzufügen
                fig.add_trace(
                    go.Scatter(
                        x=data['Time'],
                        y=data[var],
                        mode='lines',
                        name=var,
                        line=dict(color=color, width=2),
                        hovertemplate="%{y:.2f}<extra>%{x}</extra>"
                    ),
                    row=2, col=1
                )
                
                # Wenn ein Grenzwert definiert ist, Werte oberhalb des Grenzwerts hervorheben
                threshold = thresholds.get(var, None)
                if threshold is not None:
                    # Maske für Werte, die den Grenzwert überschreiten
                    mask = data[var] > threshold
                    
                    if mask.any():
                        # Hervorhebung der Werte oberhalb des Grenzwerts
                        fig.add_trace(
                            go.Scatter(
                                x=data.loc[mask, 'Time'],
                                y=data.loc[mask, var],
                                mode='markers',
                                marker=dict(
                                    color='red',
                                    size=8,
                                    symbol='circle',
                                    line=dict(
                                        color='black',
                                        width=1
                                    )
                                ),
                                name=f"{var} > {threshold:.2f}",
                                hovertemplate="%{y:.2f} (ÜBERSCHREITUNG)<extra>%{x}</extra>"
                            ),
                            row=2, col=1
                        )
                        
                        # Horizontale Linie für den Grenzwert hinzufügen
                        fig.add_shape(
                            type="line",
                            x0=data['Time'].min(),
                            x1=data['Time'].max(),
                            y0=threshold,
                            y1=threshold,
                            line=dict(
                                color="red",
                                width=2,
                                dash="dash",
                            ),
                            row=2, col=1
                        )
    
    # Layout anpassen
    fig.update_layout(
        title=title,
        height=700,
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # X-Achsenbeschriftungen
    fig.update_xaxes(title_text="Zeit", row=n_rows, col=1)
    
    # Y-Achsenbeschriftungen
    fig.update_yaxes(title_text="Wert", row=1, col=1)
    if n_rows > 1:
        fig.update_yaxes(title_text="Durchfluss (m³)", row=2, col=1)
    
    return fig 