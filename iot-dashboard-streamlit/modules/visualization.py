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
                           height: int = 500) -> go.Figure:
    """
    Erstellt ein Zeitreihendiagramm für die angegebenen Variablen.
    
    Args:
        data: DataFrame mit den Daten
        variables: Liste der darzustellenden Variablen
        title: Titel des Diagramms
        height: Höhe des Diagramms in Pixeln
        
    Returns:
        Plotly-Figur mit dem Zeitreihendiagramm
    """
    if data.empty or not variables:
        # Leeres Diagramm zurückgeben
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title="Zeit",
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
    
    # Filtern der Daten für die angegebenen Variablen
    plot_data = data[['Time'] + [var for var in variables if var in data.columns]]
    
    if len(plot_data.columns) <= 1:
        # Keine Daten für die ausgewählten Variablen
        fig = go.Figure()
        fig.update_layout(
            title=title,
            xaxis_title="Zeit",
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
    
    # Erstellen des Diagramms
    fig = go.Figure()
    
    for i, var in enumerate([v for v in variables if v in data.columns]):
        # Farbe auswählen
        color = color_map.get(var, default_colors[i % len(default_colors)])
        
        # Linie hinzufügen
        fig.add_trace(
            go.Scatter(
                x=plot_data['Time'],
                y=plot_data[var],
                mode='lines',
                name=var,
                line=dict(color=color, width=2),
                hovertemplate="%{y:.2f}<extra>%{x}</extra>"
            )
        )
    
    # Layout anpassen
    fig.update_layout(
        title=title,
        xaxis_title="Zeit",
        yaxis_title="Wert",
        height=height,
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
    
    return fig

def create_bar_chart(data: pd.DataFrame,
                    variables: List[str],
                    title: str = "Aggregierte Daten",
                    height: int = 500,
                    aggregate_func: str = 'sum') -> go.Figure:
    """
    Erstellt ein Balkendiagramm für die angegebenen Variablen.
    
    Args:
        data: DataFrame mit den Daten
        variables: Liste der darzustellenden Variablen
        title: Titel des Diagramms
        height: Höhe des Diagramms in Pixeln
        aggregate_func: Aggregationsfunktion ('sum', 'mean', 'max', 'min')
        
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
                  height: int = 500) -> go.Figure:
    """
    Erstellt eine Heatmap für die angegebene Variable über Zeit.
    
    Args:
        data: DataFrame mit den Daten
        variable: Name der darzustellenden Variable
        title: Titel des Diagramms
        height: Höhe des Diagramms in Pixeln
        
    Returns:
        Plotly-Figur mit der Heatmap
    """
    if data.empty or variable not in data.columns:
        # Leeres Diagramm zurückgeben
        fig = go.Figure()
        fig.update_layout(
            title=title,
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
    
    # Zeitdaten erstellen
    if not pd.api.types.is_datetime64_any_dtype(data['Time']):
        try:
            data['Time'] = pd.to_datetime(data['Time'])
        except:
            print("Fehler beim Konvertieren der Zeitstempel für die Heatmap.")
            # Leeres Diagramm zurückgeben
            fig = go.Figure()
            fig.update_layout(
                title=title,
                height=height,
                template="plotly_white"
            )
            fig.add_annotation(
                text="Fehler bei der Zeitkonvertierung",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
    
    # Tage und Stunden extrahieren
    data_with_components = data.copy()
    data_with_components['day'] = data_with_components['Time'].dt.date
    data_with_components['hour'] = data_with_components['Time'].dt.hour
    
    # Aggregieren nach Tag und Stunde
    pivot_data = data_with_components.pivot_table(
        index='day',
        columns='hour',
        values=variable,
        aggfunc='mean'
    )
    
    # Erstellen der Heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Viridis',
        hoverongaps=False,
        colorbar=dict(title=variable)
    ))
    
    # Layout anpassen
    fig.update_layout(
        title=title,
        xaxis_title="Stunde des Tages",
        yaxis_title="Datum",
        height=height,
        template="plotly_white"
    )
    
    return fig

def create_dashboard(data: pd.DataFrame, 
                    primary_vars: List[str], 
                    flow_vars: List[str],
                    title: str = "IoT-Anlagen Dashboard",
                    time_range: str = 'week') -> go.Figure:
    """
    Erstellt ein komplettes Dashboard mit mehreren Diagrammen.
    
    Args:
        data: DataFrame mit den Daten
        primary_vars: Liste der primären Variablen (für Zeitreihen)
        flow_vars: Liste der Durchflussvariablen (für Balkendiagramm)
        title: Titel des Dashboards
        time_range: Zeitraum der Daten ('day', 'week', 'custom')
        
    Returns:
        Plotly-Figur mit dem Dashboard
    """
    if data.empty:
        # Leeres Diagramm zurückgeben
        fig = go.Figure()
        fig.update_layout(
            title=title,
            height=800,
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
    
    # Erstellen des Dashboards mit 2 Zeilen und 1 Spalte
    fig = make_subplots(
        rows=2, 
        cols=1,
        subplot_titles=(
            f"Telemetriedaten ({time_range})",
            "Gesamtmengen"
        ),
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3]
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
    
    # 1. Zeitreihendiagramm hinzufügen
    for i, var in enumerate([v for v in primary_vars if v in data.columns]):
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
    
    # 2. Balkendiagramm für Gesamtmengen hinzufügen
    for i, var in enumerate([v for v in flow_vars if v in data.columns]):
        # Farbe auswählen
        color = color_map.get(var, default_colors[(i + len(primary_vars)) % len(default_colors)])
        
        # Wert berechnen
        value = data[var].sum()
        
        # Balken hinzufügen
        fig.add_trace(
            go.Bar(
                x=[var],
                y=[value],
                name=var,
                marker_color=color,
                text=[f"{value:.2f}"],
                textposition="auto"
            ),
            row=2, col=1
        )
    
    # Layout anpassen
    fig.update_layout(
        title=title,
        height=800,
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
    
    # X- und Y-Achsen beschriften
    fig.update_xaxes(title_text="Zeit", row=1, col=1)
    fig.update_yaxes(title_text="Wert", row=1, col=1)
    
    fig.update_xaxes(title_text="Variable", row=2, col=1)
    fig.update_yaxes(title_text="Gesamtmenge", row=2, col=1)
    
    return fig 