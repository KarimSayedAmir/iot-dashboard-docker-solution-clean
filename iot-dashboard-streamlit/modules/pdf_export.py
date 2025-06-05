"""
PDF Export Module for IoT Dashboard
Handles the creation of PDF reports with proper unit display
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
import plotly.io as pio
import tempfile
import os
from datetime import datetime
import pandas as pd

# Import the get_unit_for_variable function from visualization module
from .visualization import get_unit_for_variable

def create_pdf_report(data: pd.DataFrame, 
                     figures: dict,
                     filename: str,
                     title: str = "IoT-Anlagen Bericht",
                     selected_variables: list = None,
                     aggregates: dict = None) -> str:
    """
    Create a PDF report with data visualizations and statistics.
    
    Args:
        data: DataFrame with the sensor data
        figures: Dictionary of plotly figures to include
        filename: Output filename for the PDF
        title: Report title
        selected_variables: List of selected variables to include
        aggregates: Dictionary of aggregate statistics
    
    Returns:
        str: Path to the generated PDF file
    """
    # Calculate page dimensions
    page_width, page_height = landscape(A4)
    margin = 15*mm
    content_width = page_width - 2*margin
    content_height = page_height - 2*margin
    
    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        rightMargin=margin,
        leftMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    # Prepare the story (content) for the PDF
    story = []
    styles = getSampleStyleSheet()
    
    # Modify existing styles
    styles['Title'].fontSize = 24
    styles['Title'].alignment = 1  # Center alignment
    styles['Title'].spaceAfter = 20
    
    # Create custom section header style
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
        spaceBefore=10,
        alignment=1  # Center alignment
    ))
    
    # Add title page
    story.append(Paragraph(title, styles['Title']))
    
    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    story.append(Paragraph(f"Erstellt am: {timestamp}", styles['Normal']))
    
    # Add summary statistics if available
    if aggregates and "weeklyAggregates" in aggregates:
        story.append(Spacer(1, 10*mm))
        story.append(Paragraph("Zusammenfassung", styles['SectionHeader']))
        metrics = aggregates["weeklyAggregates"]
        
        # Create summary table
        summary_data = [
            ["Metrik", "Wert"],
            ["Pumpdauer", f"{metrics.get('pumpDuration', 0):.1f} Stunden"],
            ["Gesamtmenge ARA", f"{metrics.get('totalFlowARA', 0):.2f} m³"],
            ["Gesamtmenge Geräte 58+59", f"{metrics.get('totalFlow5859', 0):.2f} m³"]
        ]
        
        # Add additional flow metrics if available
        if 'totalFlow58' in metrics:
            summary_data.append(["Gerät 0058 Gesamt", f"{metrics['totalFlow58']:.2f} m³"])
        if 'totalFlow59' in metrics:
            summary_data.append(["Gerät 0059 (Flow_59)", f"{metrics['totalFlow59']:.2f} m³"])
        
        # Calculate table width based on content width
        col_width = content_width / 2.2  # Slightly less than half to ensure margins
        summary_table = Table(summary_data, colWidths=[col_width, col_width])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(PageBreak())
    
    # Add figures
    for title, fig in figures.items():
        # Create a list to keep elements together on one page
        elements = []
        
        # Add section header
        elements.append(Paragraph(title, styles['SectionHeader']))
        elements.append(Spacer(1, 5*mm))
        
        # Save figure to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            # Calculate optimal image dimensions
            img_width = content_width
            img_height = content_height * 0.85  # Leave room for title
            
            # Export with high quality
            pio.write_image(fig, tmp.name, format='png', width=1500, height=800, scale=2)
            
            # Add image with calculated dimensions
            img = Image(tmp.name)
            img.drawWidth = img_width
            img.drawHeight = img_height
            elements.append(img)
        
        # Keep all elements together on one page
        story.append(KeepTogether(elements))
        
        # Only add PageBreak if this is not the last figure
        if title != list(figures.keys())[-1]:
            story.append(PageBreak())
    
    # Build the PDF
    doc.build(story)
    return filename

def export_current_view(data: pd.DataFrame,
                       figures: dict,
                       selected_variables: list,
                       aggregates: dict = None) -> str:
    """
    Export the current dashboard view to PDF.
    
    Args:
        data: DataFrame with the sensor data
        figures: Dictionary of plotly figures to include
        selected_variables: List of selected variables
        aggregates: Dictionary of aggregate statistics
    
    Returns:
        str: Path to the generated PDF file
    """
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"iot_dashboard_report_{timestamp}.pdf"
    
    # Create the PDF
    pdf_path = create_pdf_report(
        data,
        figures,
        filename,
        "IoT-Anlagen Bericht",
        selected_variables,
        aggregates
    )
    
    return pdf_path 