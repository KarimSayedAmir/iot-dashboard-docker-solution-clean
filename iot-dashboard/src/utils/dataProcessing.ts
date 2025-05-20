import Papa from 'papaparse';
import { IoTData, ManualData } from '../types';

/**
 * Parst CSV-Daten und konvertiert sie in ein Array von IoTData-Objekten
 */
export const parseCSVData = (csvString: string): IoTData[] => {
  const result = Papa.parse(csvString, {
    header: true,
    skipEmptyLines: true,
    dynamicTyping: true,
  });

  // Entferne Duplikate basierend auf Zeitstempel
  const uniqueData: { [key: string]: IoTData } = {};
  
  result.data.forEach((row: any) => {
    // Überspringe die ersten Zeilen mit Metadaten
    if (!row.Time || typeof row.Time !== 'string') return;
    
    // Normalisiere Spaltennamen (ersetze Leerzeichen durch Unterstriche)
    const normalizedRow: any = {};
    Object.keys(row).forEach(key => {
      const normalizedKey = key.replace(/ /g, '_');
      normalizedRow[normalizedKey] = row[key];
    });
    
    uniqueData[normalizedRow.Time] = normalizedRow as IoTData;
  });

  return Object.values(uniqueData);
};

/**
 * Berechnet Tages- und Wochensummen für relevante Kennzahlen
 */
export const calculateAggregates = (data: IoTData[]): { 
  dailyAggregates: { [date: string]: any },
  weeklyAggregates: any 
} => {
  const dailyAggregates: { [date: string]: any } = {};
  const weeklyAggregates: any = {
    pumpDuration: 0,
    totalFlowARA: 0,
    totalFlowGalgenkanal: 0,
    avgPH_58: 0,
    avgPH_59: 0,
    maxTrübung_Zulauf: 0,
    minTrübung_Zulauf: Number.MAX_VALUE,
    avgTrübung_Zulauf: 0,
    dataPoints: 0,
  };

  // Gruppiere Daten nach Tagen
  data.forEach(item => {
    const date = item.Time.split(' ')[0]; // Extrahiere nur das Datum
    
    if (!dailyAggregates[date]) {
      dailyAggregates[date] = {
        date,
        pumpDuration: 0,
        flowARA: 0,
        flowGalgenkanal: 0,
        avgPH_58: 0,
        avgPH_59: 0,
        maxTrübung: 0,
        minTrübung: Number.MAX_VALUE,
        dataPoints: 0,
      };
    }

    // Tägliche Aggregate aktualisieren
    const daily = dailyAggregates[date];
    daily.dataPoints += 1;
    
    // Annahme: Flow_Rate_2 repräsentiert den Galgenkanal-Fluss
    daily.flowARA += item.ARA_Flow || 0;
    daily.flowGalgenkanal += item.Flow_Rate_2 || 0;
    
    // Pumpdauer schätzen (30 Minuten pro Datenpunkt, wenn Flow > 0)
    if ((item.Flow_Rate_1 || 0) > 0 || (item.Flow_Rate_2 || 0) > 0) {
      daily.pumpDuration += 0.5; // 30 Minuten in Stunden
    }
    
    daily.avgPH_58 += item.PH_58 || 0;
    daily.avgPH_59 += item.PH_59 || 0;
    
    daily.maxTrübung = Math.max(daily.maxTrübung, item.Trübung_Zulauf || 0);
    daily.minTrübung = Math.min(daily.minTrübung, item.Trübung_Zulauf || 0);
    
    // Wöchentliche Aggregate aktualisieren
    weeklyAggregates.dataPoints += 1;
    weeklyAggregates.totalFlowARA += item.ARA_Flow || 0;
    weeklyAggregates.totalFlowGalgenkanal += item.Flow_Rate_2 || 0;
    
    if ((item.Flow_Rate_1 || 0) > 0 || (item.Flow_Rate_2 || 0) > 0) {
      weeklyAggregates.pumpDuration += 0.5; // 30 Minuten in Stunden
    }
    
    weeklyAggregates.avgPH_58 += item.PH_58 || 0;
    weeklyAggregates.avgPH_59 += item.PH_59 || 0;
    
    weeklyAggregates.maxTrübung_Zulauf = Math.max(weeklyAggregates.maxTrübung_Zulauf, item.Trübung_Zulauf || 0);
    weeklyAggregates.minTrübung_Zulauf = Math.min(weeklyAggregates.minTrübung_Zulauf, item.Trübung_Zulauf || 0);
    weeklyAggregates.avgTrübung_Zulauf += item.Trübung_Zulauf || 0;
  });

  // Berechne Durchschnittswerte für tägliche Aggregate
  Object.values(dailyAggregates).forEach(day => {
    if (day.dataPoints > 0) {
      day.avgPH_58 /= day.dataPoints;
      day.avgPH_59 /= day.dataPoints;
    }
  });

  // Berechne Durchschnittswerte für wöchentliche Aggregate
  if (weeklyAggregates.dataPoints > 0) {
    weeklyAggregates.avgPH_58 /= weeklyAggregates.dataPoints;
    weeklyAggregates.avgPH_59 /= weeklyAggregates.dataPoints;
    weeklyAggregates.avgTrübung_Zulauf /= weeklyAggregates.dataPoints;
  }

  return { dailyAggregates, weeklyAggregates };
};

