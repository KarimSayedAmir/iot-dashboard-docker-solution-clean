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
                   date_format: str = "%d/%m/%Y %H:%M") -> pd.DataFrame:
    """
    Parst CSV-Daten aus einer Datei oder einem String.
    
    Args:
        file_content: CSV-Daten als String, Bytes oder BytesIO-Objekt
        date_format: Format der Zeitstempel in den Daten
        
    Returns:
        DataFrame mit den verarbeiteten Daten
    """
    try:
        # Daten als String konvertieren
        if isinstance(file_content, bytes):
            content_str = file_content.decode('utf-8')
        elif isinstance(file_content, io.BytesIO):
            content_str = file_content.getvalue().decode('utf-8')
        else:
            content_str = file_content
            
        # Zeilen der CSV-Datei lesen
        lines = content_str.strip().split('\n')
        
        # Prüfen, ob es sich um das spezielle Format mit Metadaten handelt
        if len(lines) > 5 and ',' in lines[0] and lines[0].startswith('Customer'):
            # Metadaten extrahieren (für später)
            metadata = {}
            for i in range(5):
                if ',' in lines[i]:
                    key, value = lines[i].split(',', 1)
                    metadata[key.strip()] = value.strip()
            
            # DataFrame aus den tatsächlichen Daten erstellen (ab Zeile 6)
            data_content = '\n'.join(lines[5:])
            df = pd.read_csv(io.StringIO(data_content))
            
            # Zeitstempel-Spalte finden und konvertieren
            time_column = 'Time' if 'Time' in df.columns else df.columns[0]
            
            try:
                df[time_column] = pd.to_datetime(df[time_column], format=date_format)
            except:
                try:
                    # Flexibler parsen, wenn das spezifizierte Format nicht funktioniert
                    df[time_column] = pd.to_datetime(df[time_column])
                except Exception as e:
                    print(f"Fehler beim Parsen der Zeitstempel: {e}. Behalte Originalformat bei.")
            
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
        else:
            # Standard CSV-Parsing ohne spezielle Metadaten
            df = pd.read_csv(io.StringIO(content_str))
        
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

def calculate_pump_runtime(data: pd.DataFrame, pump_variables: List[str]) -> Dict[str, float]:
    """
    Berechnet die Laufzeit der Pumpen in Stunden.
    
    Args:
        data: DataFrame mit den Daten
        pump_variables: Liste der Variablen, die den Pumpenstatus repräsentieren
        
    Returns:
        Dictionary mit Laufzeiten für jede Pumpe und Gesamtlaufzeit
    """
    if data.empty or not pump_variables:
        return {"total_runtime": 0}
    
    # Ergebnis-Dictionary initialisieren
    result = {var: 0.0 for var in pump_variables}
    result["total_runtime"] = 0.0
    
    # Zeitintervall zwischen Messungen berechnen (in Stunden)
    if not pd.api.types.is_datetime64_any_dtype(data['Time']):
        try:
            data['Time'] = pd.to_datetime(data['Time'])
        except:
            print("Fehler beim Konvertieren der Zeitstempel für die Laufzeitberechnung.")
            return result
            
    # Kopie der Daten erstellen und sortieren
    sorted_data = data.copy().sort_values('Time')
    
    # Prüfen, ob die Pumpenvariablen existieren, und fehlende Werte als "aus" (0) behandeln
    for var in pump_variables:
        if var not in sorted_data.columns:
            print(f"Warnung: Variable {var} nicht in den Daten gefunden.")
            continue
        
        # Fehlende Werte durch 0 ersetzen (Pumpe ist aus wenn kein Wert)
        sorted_data[var] = sorted_data[var].fillna(0)
        
        # Boolean-Werte in Integer (0/1) umwandeln
        if sorted_data[var].dtype == 'bool':
            sorted_data[var] = sorted_data[var].astype(int)
        elif sorted_data[var].dtype == 'object':
            # Versuche, String-Werte 'true'/'false' zu konvertieren
            try:
                # Zuerst prüfen, ob es sich um 'true'/'false' Strings handelt
                if sorted_data[var].astype(str).str.lower().str.contains('true').any() or \
                   sorted_data[var].astype(str).str.lower().str.contains('false').any():
                    sorted_data[var] = sorted_data[var].astype(str).str.lower().str.contains('true').astype(int)
                else:
                    # Wenn nicht, versuchen als Zahl zu interpretieren
                    sorted_data[var] = pd.to_numeric(sorted_data[var], errors='coerce').fillna(0)
            except Exception as e:
                print(f"Warnung: Konnte Variable {var} nicht konvertieren. Fehler: {e}")
                sorted_data[var] = 0  # Fallback: alle Werte auf 0 setzen
    
    # Zeitliche Differenzen berechnen (in Stunden)
    time_diffs = sorted_data['Time'].diff().dt.total_seconds() / 3600  # in Stunden
    
    # Standardwert für das erste Intervall (falls nicht verfügbar)
    avg_interval = time_diffs.mean()
    if pd.isna(avg_interval) or avg_interval == 0:
        # Wenn nicht berechenbar, nehmen wir einen Standardwert von 15 Minuten
        avg_interval = 0.25  # 15 Minuten in Stunden
    
    # Ersetze NaN im ersten Eintrag mit dem Durchschnittsintervall
    time_diffs.iloc[0] = avg_interval
    
    # Für jede Pumpenvariable
    for var in pump_variables:
        if var in sorted_data.columns:
            # Ersetze NaN-Werte mit 0 (nicht laufend)
            if sorted_data[var].isna().any():
                sorted_data[var] = sorted_data[var].fillna(0)
            
            # Debug-Ausgabe für Datentypen und einzigartige Werte
            print(f"Variable {var} hat Datentyp: {sorted_data[var].dtype}")
            print(f"Einzigartige Werte in {var}: {sorted_data[var].unique()}")
            
            # Prüfe, ob die Variable binär ist (0/1) oder numerisch
            if sorted_data[var].dtype in ('bool', 'int64', 'int32', 'float64'):
                # Betrachte Werte > 0 als laufend, berechne die tatsächliche Laufzeit
                is_running = sorted_data[var] > 0
                runtime = (is_running * time_diffs).sum()
                
                # Debug-Ausgabe
                print(f"Anzahl Datenpunkte für {var}: {len(sorted_data)}")
                print(f"Anzahl 'AN'-Datenpunkte: {is_running.sum()}")
                print(f"Berechnete Laufzeit: {runtime:.2f} Stunden")
                
                result[var] = runtime
                result["total_runtime"] += runtime
            else:
                print(f"Warnung: Variable {var} hat unerwarteten Datentyp: {sorted_data[var].dtype}")
    
    return result

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

