import React, { useState, useRef, useEffect } from 'react';
import { IoTData, ManualData, SelectedVariables, ChartConfig } from '../types';
import DataVisualization from './DataVisualization';
import VariableSelector from './VariableSelector';
import ManualDataForm from './ManualDataForm';
import PDFExport from './PDFExport';
import CSVUpload from './CSVUpload';
import { parseCSVData, calculateAggregates, identifyOutliers, correctOutliers, filterByTimeRange } from '../utils/dataProcessing';
import { API_BASE_URL } from '../services/dataService';

interface DashboardProps {
  initialData?: string; // CSV-Daten als String
}

const Dashboard: React.FC<DashboardProps> = ({ initialData }) => {
  const [rawData, setRawData] = useState<IoTData[]>([]);
  const [processedData, setProcessedData] = useState<IoTData[]>([]);
  const [manualData, setManualData] = useState<ManualData[]>([]);
  const [selectedVariables, setSelectedVariables] = useState<SelectedVariables>({
    PH_58: true,
    Trübung_Zulauf: true,
    Water_Level: false,
    Flow_Rate_2: false,
    ARA_Flow: false,
  });
  const [timeRange, setTimeRange] = useState<'day' | 'week' | 'custom'>('week');
  const [customStartDate, setCustomStartDate] = useState<string>('');
  const [customEndDate, setCustomEndDate] = useState<string>('');
  const [fileUploaded, setFileUploaded] = useState<boolean>(!!initialData);
  const [aggregates, setAggregates] = useState<any>({ dailyAggregates: {}, weeklyAggregates: {} });
  const [availableWeeks, setAvailableWeeks] = useState<any[]>([]);
  
  const dashboardRef = useRef<HTMLDivElement>(null);

  // Verfügbare Variablen aus den Daten extrahieren
  const availableVariables = rawData.length > 0 
    ? Object.keys(rawData[0]).filter(key => key !== 'Time' && typeof rawData[0][key] === 'number')
    : [];

  // Konfigurationen für die Diagramme
  const chartConfigs: ChartConfig[] = [
    {
      type: 'line',
      variables: Object.keys(selectedVariables).filter(key => selectedVariables[key]),
      title: 'Telemetriedaten (Zeitverlauf)',
      yAxisLabel: 'Wert',
      timeRange,
      customStartDate,
      customEndDate,
    },
    {
      type: 'bar',
      variables: ['Flow_Rate_2', 'ARA_Flow'].filter(key => selectedVariables[key]),
      title: 'Wöchentliche Gesamtmengen',
      yAxisLabel: 'Durchfluss (m³)',
      timeRange,
      customStartDate,
      customEndDate,
    },
  ];

  // CSV-Datei verarbeiten
  useEffect(() => {
    if (initialData) {
      const parsedData = parseCSVData(initialData);
      setRawData(parsedData);
      
      // Berechne Aggregate
      const calculatedAggregates = calculateAggregates(parsedData);
      setAggregates(calculatedAggregates);
      
      // Filtere Daten nach Zeitraum
      const filteredData = filterByTimeRange(parsedData, timeRange, customStartDate, customEndDate);
      setProcessedData(filteredData);
    }
  }, [initialData]);

  // Daten nach Zeitraum filtern
  useEffect(() => {
    if (rawData.length > 0) {
      const filteredData = filterByTimeRange(rawData, timeRange, customStartDate, customEndDate);
      setProcessedData(filteredData);
    }
  }, [rawData, timeRange, customStartDate, customEndDate]);

  // Alle Wochen laden
  useEffect(() => {
    fetch(`${API_BASE_URL}/weeks`)
      .then(response => response.json())
      .then(weeks => {
        setAvailableWeeks(weeks);
      })
      .catch(error => {
        console.error('Error fetching weeks:', error);
      });
  }, []);

  // CSV-Datei hochladen
  const handleUploadSuccess = () => {
    // Aktualisiere die Daten nach erfolgreichem Upload
    fetch(`${API_BASE_URL}/weeks`)
      .then(response => response.json())
      .then(weeks => {
        if (weeks.length > 0) {
          // Hole die Daten der neuesten Woche
          fetch(`${API_BASE_URL}/weeks/${weeks[0].id}`)
            .then(response => response.json())
            .then(weekData => {
              setRawData(weekData.iotData);
              
              // Berechne Aggregate
              const calculatedAggregates = calculateAggregates(weekData.iotData);
              setAggregates(calculatedAggregates);
              
              // Filtere Daten nach Zeitraum
              const filteredData = filterByTimeRange(weekData.iotData, timeRange, customStartDate, customEndDate);
              setProcessedData(filteredData);
              
              setFileUploaded(true);
            });
        }
      })
      .catch(error => {
        console.error('Error fetching weeks after upload:', error);
      });
  };

  // Manuelle Daten speichern
  const handleSaveManualData = (data: ManualData) => {
    setManualData([...manualData, data]);
  };

  // Ausreißer korrigieren
  const handleCorrectOutliers = (variable: string) => {
    if (rawData.length === 0) return;
    
    const outlierIndices = identifyOutliers(rawData, variable);
    if (outlierIndices.length === 0) {
      alert(`Keine Ausreißer für ${variable} gefunden.`);
      return;
    }
    
    const correctedData = correctOutliers(rawData, variable, outlierIndices);
    setRawData(correctedData);
    
    // Aktualisiere verarbeitete Daten
    const filteredData = filterByTimeRange(correctedData, timeRange, customStartDate, customEndDate);
    setProcessedData(filteredData);
    
    // Aktualisiere Aggregate
    const calculatedAggregates = calculateAggregates(correctedData);
    setAggregates(calculatedAggregates);
    
    alert(`${outlierIndices.length} Ausreißer für ${variable} wurden korrigiert.`);
  };

  return (
    <div className="dashboard" ref={dashboardRef}>
      <header className="dashboard-header">
        <h1>IoT-Anlagen Dashboard</h1>
        <div className="logo-placeholder">OWIPEX</div>
      </header>
      
      <div className="dashboard-controls">
        <CSVUpload onUploadSuccess={handleUploadSuccess} />
        
        <div className="time-range-selector">
          <h2>Zeitraum</h2>
          <div className="time-range-options">
            <label>
              <input 
                type="radio" 
                name="timeRange" 
                value="day" 
                checked={timeRange === 'day'} 
                onChange={() => setTimeRange('day')} 
              />
              Tag
            </label>
            <label>
              <input 
                type="radio" 
                name="timeRange" 
                value="week" 
                checked={timeRange === 'week'} 
                onChange={() => setTimeRange('week')} 
              />
              Woche
            </label>
            <label>
              <input 
                type="radio" 
                name="timeRange" 
                value="custom" 
                checked={timeRange === 'custom'} 
                onChange={() => setTimeRange('custom')} 
              />
              Benutzerdefiniert
            </label>
          </div>
          
          {timeRange === 'custom' && (
            <div className="custom-date-range">
              <div className="date-input">
                <label htmlFor="startDate">Von:</label>
                <input 
                  type="date" 
                  id="startDate" 
                  value={customStartDate} 
                  onChange={(e) => setCustomStartDate(e.target.value)} 
                />
              </div>
              <div className="date-input">
                <label htmlFor="endDate">Bis:</label>
                <input 
                  type="date" 
                  id="endDate" 
                  value={customEndDate} 
                  onChange={(e) => setCustomEndDate(e.target.value)} 
                />
              </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="dashboard-content">
        <aside className="dashboard-sidebar">
          <VariableSelector 
            availableVariables={availableVariables}
            selectedVariables={selectedVariables}
            onSelectionChange={setSelectedVariables}
          />
          
          <div className="outlier-correction">
            <h2>Ausreißer korrigieren</h2>
            <div className="variable-selection">
              <select id="outlier-variable">
                {availableVariables.map(variable => (
                  <option key={variable} value={variable}>{variable}</option>
                ))}
              </select>
              <button 
                onClick={() => {
                  const select = document.getElementById('outlier-variable') as HTMLSelectElement;
                  handleCorrectOutliers(select.value);
                }}
                disabled={!fileUploaded}
                className="btn-correct"
              >
                Korrigieren
              </button>
            </div>
          </div>
          
          <div className="weekly-summary">
            <h2>Wöchentliche Zusammenfassung</h2>
            {aggregates.weeklyAggregates && (
              <div className="summary-content">
                <p><strong>Pumpdauer:</strong> {aggregates.weeklyAggregates.pumpDuration.toFixed(1)} Stunden</p>
                <p><strong>Gesamtmenge ARA:</strong> {aggregates.weeklyAggregates.totalFlowARA.toFixed(2)} m³</p>
                <p><strong>Gesamtmenge Galgenkanal:</strong> {aggregates.weeklyAggregates.totalFlowGalgenkanal.toFixed(2)} m³</p>
                <p><strong>Durchschnitt pH (58):</strong> {aggregates.weeklyAggregates.avgPH_58.toFixed(2)}</p>
                <p><strong>Max. Trübung:</strong> {aggregates.weeklyAggregates.maxTrübung_Zulauf.toFixed(2)}</p>
              </div>
            )}
          </div>
          
          <PDFExport targetRef={dashboardRef} fileName="iot-dashboard-export.pdf" />
        </aside>
        
        <main className="dashboard-main">
          {processedData.length > 0 ? (
            <>
              {chartConfigs.map((config, index) => (
                <div key={index} className="chart-wrapper">
                  <DataVisualization data={processedData} config={config} />
                </div>
              ))}
            </>
          ) : (
            <div className="no-data-message">
              <p>Keine Daten verfügbar. Bitte laden Sie eine CSV-Datei hoch.</p>
            </div>
          )}
          
          <ManualDataForm onSave={handleSaveManualData} />
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