/**
 * Identifiziert Ausreißer in den Daten basierend auf statistischen Methoden
 */
export const identifyOutliers = (data: IoTData[], field: string): number[] => {
  // Extrahiere die Werte für das angegebene Feld
  const values = data.map(item => Number(item[field])).filter(val => !isNaN(val));
  
  // Berechne Quartile und IQR (Interquartile Range)
  values.sort((a, b) => a - b);
  const q1 = values[Math.floor(values.length * 0.25)];
  const q3 = values[Math.floor(values.length * 0.75)];
  const iqr = q3 - q1;
  
  // Definiere Grenzen für Ausreißer
  const lowerBound = q1 - 1.5 * iqr;
  const upperBound = q3 + 1.5 * iqr;
  
  // Finde Indizes der Ausreißer
  const outlierIndices: number[] = [];
  data.forEach((item, index) => {
    const value = Number(item[field]);
    if (!isNaN(value) && (value < lowerBound || value > upperBound)) {
      outlierIndices.push(index);
    }
  });
  
  return outlierIndices;
};

/**
 * Korrigiert Ausreißer in den Daten durch Interpolation oder feste Werte
 */
export const correctOutliers = (data: IoTData[], field: string, outlierIndices: number[]): IoTData[] => {
  const correctedData = [...data];
  
  outlierIndices.forEach(index => {
    // Finde den nächsten gültigen Wert vor dem Ausreißer
    let prevIndex = index - 1;
    while (prevIndex >= 0 && outlierIndices.includes(prevIndex)) {
      prevIndex--;
    }
    
    // Finde den nächsten gültigen Wert nach dem Ausreißer
    let nextIndex = index + 1;
    while (nextIndex < data.length && outlierIndices.includes(nextIndex)) {
      nextIndex++;
    }
    
    // Korrigiere den Ausreißer durch Interpolation oder den letzten gültigen Wert
    if (prevIndex >= 0 && nextIndex < data.length) {
      // Interpolation
      const prevValue = Number(data[prevIndex][field]);
      const nextValue = Number(data[nextIndex][field]);
      const correctedValue = (prevValue + nextValue) / 2;
      correctedData[index] = { ...correctedData[index], [field]: correctedValue };
    } else if (prevIndex >= 0) {
      // Verwende den vorherigen Wert
      correctedData[index] = { ...correctedData[index], [field]: data[prevIndex][field] };
    } else if (nextIndex < data.length) {
      // Verwende den nächsten Wert
      correctedData[index] = { ...correctedData[index], [field]: data[nextIndex][field] };
    }
  });
  
  return correctedData;
};

/**
 * Kombiniert IoT-Daten mit manuell eingegebenen Daten
 */
export const combineWithManualData = (iotData: IoTData[], manualData: ManualData[]): IoTData[] => {
  // Diese Funktion würde in einer realen Anwendung komplexer sein
  // Hier vereinfachen wir und geben nur die IoT-Daten zurück
  return iotData;
};

/**
 * Filtert Daten nach Zeitraum
 */
export const filterByTimeRange = (
  data: IoTData[], 
  timeRange: 'day' | 'week' | 'custom',
  customStartDate?: string,
  customEndDate?: string
): IoTData[] => {
  if (timeRange === 'custom' && customStartDate && customEndDate) {
    const startDate = new Date(customStartDate);
    const endDate = new Date(customEndDate);
    
    return data.filter(item => {
      const itemDate = new Date(item.Time.split(' ')[0].split('/').reverse().join('-'));
      return itemDate >= startDate && itemDate <= endDate;
    });
  }
  
  if (timeRange === 'day') {
    // Nehme den letzten Tag aus den Daten
    const dates = data.map(item => item.Time.split(' ')[0]);
    const uniqueDates = [...new Set(dates)].sort();
    const lastDate = uniqueDates[uniqueDates.length - 1];
    
    return data.filter(item => item.Time.startsWith(lastDate));
  }
  
  // Standardmäßig gib alle Daten zurück (wöchentlich)
  return data;
};

/**
 * Formatiert Daten für die Anzeige in Diagrammen
 */
export const formatForCharts = (data: IoTData[], variables: string[]): any[] => {
  return data.map(item => {
    const formattedItem: any = {
      time: item.Time,
    };
    
    variables.forEach(variable => {
      formattedItem[variable] = item[variable];
    });
    
    return formattedItem;
  });
};
