"""
Datenbankmodul für das IoT-Dashboard.
Enthält Funktionen für die Datenbankinteraktion mit SQLite.
"""

import sqlite3
import os
import pandas as pd
import json
from typing import Dict, List, Optional, Union
from datetime import datetime


# Pfad zur Datenbank
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'iot_dashboard.db')

def init_db():
    """
    Initialisiert die Datenbank mit den notwendigen Tabellen.
    """
    # Stelle sicher, dass das Verzeichnis existiert
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Erstelle Weeks-Tabelle
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS weeks (
        id TEXT PRIMARY KEY,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        data_type TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        last_modified INTEGER NOT NULL
    )
    ''')
    
    # Erstelle IoT-Daten-Tabelle
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS iot_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_id TEXT NOT NULL,
        time TEXT NOT NULL,
        data TEXT NOT NULL,
        FOREIGN KEY (week_id) REFERENCES weeks (id) ON DELETE CASCADE
    )
    ''')
    
    # Erstelle manuelle Korrekturen-Tabelle
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS manual_corrections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_id TEXT NOT NULL,
        pump_duration REAL,
        total_flow_ara REAL,
        total_flow_galgenkanal REAL,
        notes TEXT,
        created_at INTEGER NOT NULL,
        FOREIGN KEY (week_id) REFERENCES weeks (id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()

def save_week_data(start_date: str, end_date: str, data_type: str, 
                  iot_data: pd.DataFrame, manual_corrections: List[Dict] = None) -> str:
    """
    Speichert Wochendaten in der Datenbank.
    
    Args:
        start_date: Startdatum der Woche
        end_date: Enddatum der Woche
        data_type: Datentyp ('telemetry', 'totalAmount', 'both')
        iot_data: DataFrame mit IoT-Daten
        manual_corrections: Liste mit manuellen Korrekturen
        
    Returns:
        ID der gespeicherten Woche
    """
    # Initialisiere Datenbank, falls noch nicht geschehen
    if not os.path.exists(DB_PATH):
        init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Generiere Week-ID
    week_id = f"week_{start_date.replace('-', '')}_to_{end_date.replace('-', '')}"
    
    # Aktueller Zeitstempel
    now = int(datetime.now().timestamp())
    
    # Speichere Week-Daten
    cursor.execute('''
    INSERT OR REPLACE INTO weeks (id, start_date, end_date, data_type, created_at, last_modified)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (week_id, start_date, end_date, data_type, now, now))
    
    # Lösche vorhandene IoT-Daten für diese Woche
    cursor.execute('DELETE FROM iot_data WHERE week_id = ?', (week_id,))
    
    # Speichere IoT-Daten
    for _, row in iot_data.iterrows():
        # Konvertiere Zeitstempel in String
        if pd.api.types.is_datetime64_any_dtype(row['Time']):
            time_str = row['Time'].strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = str(row['Time'])
        
        # Erstelle Dictionary aus den restlichen Spalten
        data_dict = {col: float(row[col]) if pd.notna(row[col]) else None 
                    for col in row.index if col != 'Time'}
        
        # Speichere in Datenbank
        cursor.execute('''
        INSERT INTO iot_data (week_id, time, data)
        VALUES (?, ?, ?)
        ''', (week_id, time_str, json.dumps(data_dict)))
    
    # Speichere manuelle Korrekturen, falls vorhanden
    if manual_corrections:
        # Lösche vorhandene Korrekturen
        cursor.execute('DELETE FROM manual_corrections WHERE week_id = ?', (week_id,))
        
        for correction in manual_corrections:
            cursor.execute('''
            INSERT INTO manual_corrections 
            (week_id, pump_duration, total_flow_ara, total_flow_galgenkanal, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                week_id, 
                correction.get('pump_duration'), 
                correction.get('total_flow_ara'), 
                correction.get('total_flow_galgenkanal'),
                correction.get('notes', ''),
                now
            ))
    
    conn.commit()
    conn.close()
    
    return week_id

def get_all_weeks() -> List[Dict]:
    """
    Gibt alle gespeicherten Wochen zurück.
    
    Returns:
        Liste mit Wochendaten
    """
    if not os.path.exists(DB_PATH):
        init_db()
        return []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, start_date, end_date, data_type, created_at, last_modified
    FROM weeks
    ORDER BY start_date DESC
    ''')
    
    weeks = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return weeks

def get_week_data(week_id: str) -> Optional[Dict]:
    """
    Holt Wochendaten aus der Datenbank.
    
    Args:
        week_id: ID der Woche
        
    Returns:
        Dictionary mit Wochendaten oder None, wenn nicht gefunden
    """
    if not os.path.exists(DB_PATH):
        init_db()
        return None
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Hole Wochendaten
    cursor.execute('''
    SELECT id, start_date, end_date, data_type, created_at, last_modified
    FROM weeks
    WHERE id = ?
    ''', (week_id,))
    
    week_row = cursor.fetchone()
    
    if not week_row:
        conn.close()
        return None
    
    week_data = dict(week_row)
    
    # Hole IoT-Daten
    cursor.execute('''
    SELECT time, data
    FROM iot_data
    WHERE week_id = ?
    ORDER BY time
    ''', (week_id,))
    
    iot_data_rows = cursor.fetchall()
    
    # Konvertiere in DataFrame
    iot_data_list = []
    for row in iot_data_rows:
        data_dict = json.loads(row['data'])
        data_dict['Time'] = row['time']
        iot_data_list.append(data_dict)
    
    if iot_data_list:
        iot_df = pd.DataFrame(iot_data_list)
        # Konvertiere Zeitstempel
        iot_df['Time'] = pd.to_datetime(iot_df['Time'])
        # In Liste von Dicts umwandeln für JSON-Serialisierung
        week_data['iotData'] = iot_df.to_dict('records')
    else:
        week_data['iotData'] = []
    
    # Hole manuelle Korrekturen
    cursor.execute('''
    SELECT id, pump_duration, total_flow_ara, total_flow_galgenkanal, notes, created_at
    FROM manual_corrections
    WHERE week_id = ?
    ORDER BY created_at DESC
    ''', (week_id,))
    
    corrections = [dict(row) for row in cursor.fetchall()]
    week_data['manualCorrections'] = corrections
    
    conn.close()
    
    return week_data

def delete_week(week_id: str) -> bool:
    """
    Löscht eine Woche aus der Datenbank.
    
    Args:
        week_id: ID der zu löschenden Woche
        
    Returns:
        True, wenn erfolgreich, sonst False
    """
    if not os.path.exists(DB_PATH):
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Lösche Woche (kaskadiert zu IoT-Daten und Korrekturen)
        cursor.execute('DELETE FROM weeks WHERE id = ?', (week_id,))
        success = cursor.rowcount > 0
        conn.commit()
        return success
    except Exception as e:
        print(f"Fehler beim Löschen der Woche: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def update_manual_corrections(week_id: str, corrections: List[Dict]) -> bool:
    """
    Aktualisiert die manuellen Korrekturen für eine Woche.
    
    Args:
        week_id: ID der Woche
        corrections: Liste mit manuellen Korrekturen
        
    Returns:
        True, wenn erfolgreich, sonst False
    """
    if not os.path.exists(DB_PATH):
        init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Lösche vorhandene Korrekturen
        cursor.execute('DELETE FROM manual_corrections WHERE week_id = ?', (week_id,))
        
        # Aktueller Zeitstempel
        now = int(datetime.now().timestamp())
        
        # Füge neue Korrekturen hinzu
        for correction in corrections:
            cursor.execute('''
            INSERT INTO manual_corrections 
            (week_id, pump_duration, total_flow_ara, total_flow_galgenkanal, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                week_id, 
                correction.get('pump_duration'), 
                correction.get('total_flow_ara'), 
                correction.get('total_flow_galgenkanal'),
                correction.get('notes', ''),
                now
            ))
        
        # Aktualisiere last_modified in der Wochen-Tabelle
        cursor.execute('''
        UPDATE weeks SET last_modified = ? WHERE id = ?
        ''', (now, week_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Fehler beim Aktualisieren der Korrekturen: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def purge_old_data(days: int = 365) -> int:
    """
    Löscht Daten, die älter als die angegebene Anzahl von Tagen sind.
    
    Args:
        days: Anzahl der Tage, nach denen Daten gelöscht werden sollen
        
    Returns:
        Anzahl der gelöschten Wochen
    """
    if not os.path.exists(DB_PATH):
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Berechne Zeitstempel für das Cutoff-Datum
        cutoff_timestamp = int((datetime.now() - pd.Timedelta(days=days)).timestamp())
        
        # Finde Wochen, die älter als der Cutoff sind
        cursor.execute('''
        SELECT id FROM weeks WHERE created_at < ?
        ''', (cutoff_timestamp,))
        
        old_weeks = [row[0] for row in cursor.fetchall()]
        
        # Lösche alte Wochen
        for week_id in old_weeks:
            cursor.execute('DELETE FROM weeks WHERE id = ?', (week_id,))
        
        conn.commit()
        return len(old_weeks)
    except Exception as e:
        print(f"Fehler beim Löschen alter Daten: {e}")
        conn.rollback()
        return 0
    finally:
        conn.close() 