def calculate_aggregates(data: pd.DataFrame, pump_runtimes: Dict = None) -> Dict:
    """
    Berechnet Aggregate (tägliche und wöchentliche Zusammenfassungen) aus den Daten.
    
    Args:
        data: DataFrame mit den Daten
        pump_runtimes: Optional, Dictionary mit bereits berechneten Pumpenlaufzeiten
        
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
    
    # Pumpdauer - verwende übergebene Pumpenlaufzeiten, wenn verfügbar
    if pump_runtimes is not None and "total_runtime" in pump_runtimes:
        weekly_agg['pumpDuration'] = pump_runtimes["total_runtime"]
    else:
        # Fallback zur alten Berechnung
        pump_col = next((col for col in numeric_cols if 'Pump' in col and 'dauer' in col), None)
        if pump_col:
            weekly_agg['pumpDuration'] = data[pump_col].sum()
        else:
            # Versuche, Pumpen nach ihrem Namen zu erkennen
            pump_cols = [col for col in data.columns if 'Pump' in col]
            if pump_cols:
                # Versuche, die Pumpenlaufzeit selbst zu berechnen
                total_runtime = 0.0
                for col in pump_cols:
                    if col in data.columns:
                        # Für numerische Daten
                        if data[col].dtype in ('float64', 'int64', 'bool'):
                            # Betrachte Werte > 0 als "an"
                            is_running = data[col] > 0
                            if is_running.sum() > 0:
                                # Näherungsweise Berechnung, wenn keine Zeitintervalle bekannt sind
                                # Annahme: 1 Messwert entspricht ca. 15 Minuten (0.25 Stunden)
                                total_runtime += is_running.sum() * 0.25
                weekly_agg['pumpDuration'] = total_runtime
            else:
                weekly_agg['pumpDuration'] = 0
    
    # Gesamtmengen für Durchfluss
    # Aktualisierte Flow-Berechnung für die spezifischen Spalten Flow_Rate_59 und ARA_Flow
    if 'Flow_Rate_59' in data.columns:
        # Filtere negative Werte und NaN heraus für realistischere Summen
        valid_flow = data['Flow_Rate_59'].replace([np.inf, -np.inf], np.nan).dropna()
        valid_flow = valid_flow[valid_flow >= 0]  # Nur positive Werte
        weekly_agg['totalFlowGalgenkanal'] = valid_flow.sum()
    else:
        # Fallback für andere Flow-Spalten mit "Galgen" im Namen
        galgen_flow_col = next((col for col in numeric_cols if 'Flow' in col and ('Galgen' in col or '59' in col)), None)
        if galgen_flow_col:
            valid_flow = data[galgen_flow_col].replace([np.inf, -np.inf], np.nan).dropna()
            valid_flow = valid_flow[valid_flow >= 0]
            weekly_agg['totalFlowGalgenkanal'] = valid_flow.sum()
        else:
            weekly_agg['totalFlowGalgenkanal'] = 0
    
    if 'ARA_Flow' in data.columns:
        # Filtere negative Werte und NaN heraus für realistischere Summen
        valid_flow = data['ARA_Flow'].replace([np.inf, -np.inf], np.nan).dropna()
        valid_flow = valid_flow[valid_flow >= 0]  # Nur positive Werte
        weekly_agg['totalFlowARA'] = valid_flow.sum()
    else:
        # Fallback für andere Flow-Spalten mit "ARA" im Namen
        ara_flow_col = next((col for col in numeric_cols if 'Flow' in col and 'ARA' in col), None)
        if ara_flow_col:
            valid_flow = data[ara_flow_col].replace([np.inf, -np.inf], np.nan).dropna()
            valid_flow = valid_flow[valid_flow >= 0]
            weekly_agg['totalFlowARA'] = valid_flow.sum()
        else:
            weekly_agg['totalFlowARA'] = 0
    
    # Spezifische Flow-Werte für Gerät 0058 und 0059 (falls vorhanden)
    if 'Flow_58' in data.columns:
        valid_flow = data['Flow_58'].replace([np.inf, -np.inf], np.nan).dropna()
        valid_flow = valid_flow[valid_flow >= 0]
        weekly_agg['totalFlow58'] = valid_flow.sum()
    
    if 'Flow_59' in data.columns:
        valid_flow = data['Flow_59'].replace([np.inf, -np.inf], np.nan).dropna()
        valid_flow = valid_flow[valid_flow >= 0]
        weekly_agg['totalFlow59'] = valid_flow.sum()
    
    result["weeklyAggregates"] = weekly_agg
    
    return result 