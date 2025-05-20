import React from 'react';
import { StoredWeekData } from '../services/dataService';

interface WeekSelectorProps {
  weeks: StoredWeekData[];
  selectedWeekId: string | null;
  onSelectWeek: (weekId: string) => void;
}

const WeekSelector: React.FC<WeekSelectorProps> = ({ weeks, selectedWeekId, onSelectWeek }) => {
  // Sortiere Wochen nach Startdatum (neueste zuerst)
  const sortedWeeks = [...weeks].sort((a, b) => {
    const dateA = new Date(b.start_date);
    const dateB = new Date(a.start_date);
    return dateA.getTime() - dateB.getTime();
  });

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('de-DE');
  };

  const getDataTypeText = (type: 'telemetry' | 'totalAmount' | 'both') => {
    switch (type) {
      case 'telemetry':
        return 'Telemetriedaten';
      case 'totalAmount':
        return 'Gesamtmengen';
      case 'both':
        return 'Beides';
      default:
        return '';
    }
  };

  return (
    <div className="week-selector">
      <h3>Gespeicherte Wochen</h3>
      <select
        value={selectedWeekId || ''}
        onChange={(e) => onSelectWeek(e.target.value)}
        className="week-select"
        disabled={weeks.length === 0}
      >
        <option value="">
          {weeks.length === 0 ? '-- Keine Wochen verfügbar --' : '-- Woche auswählen --'}
        </option>
        {sortedWeeks.map((week) => (
          <option key={week.id} value={week.id}>
            {formatDate(week.start_date)} bis {formatDate(week.end_date)} ({getDataTypeText(week.data_type)})
          </option>
        ))}
      </select>
    </div>
  );
};

export default WeekSelector;
