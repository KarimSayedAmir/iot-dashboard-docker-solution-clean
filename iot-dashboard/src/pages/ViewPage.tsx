import React, { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { IoTData, SelectedVariables, ChartConfig } from '../types';
import DataVisualization from '../components/DataVisualization';
import PDFExport from '../components/PDFExport';
import { filterByTimeRange } from '../utils/dataProcessing';
import { getWeekData, StoredWeekData } from '../services/dataService';
import '../styles/ViewPage.css';

interface ViewPageProps {}

const ViewPage: React.FC<ViewPageProps> = () => {
  const { weekId } = useParams<{ weekId: string }>();
  const [weekData, setWeekData] = useState<StoredWeekData | null>(null);
  const [processedData, setProcessedData] = useState<IoTData[]>([]);
  const [selectedVariables, setSelectedVariables] = useState<SelectedVariables>({
    PH_58: true,
    Trübung_Zulauf: true,
    Water_Level: false,
    Flow_Rate_2: false,
    ARA_Flow: false,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  const dashboardRef = useRef<HTMLDivElement>(null);

  // Lade Wochendaten beim Start
  useEffect(() => {
    const loadWeekData = async () => {
      if (!weekId) {
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const data = await getWeekData(weekId);
        
        if (data) {
          setWeekData(data);
          setProcessedData(data.iotData);
          
          // Setze Variablenauswahl basierend auf dem Datentyp
          if (data.dataType === 'telemetry') {
            setSelectedVariables({
              PH_58: true,
              Trübung_Zulauf: true,
              Water_Level: true,
              Flow_Rate_2: false,
              ARA_Flow: false,
            });
          } else if (data.dataType === 'totalAmount') {
            setSelectedVariables({
              PH_58: false,
              Trübung_Zulauf: false,
              Water_Level: false,
              Flow_Rate_2: true,
              ARA_Flow: true,
            });
          }
        } else {
          setError('Die angeforderte Woche wurde nicht gefunden.');
        }
      } catch (error) {
        console.error('Fehler beim Laden der Wochendaten:', error);
        setError('Fehler beim Laden der Wochendaten. Bitte versuchen Sie es erneut.');
      } finally {
        setLoading(false);
      }
    };

    loadWeekData();
  }, [weekId]);

  // Konfigurationen für die Diagramme
  const chartConfigs: ChartConfig[] = [
    {
      type: 'line',
      variables: Object.keys(selectedVariables).filter(key => selectedVariables[key] && ['PH_58', 'Trübung_Zulauf', 'Water_Level'].includes(key)),
      title: 'Telemetriedaten (Zeitverlauf)',
      yAxisLabel: 'Wert',
      timeRange: 'week',
      customStartDate: weekData?.startDate,
      customEndDate: weekData?.endDate,
    },
    {
      type: 'bar',
      variables: Object.keys(selectedVariables).filter(key => selectedVariables[key] && ['Flow_Rate_2', 'ARA_Flow'].includes(key)),
      title: 'Wöchentliche Gesamtmengen',
      yAxisLabel: 'Durchfluss (m³)',
      timeRange: 'week',
      customStartDate: weekData?.startDate,
      customEndDate: weekData?.endDate,
    },
  ];

  return (
    <div className="view-page" ref={dashboardRef}>
      <header className="dashboard-header">
        <h1>IoT-Anlagen Dashboard - Ansicht</h1>
        <div className="logo-placeholder">OWIPEX</div>
        <Link to="/" className="btn-setup-page">
          Zurück zum Setup
        </Link>
      </header>
      
      {loading ? (
        <div className="loading-message">
          <p>Daten werden geladen...</p>
        </div>
      ) : error ? (
        <div className="error-message">
          <p>{error}</p>
          <Link to="/" className="btn-return">
            Zurück zum Setup
          </Link>
        </div>
      ) : weekData ? (
        <div className="dashboard-content view-only">
          <div className="week-info">
            <h2>Wochenübersicht: {weekData.startDate} bis {weekData.endDate}</h2>
            <p>Datentyp: {
              weekData.dataType === 'telemetry' ? 'Telemetriedaten' : 
              weekData.dataType === 'totalAmount' ? 'Gesamtmengen' : 
              'Telemetriedaten und Gesamtmengen'
            }</p>
          </div>
          
          <div className="charts-container">
            {chartConfigs.map((config, index) => (
              config.variables.length > 0 && (
                <div key={index} className="chart-wrapper">
                  <DataVisualization data={processedData} config={config} />
                </div>
              )
            ))}
          </div>
          
          <div className="manual-data-summary">
            <h2>Manuelle Eingaben</h2>
            {weekData.manualCorrections && weekData.manualCorrections.length > 0 ? (
              <div className="manual-data-list">
                {weekData.manualCorrections.map((correction, index) => (
                  <div key={index} className="manual-data-item">
                    <p><strong>Pumpdauer:</strong> {correction.pumpDuration} Stunden</p>
                    <p><strong>Gesamtmenge ARA:</strong> {correction.totalFlowARA} m³</p>
                    <p><strong>Gesamtmenge Galgenkanal:</strong> {correction.totalFlowGalgenkanal} m³</p>
                    {correction.notes && <p><strong>Notizen:</strong> {correction.notes}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p>Keine manuellen Eingaben vorhanden.</p>
            )}
          </div>
          
          <div className="export-container">
            <PDFExport targetRef={dashboardRef} fileName={`iot-dashboard-${weekData.startDate}-to-${weekData.endDate}.pdf`} />
          </div>
        </div>
      ) : (
        <div className="no-data-message">
          <p>Keine Woche ausgewählt. Bitte wählen Sie eine Woche im Setup-Bereich aus.</p>
          <Link to="/" className="btn-return">
            Zurück zum Setup
          </Link>
        </div>
      )}
    </div>
  );
};

export default ViewPage;
