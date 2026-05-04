"""
NOVA_CORE — Contract Engine
Generación de contratos de actuación (Performance Agreements) para DJs.
"""

import os
from fpdf import FPDF
from datetime import datetime
from pathlib import Path
from bot_engine.config import BASE_DIR

class ContractPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "PERFORMANCE AGREEMENT", ln=True, align="C")
        self.set_line_width(0.5)
        self.line(10, 20, 200, 20)
        self.ln(10)

    def footer(self):
        # Disclaimer Legal Crítico
        self.set_y(-25)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        disclaimer = (
            "Este documento es una plantilla generada por NOVA_CORE. "
            "NOVA CLUB C.B. no asume responsabilidad legal sobre el acuerdo entre las partes. "
            "Para validez legal, este documento debe ser firmado por ambas partes."
        )
        self.multi_cell(0, 5, disclaimer, align='C')
        self.set_y(-15)
        self.cell(0, 10, f'Página {self.page_no()}', align='C')

def generate_performance_contract(artist_name: str, venue_name: str, event_date: str, fee: float, currency: str = "EUR") -> Path:
    """Genera un contrato legal básico de actuación."""
    pdf = ContractPDF()
    pdf.add_page()
    
    # Datos del acuerdo
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "1. PARTIES", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, f"This agreement is made on {datetime.now().strftime('%d/%m/%Y')} between:\n"
                         f"ARTIST: {artist_name}\n"
                         f"PROMOTER/VENUE: {venue_name}\n")
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "2. EVENT DETAILS", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, f"DATE: {event_date}\n"
                         f"PERFORMANCE FEE: {fee} {currency}\n"
                         f"DEPOSIT: 50% due upon signing (recommended)\n")

    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "3. OBLIGATIONS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, "• The Artist agrees to provide professional DJ services for the specified duration.\n"
                         "• The Promoter agrees to provide the technical equipment specified in the Artist's Technical Rider.\n"
                         "• The Promoter is responsible for the safety of the Artist and their equipment.\n"
                         "• Any cancellation by the Promoter within 14 days of the event will result in the full fee being payable.\n")

    pdf.ln(15)
    # Firmas
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(90, 10, "__________________________", ln=0)
    pdf.cell(90, 10, "__________________________", ln=1)
    pdf.cell(90, 5, "Artist Signature", ln=0)
    pdf.cell(90, 5, "Promoter Signature", ln=1)

    out_dir = BASE_DIR / "data" / "contracts"
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"Contract_{artist_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    file_path = out_dir / filename
    pdf.output(str(file_path))
    
    return file_path
