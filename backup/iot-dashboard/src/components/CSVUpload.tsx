import React, { useState } from 'react';
import axios from 'axios';
import { API_BASE_URL } from '../services/dataService';

interface CSVUploadProps {
  onUploadSuccess: (data: any) => void;
}

const CSVUpload: React.FC<CSVUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setFile(file);
      setError(null);
      setSuccess(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Bitte wählen Sie eine CSV-Datei aus');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload-csv`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      console.log('Upload successful:', response.data);
      setFile(null);
      setSuccess(true);
      
      // Hole die Daten der neu hochgeladenen Woche
      const weekResponse = await axios.get(`${API_BASE_URL}/weeks/${response.data.id}`);
      onUploadSuccess(weekResponse.data);
      
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Upload fehlgeschlagen. Bitte versuchen Sie es erneut.');
      setSuccess(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-xl font-semibold mb-4">CSV-Datei importieren</h2>
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => document.getElementById('csv-file-input')?.click()}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            CSV-Datei auswählen
          </button>
          <input
            id="csv-file-input"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="hidden"
          />
          {file && (
            <span className="text-sm text-gray-600">
              {file.name}
            </span>
          )}
        </div>
        
        {error && (
          <div className="text-red-600 text-sm">{error}</div>
        )}
        
        {success && (
          <div className="text-green-600 text-sm">✓ Datei erfolgreich hochgeladen</div>
        )}
        
        <button
          onClick={handleUpload}
          disabled={!file || loading}
          className={`w-full py-2 px-4 rounded text-white font-medium
            ${!file || loading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
            }`}
        >
          {loading ? 'Wird hochgeladen...' : 'Importieren'}
        </button>
      </div>
    </div>
  );
};

export default CSVUpload; 