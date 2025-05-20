"""
Datenverarbeitungsmodul für das IoT-Dashboard.
Enthält Funktionen für Import, Verarbeitung und Analyse von CSV-Daten.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
import io
import os
from datetime import datetime, timedelta

def parse_csv_data(file_content: Union[str, bytes, io.BytesIO], 
                   date_format: str = "%Y-%m-%d %H:%M:%S") -> pd.DataFrame:
    """
    Parst CSV-Daten aus einer Datei oder einem String.
    
    Args:
        file_content: CSV-Daten als String, Bytes oder BytesIO-Objekt
        date_format: Format der Zeitstempel in den Daten
        
    Returns:
        DataFrame mit den verarbeiteten Daten
    """
    try:
        # CSV-Datei einlesen
        if isinstance(file_content, (str, bytes)):
            df = pd.read_csv(io.StringIO(file_content) if isinstance(file_content, str) 
                             else io.StringIO(file_content.decode('utf-8')))
        else:
            df = pd.read_csv(file_content)
        
        # Prüfen auf Zeit-Spalte
        time_column = None
        for col in ['Time', 'Zeit', 'Timestamp', 'Zeitstempel', 'Date', 'Datum']:
            if col in df.columns:
                time_column = col
                break
        
        if time_column is None:
            # Wenn keine Zeit-Spalte gefunden wurde, erste Spalte als Zeit interpretieren
            time_column = df.columns[0]
            print(f"Keine eindeutige Zeitspalte gefunden, verwende erste Spalte: {time_column}")
        
        # Zeitstempel konvertieren
        try:
            df[time_column] = pd.to_datetime(df[time_column], format=date_format)
        except:
            try:
                # Flexibler parsen, wenn das spezifizierte Format nicht funktioniert
                df[time_column] = pd.to_datetime(df[time_column])
            except:
                print(f"Fehler beim Parsen der Zeitstempel. Behalte Originalformat bei.")
        
        # Umbenennen für einheitliche Verwendung
        if time_column != 'Time':
            df = df.rename(columns={time_column: 'Time'})
        
        # Numerische Spalten identifizieren und konvertieren
        for col in df.columns:
            if col != 'Time':
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    print(f"Spalte {col} konnte nicht in numerisches Format konvertiert werden.")
        
        return df
        
    except Exception as e:
        print(f"Fehler beim Parsen der CSV-Daten: {e}")
        raise

def filter_by_time_range(data: pd.DataFrame, 
                         time_range: str = 'week',
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Filtert Daten nach einem Zeitraum.
    
    Args:
        data: DataFrame mit den Daten
        time_range: 'day', 'week', oder 'custom'
        start_date: Startdatum für benutzerdefinierten Zeitraum
        end_date: Enddatum für benutzerdefinierten Zeitraum
        
    Returns:
        DataFrame mit gefilterten Daten
    """
    if data.empty:
        return data
    
    # Sicherstellen, dass die Zeit-Spalte im richtigen Format ist
    if not pd.api.types.is_datetime64_any_dtype(data['Time']):
        try:
            data['Time'] = pd.to_datetime(data['Time'])
        except:
            print("Fehler beim Konvertieren der Zeitstempel für das Filtern.")
            return data
    
    # Nach Zeitraum filtern
    if time_range == 'day':
        # Letzten Tag filtern
        latest_date = data['Time'].max()
        one_day_ago = latest_date - timedelta(days=1)
        return data[data['Time'] >= one_day_ago]
    
    elif time_range == 'week':
        # Letzte Woche filtern
        latest_date = data['Time'].max()
        one_week_ago = latest_date - timedelta(days=7)
        return data[data['Time'] >= one_week_ago]
    
    elif time_range == 'custom' and start_date and end_date:
        # Benutzerdefinierten Zeitraum filtern
        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            # End-Datum ist inklusive, daher +1 Tag
            end_dt = end_dt + timedelta(days=1)
            return data[(data['Time'] >= start_dt) & (data['Time'] < end_dt)]
        except:
            print("Fehler beim Parsen der benutzerdefinierten Datumsangaben.")
            return data
    
    return data

def identify_outliers(data: pd.DataFrame, variable: str, method: str = 'iqr', threshold: float = 1.5) -> List[int]:
    """
    Identifiziert Ausreißer in einer Datenvariable.
    
    Args:
        data: DataFrame mit den Daten
        variable: Name der zu überprüfenden Variable
        method: Methode zur Erkennung von Ausreißern ('iqr' oder 'zscore')
        threshold: Schwellenwert für die Ausreißererkennung
        
    Returns:
        Liste der Indizes von Ausreißern
    """
    if variable not in data.columns or data.empty:
        return []
    
    # Nichtvorhandene Werte ausfiltern
    values = data[variable].dropna()
    
    if method == 'iqr':
        # IQR-Methode (Interquartile Range)
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        
        outliers = data[(data[variable] < lower_bound) | (data[variable] > upper_bound)].index.tolist()
        
    elif method == 'zscore':
        # Z-Score-Methode
        mean = values.mean()
        std = values.std()
        z_scores = abs((values - mean) / std)
        outliers = data[z_scores > threshold].index.tolist()
        
    else:
        print(f"Unbekannte Methode: {method}. Verwende IQR.")
        return identify_outliers(data, variable)
    
    return outliers

