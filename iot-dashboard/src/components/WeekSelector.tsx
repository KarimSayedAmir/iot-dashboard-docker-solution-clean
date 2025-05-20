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
    return new Date(b.startDate).getTime() - new Date(a.startDate).getTime();
  });

  return (
    <div className="week-selector">
      <h3>Gespeicherte Wochen</h3>
      {sortedWeeks.length > 0 ? (
        <div className="weeks-list">
          <select
            value={selectedWeekId || ''}
            onChange={(e) => onSelectWeek(e.target.value)}
            className="week-select"
          >
            <option value="">-- Woche auswählen --</option>
            {sortedWeeks.map((week) => (
              <option key={week.id} value={week.id}>
                {week.startDate} bis {week.endDate} ({
                  week.dataType === 'telemetry' ? 'Telemetrie' : 
                  week.dataType === 'totalAmount' ? 'Gesamtmengen' : 
                  'Beides'
                })
              </option>
            ))}
          </select>
        </div>
      ) : (
        <p className="no-weeks-message">Keine gespeicherten Wochen vorhanden.</p>
      )}
    </div>
  );
};

export default WeekSelector;
