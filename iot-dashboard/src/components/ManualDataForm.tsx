import React, { useState } from 'react';
import { ManualData } from '../types';

interface ManualDataFormProps {
  initialData?: ManualData;
  onSave: (data: ManualData) => void;
}

const ManualDataForm: React.FC<ManualDataFormProps> = ({ initialData, onSave }) => {
  const [formData, setFormData] = useState<ManualData>(
    initialData || {
      weekStartDate: '',
      weekEndDate: '',
      pumpDuration: 0,
      totalFlowARA: 0,
      totalFlowGalgenkanal: 0,
      notes: '',
    }
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    // Konvertiere numerische Werte
    if (['pumpDuration', 'totalFlowARA', 'totalFlowGalgenkanal'].includes(name)) {
      setFormData({
        ...formData,
        [name]: parseFloat(value) || 0,
      });
    } else {
      setFormData({
        ...formData,
        [name]: value,
      });
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  return (
    <div className="manual-data-form">
      <h2>Manuelle Dateneingabe</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="weekStartDate">Wochenanfang:</label>
          <input
            type="date"
            id="weekStartDate"
            name="weekStartDate"
            value={formData.weekStartDate}
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="weekEndDate">Wochenende:</label>
          <input
            type="date"
            id="weekEndDate"
            name="weekEndDate"
            value={formData.weekEndDate}
            onChange={handleChange}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="pumpDuration">Pumpdauer (Stunden):</label>
          <input
            type="number"
            id="pumpDuration"
            name="pumpDuration"
            value={formData.pumpDuration}
            onChange={handleChange}
            step="0.1"
            min="0"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="totalFlowARA">Gesamtmenge ARA (m³):</label>
          <input
            type="number"
            id="totalFlowARA"
            name="totalFlowARA"
            value={formData.totalFlowARA}
            onChange={handleChange}
            step="0.01"
            min="0"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="totalFlowGalgenkanal">Gesamtmenge Galgenkanal (m³):</label>
          <input
            type="number"
            id="totalFlowGalgenkanal"
            name="totalFlowGalgenkanal"
            value={formData.totalFlowGalgenkanal}
            onChange={handleChange}
            step="0.01"
            min="0"
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="notes">Notizen:</label>
          <textarea
            id="notes"
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={4}
          />
        </div>
        
        <button type="submit" className="btn-primary">Speichern</button>
      </form>
    </div>
  );
};

export default ManualDataForm;