def correct_outliers(data: pd.DataFrame, variable: str, outlier_indices: List[int], 
                     method: str = 'mean') -> pd.DataFrame:
    """
    Korrigiert Ausreißer in einer Datenvariable.
    
    Args:
        data: DataFrame mit den Daten
        variable: Name der zu korrigierenden Variable
        outlier_indices: Liste der Indizes von Ausreißern
        method: Korrekturmethode ('mean', 'median', 'nearest', oder 'remove')
        
    Returns:
        DataFrame mit korrigierten Daten
    """
    if variable not in data.columns or data.empty or not outlier_indices:
        return data
    
    # Kopie erstellen, um das Original nicht zu verändern
    df = data.copy()
    
    if method == 'mean':
        # Durch Mittelwert ersetzen
        replacement_value = data[variable].mean()
        df.loc[outlier_indices, variable] = replacement_value
        
    elif method == 'median':
        # Durch Median ersetzen
        replacement_value = data[variable].median()
        df.loc[outlier_indices, variable] = replacement_value
        
    elif method == 'nearest':
        # Durch Interpolation ersetzen
        for idx in outlier_indices:
            # Suche nächstgelegene gültige Werte
            mask = ~data.index.isin(outlier_indices) & data[variable].notna()
            if not any(mask):
                # Keine gültigen Werte gefunden, verwende Median
                df.loc[idx, variable] = data[variable].median()
                continue
                
            # Berechne Distanzen zu allen anderen Punkten
            distances = abs(data.index[mask] - idx)
            nearest_idx = data.index[mask][distances.argmin()]
            df.loc[idx, variable] = data.loc[nearest_idx, variable]
            
    elif method == 'remove':
        # Ausreißer entfernen
        df = df.drop(outlier_indices)
        
    else:
        print(f"Unbekannte Methode: {method}. Keine Korrektur vorgenommen.")
        
    return df

def calculate_aggregates(data: pd.DataFrame) -> Dict:
    """
    Berechnet Aggregate (tägliche und wöchentliche Zusammenfassungen) aus den Daten.
    
    Args:
        data: DataFrame mit den Daten
        
    Returns:
        Dictionary mit berechneten Aggregaten
    """
    if data.empty:
        return {"dailyAggregates": {}, "weeklyAggregates": {}}
    
    result = {
        "dailyAggregates": {},
        "weeklyAggregates": {}
    }
    
    # Alle numerischen Spalten
    numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
    
    # Tägliche Aggregate
    data_with_date = data.copy()
    if pd.api.types.is_datetime64_any_dtype(data['Time']):
        data_with_date['Date'] = data['Time'].dt.date
    else:
        try:
            data_with_date['Time'] = pd.to_datetime(data['Time'])
            data_with_date['Date'] = data_with_date['Time'].dt.date
        except:
            print("Fehler beim Konvertieren der Zeitstempel für Aggregate.")
            return result
    
    daily_agg = data_with_date.groupby('Date')[numeric_cols].agg(['mean', 'min', 'max', 'sum']).reset_index()
    result["dailyAggregates"] = daily_agg.to_dict()
    
    # Wöchentliche Aggregate
    # Spezielle Aggregate, die für das IoT-Dashboard relevant sind
    weekly_agg = {}
    
    # Durchschnittswerte für PH_58
    if 'PH_58' in numeric_cols:
        weekly_agg['avgPH_58'] = data['PH_58'].mean()
    else:
        weekly_agg['avgPH_58'] = 0
    
    # Maximale Trübung
    trub_col = next((col for col in numeric_cols if 'Tr' in col and 'bung' in col), None)
    if trub_col:
        weekly_agg['maxTrübung_Zulauf'] = data[trub_col].max()
    else:
        weekly_agg['maxTrübung_Zulauf'] = 0
    
    # Pumpdauer
    pump_col = next((col for col in numeric_cols if 'Pump' in col and 'dauer' in col), None)
    if pump_col:
        weekly_agg['pumpDuration'] = data[pump_col].sum()
    else:
        weekly_agg['pumpDuration'] = 0
    
    # Gesamtmengen für Durchfluss
    flow_cols = [col for col in numeric_cols if 'Flow' in col or 'Durchfluss' in col]
    ara_flow_col = next((col for col in flow_cols if 'ARA' in col), None)
    galgen_flow_col = next((col for col in flow_cols if 'Galgen' in col), None)
    
    if ara_flow_col:
        weekly_agg['totalFlowARA'] = data[ara_flow_col].sum()
    else:
        weekly_agg['totalFlowARA'] = 0
        
    if galgen_flow_col:
        weekly_agg['totalFlowGalgenkanal'] = data[galgen_flow_col].sum()
    else:
        weekly_agg['totalFlowGalgenkanal'] = 0
    
    result["weeklyAggregates"] = weekly_agg
    
    return result 