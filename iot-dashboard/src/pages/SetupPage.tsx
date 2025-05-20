import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { IoTData, ManualData, SelectedVariables, ChartConfig } from '../types';
import DataVisualization from '../components/DataVisualization';
import VariableSelector from '../components/VariableSelector';
import ManualDataForm from '../components/ManualDataForm';
import PDFExport from '../components/PDFExport';
import WeekSelector from '../components/WeekSelector';
import { parseCSVData, calculateAggregates, identifyOutliers, correctOutliers, filterByTimeRange } from '../utils/dataProcessing';
import { saveWeekData, updateManualCorrections, getAllWeeks, StoredWeekData } from '../services/dataService';
import CSVUpload from '../components/CSVUpload';
import '../styles/SetupPage.css';

interface SetupPageProps {}

const SetupPage: React.FC<SetupPageProps> = () => {
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
  const [fileUploaded, setFileUploaded] = useState<boolean>(false);
  const [aggregates, setAggregates] = useState<any>({
    dailyAggregates: {},
    weeklyAggregates: {
      pumpDuration: 0,
      totalFlowARA: 0,
      totalFlowGalgenkanal: 0,
      avgPH_58: 0,
      maxTrübung_Zulauf: 0
    }
  });
  const [dataType, setDataType] = useState<'telemetry' | 'totalAmount' | 'both'>('both');
  const [storedWeeks, setStoredWeeks] = useState<StoredWeekData[]>([]);
  const [selectedWeekId, setSelectedWeekId] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);
  
  const dashboardRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

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

  // Lade gespeicherte Wochen beim Start
  useEffect(() => {
    const loadStoredWeeks = async () => {
      try {
        const weeks = await getAllWeeks();
        setStoredWeeks(weeks);
      } catch (error) {
        console.error('Fehler beim Laden der gespeicherten Wochen:', error);
      }
    };

    loadStoredWeeks();
  }, []);

  // Daten nach Zeitraum filtern
  useEffect(() => {
    if (rawData.length > 0) {
      const filteredData = filterByTimeRange(rawData, timeRange, customStartDate, customEndDate);
      setProcessedData(filteredData);
    }
  }, [rawData, timeRange, customStartDate, customEndDate]);

  // CSV-Upload erfolgreich
  const handleUploadSuccess = (weekData: any) => {
    // Setze die Rohdaten
    setRawData(weekData.iotData);
    
    // Berechne Aggregate
    const calculatedAggregates = calculateAggregates(weekData.iotData);
    setAggregates(calculatedAggregates);
    
    // Setze den Zeitraum
    setTimeRange('week');
    setCustomStartDate(weekData.start_date);
    setCustomEndDate(weekData.end_date);
    
    // Filtere Daten nach Zeitraum
    const filteredData = filterByTimeRange(weekData.iotData, 'week', weekData.start_date, weekData.end_date);
    setProcessedData(filteredData);
    
    // Setze Upload-Status
    setFileUploaded(true);
    
    // Setze die Woche als ausgewählt
    setSelectedWeekId(weekData.id);
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

  // Woche in Firebase speichern
  const handleSaveWeek = async () => {
    if (rawData.length === 0 || !customStartDate || !customEndDate) {
      alert('Bitte laden Sie Daten hoch und geben Sie einen Zeitraum an.');
      return;
    }

    setIsSaving(true);
    
    try {
      const weekId = await saveWeekData(
        customStartDate,
        customEndDate,
        dataType,
        rawData,
        manualData
      );
      
      // Aktualisiere die Liste der gespeicherten Wochen
      const weeks = await getAllWeeks();
      setStoredWeeks(weeks);
      
      setSelectedWeekId(weekId);
      setSaveSuccess(true);
      
      setTimeout(() => {
        setSaveSuccess(false);
      }, 3000);
    } catch (error) {
      console.error('Fehler beim Speichern der Woche:', error);
      alert('Fehler beim Speichern der Woche. Bitte versuchen Sie es erneut.');
    } finally {
      setIsSaving(false);
    }
  };

  // Zur Ansichtsseite navigieren
  const handleViewPage = () => {
    if (selectedWeekId) {
      navigate(`/view/${selectedWeekId}`);
    } else {
      navigate('/view');
    }
  };

  return (
    <div className="setup-page" ref={dashboardRef}>
      <header className="dashboard-header">
        <h1>IoT-Anlagen Dashboard - Setup</h1>
        <div className="logo-placeholder">OWIPEX</div>
        <button 
          className="btn-view-page"
          onClick={handleViewPage}
          disabled={!fileUploaded && !selectedWeekId}
        >
          Zur Ansichtsseite
        </button>
      </header>
      
      <div className="dashboard-controls">
        <CSVUpload onUploadSuccess={handleUploadSuccess} />
        
        <div className="data-type-selector">
          <h3>Datentyp</h3>
          <div className="radio-group">
            <label>
              <input 
                type="radio" 
                name="dataType" 
                value="telemetry" 
                checked={dataType === 'telemetry'} 
                onChange={() => setDataType('telemetry')} 
              />
              Telemetriedaten
            </label>
            <label>
              <input 
                type="radio" 
                name="dataType" 
                value="totalAmount" 
                checked={dataType === 'totalAmount'} 
                onChange={() => setDataType('totalAmount')} 
              />
              Gesamtmengen
            </label>
            <label>
              <input 
                type="radio" 
                name="dataType" 
                value="both" 
                checked={dataType === 'both'} 
                onChange={() => setDataType('both')} 
              />
              Beides
            </label>
          </div>
        </div>
        
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
        
        <div className="week-storage">
          <h2>Wochenverwaltung</h2>
          {storedWeeks.length > 0 ? (
            <WeekSelector 
              weeks={storedWeeks}
              selectedWeekId={selectedWeekId}
              onSelectWeek={setSelectedWeekId}
            />
          ) : (
            <p className="no-weeks-message">Keine gespeicherten Wochen vorhanden.</p>
          )}
          <div className="storage-actions">
            <button 
              className="btn-save-week"
              onClick={handleSaveWeek}
              disabled={isSaving || !fileUploaded}
            >
              {isSaving ? 'Speichert...' : 'Aktuelle Woche speichern'}
            </button>
            {saveSuccess && <span className="save-success">✓ Erfolgreich gespeichert</span>}
          </div>
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
            {aggregates.weeklyAggregates && Object.keys(aggregates.weeklyAggregates).length > 0 ? (
              <div className="summary-content">
                <p><strong>Pumpdauer:</strong> {aggregates.weeklyAggregates.pumpDuration?.toFixed(1) || '0.0'} Stunden</p>
                <p><strong>Gesamtmenge ARA:</strong> {aggregates.weeklyAggregates.totalFlowARA?.toFixed(2) || '0.00'} m³</p>
                <p><strong>Gesamtmenge Galgenkanal:</strong> {aggregates.weeklyAggregates.totalFlowGalgenkanal?.toFixed(2) || '0.00'} m³</p>
                <p><strong>Durchschnitt pH (58):</strong> {aggregates.weeklyAggregates.avgPH_58?.toFixed(2) || '0.00'}</p>
                <p><strong>Max. Trübung:</strong> {aggregates.weeklyAggregates.maxTrübung_Zulauf?.toFixed(2) || '0.00'}</p>
              </div>
            ) : (
              <div className="summary-content">
                <p>Keine Daten verfügbar</p>
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
              <p>Keine Daten verfügbar. Bitte laden Sie eine CSV-Datei hoch oder wählen Sie eine gespeicherte Woche aus.</p>
            </div>
          )}
          
          <ManualDataForm 
            initialData={manualData.length > 0 ? manualData[manualData.length - 1] : undefined}
            onSave={handleSaveManualData} 
          />
        </main>
      </div>
    </div>
  );
};

export default SetupPage;
