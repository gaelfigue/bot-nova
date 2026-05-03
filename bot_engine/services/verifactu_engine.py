"""
NOVA_CORE — VeriFactu Engine (AEAT)
Generador de archivos XML estructurados para el envío de registros de facturación
a la Agencia Tributaria Española.

Actualmente opera en MODO SANDBOX (simulación) guardando los XML en local.
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
from pathlib import Path
from datetime import datetime

from bot_engine.config import BASE_DIR
from bot_engine.services.legal_engine import InvoiceResult
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.verifactu")

VERIFACTU_DIR = BASE_DIR / "data" / "verifactu"
VERIFACTU_DIR.mkdir(parents=True, exist_ok=True)

# MODO SANDBOX: Si es True, no intenta enviar a la AEAT ni firmar con certificado.
# Solo genera el XML y lo guarda.
SANDBOX_MODE = True


def _format_date_aeat(date_str: str) -> str:
    """Convierte DD/MM/YYYY a YYYY-MM-DD para el XML."""
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d")


def generate_verifactu_xml(invoice: InvoiceResult, dj_name: str, dj_nif: str) -> Path:
    """
    Genera el archivo XML de Registro de Alta de Factura según el esquema
    VeriFactu de la AEAT.
    """
    logger.info(f"Generando XML VeriFactu para factura {invoice.invoice_number}")

    # Elemento Raíz (Namespace simulado de la AEAT)
    root = ET.Element("RegFactuSistemaFacturacion", xmlns="https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroLR.xsd")

    # Cabecera
    cabecera = ET.SubElement(root, "Cabecera")
    obligado = ET.SubElement(cabecera, "ObligadoEmision")
    ET.SubElement(obligado, "NombreRazon").text = dj_name
    ET.SubElement(obligado, "NIF").text = dj_nif

    # Registro de Alta
    registro_alta = ET.SubElement(root, "RegistroAlta")
    
    # ID Factura
    id_factura = ET.SubElement(registro_alta, "IDFactura")
    ET.SubElement(id_factura, "IDEmisorFactura").text = dj_nif
    ET.SubElement(id_factura, "NumSerieFactura").text = invoice.invoice_number
    ET.SubElement(id_factura, "FechaExpedicionFactura").text = _format_date_aeat(invoice.date)

    # Detalle de la factura
    factura = ET.SubElement(registro_alta, "Factura")
    ET.SubElement(factura, "TipoFactura").text = "F1"  # Factura ordinaria
    
    # Cliente (Receptor)
    destinatario = ET.SubElement(factura, "Destinatarios")
    dest_detalle = ET.SubElement(destinatario, "IDDestinatario")
    ET.SubElement(dest_detalle, "NombreRazon").text = invoice.venue_name
    ET.SubElement(dest_detalle, "NIF").text = invoice.venue_cif

    # Desglose (IVA, Base Imponible)
    desglose = ET.SubElement(factura, "Desglose")
    detalle_iva = ET.SubElement(desglose, "DetalleIVA")
    ET.SubElement(detalle_iva, "BaseImponible").text = f"{invoice.base_imponible:.2f}"
    ET.SubElement(detalle_iva, "TipoImpositivo").text = "21.00"
    ET.SubElement(detalle_iva, "CuotaRepercutida").text = f"{invoice.iva_amount:.2f}"

    # Retención IRPF y Comisión Nova Club (se añaden como metadatos/conceptos)
    conceptos = ET.SubElement(factura, "ConceptosAdicionales")
    ET.SubElement(conceptos, "RetencionIRPF").text = f"{invoice.irpf_amount:.2f}"
    ET.SubElement(conceptos, "ComisionGestion").text = f"{invoice.comision_amount:.2f}"

    # Totales
    ET.SubElement(factura, "CuotaTotal").text = f"{invoice.iva_amount:.2f}"
    ET.SubElement(factura, "ImporteTotal").text = f"{invoice.gross_amount:.2f}"

    # Huella (Hash encadenado)
    huella = ET.SubElement(registro_alta, "Huella")
    ET.SubElement(huella, "Hash").text = invoice.invoice_hash

    # Sistema Informático
    sistema = ET.SubElement(registro_alta, "SistemaInformatico")
    ET.SubElement(sistema, "Nombre").text = "NOVA_CORE Engine"
    ET.SubElement(sistema, "Version").text = "1.0.0"

    # Dar formato bonito al XML (Indentación)
    xml_str = ET.tostring(root, encoding="utf-8", method="xml")
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")

    # Guardar en local
    xml_filename = f"VERIFACTU_{invoice.invoice_number}.xml"
    xml_path = VERIFACTU_DIR / xml_filename

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    logger.info(f"XML VeriFactu guardado localmente: {xml_path.name}")
    return xml_path


def send_to_aeat(xml_path: Path) -> bool:
    """
    Función que simula el envío a Hacienda.
    Cuando la empresa esté dada de alta, aquí se implementará la conexión SOAP
    usando un Certificado Digital FNMT.
    """
    if SANDBOX_MODE:
        logger.info(f"[SANDBOX] Envío a AEAT simulado con éxito para: {xml_path.name}")
        return True
    else:
        # TODO: Implementar firma XMLDSig y request POST a la API de la AEAT
        raise NotImplementedError("El entorno de producción AEAT no está configurado.")

