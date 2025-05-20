import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

interface PDFExportProps {
  targetRef: React.RefObject<HTMLDivElement>;
  fileName?: string;
}

const PDFExport: React.FC<PDFExportProps> = ({ targetRef, fileName = 'dashboard-export.pdf' }) => {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    if (!targetRef.current) return;
    
    setIsExporting(true);
    
    try {
      const canvas = await html2canvas(targetRef.current, {
        scale: 2,
        logging: false,
        useCORS: true
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'landscape',
        unit: 'mm',
      });
      
      // Füge OWIPEX Logo hinzu (Platzhalter)
      pdf.setFontSize(10);
      pdf.text('OWIPEX', 10, 10);
      
      // Berechne Seitenverhältnis
      const imgWidth = 280;
      const imgHeight = (canvas.height * imgWidth) / canvas.width;
      
      // Füge Bild hinzu
      pdf.addImage(imgData, 'PNG', 10, 20, imgWidth, imgHeight);
      
      // Füge Datum und Seitenzahl hinzu
      const date = new Date().toLocaleDateString('de-CH');
      pdf.text(`Erstellt am: ${date}`, 10, pdf.internal.pageSize.height - 10);
      pdf.text(`Seite 1/1`, pdf.internal.pageSize.width - 20, pdf.internal.pageSize.height - 10);
      
      pdf.save(fileName);
    } catch (error) {
      console.error('PDF Export fehlgeschlagen:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="pdf-export">
      <button 
        onClick={handleExport} 
        disabled={isExporting}
        className="btn-export"
      >
        {isExporting ? 'Exportiere...' : 'Als PDF exportieren'}
      </button>
    </div>
  );
};

export default PDFExport;
