"""
NOVA_CORE — Legal Engine
Facturacion para DJs: calculos fiscales, PDF con hash SHA-256, SQLite.
"""
import hashlib, json, sqlite3, os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import qrcode
from fpdf import FPDF
from bot_engine.config import BASE_DIR
from bot_engine.utils.logger import setup_logger

logger = setup_logger("nova.legal")
DB_PATH = BASE_DIR / "data" / "invoices.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

EMISOR_NOMBRE = os.getenv("DJ_NOMBRE", "Nova Club DJ Services")
EMISOR_NIF = os.getenv("DJ_NIF", "00000000X")
EMISOR_DIRECCION = os.getenv("DJ_DIRECCION", "Calle Ejemplo 1, Madrid")
IRPF_RATE = 0.15
COMISION_RATE = 0.10
IVA_RATE = 0.21

@dataclass
class InvoiceData:
    venue_name: str
    venue_cif: str
    gross_amount: float
    date: str
    dj_name: str
    dj_nif: str
    dj_address: str

@dataclass
class InvoiceResult:
    invoice_number: str
    date: str
    venue_name: str
    venue_cif: str
    gross_amount: float
    base_imponible: float
    iva_amount: float
    irpf_amount: float
    comision_amount: float
    net_amount: float
    invoice_hash: str
    pdf_path: Path

def _get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL, date TEXT, venue_name TEXT,
        venue_cif TEXT, gross_amount REAL, base_imponible REAL,
        iva_amount REAL, irpf_amount REAL, comision_amount REAL,
        net_amount REAL, current_hash TEXT, prev_hash TEXT,
        created_at TEXT, user_id INTEGER)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS dj_profiles (
        user_id INTEGER PRIMARY KEY,
        dj_name TEXT,
        dj_nif TEXT,
        dj_address TEXT)""")
    conn.commit()
    return conn

def get_dj_profile(user_id: int):
    conn = _get_db()
    c = conn.execute("SELECT dj_name, dj_nif, dj_address FROM dj_profiles WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row

def save_dj_profile(user_id: int, name: str, nif: str, address: str):
    conn = _get_db()
    conn.execute("""INSERT OR REPLACE INTO dj_profiles (user_id, dj_name, dj_nif, dj_address)
        VALUES (?, ?, ?, ?)""", (user_id, name, nif, address))
    conn.commit()
    conn.close()

def _get_next_number():
    y = datetime.now().year
    conn = _get_db()
    c = conn.execute("SELECT COUNT(*) FROM invoices WHERE invoice_number LIKE ?", (f"NOVA-{y}-%",))
    n = c.fetchone()[0]
    conn.close()
    return f"NOVA-{y}-{n+1:04d}"

def _get_last_hash():
    conn = _get_db()
    c = conn.execute("SELECT current_hash FROM invoices ORDER BY id DESC LIMIT 1")
    r = c.fetchone()
    conn.close()
    return r[0] if r else "0"*64

def _save_invoice(r, prev_hash, user_id=0):
    conn = _get_db()
    conn.execute("""INSERT INTO invoices (invoice_number,date,venue_name,venue_cif,
        gross_amount,base_imponible,iva_amount,irpf_amount,comision_amount,
        net_amount,current_hash,prev_hash,created_at,user_id)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (r.invoice_number,r.date,r.venue_name,r.venue_cif,r.gross_amount,
         r.base_imponible,r.iva_amount,r.irpf_amount,r.comision_amount,
         r.net_amount,r.invoice_hash,prev_hash,datetime.now().isoformat(),user_id))
    conn.commit()
    conn.close()

def calculate_invoice(gross):
    base = round(gross / (1 + IVA_RATE), 2)
    iva = round(base * IVA_RATE, 2)
    irpf = round(base * IRPF_RATE, 2)
    comision = round(gross * COMISION_RATE, 2)
    neto = round(gross - irpf - comision, 2)
    return {"gross":gross,"base_imponible":base,"iva":iva,"irpf":irpf,"comision":comision,"neto":neto}

def compute_chain_hash(data, prev_hash):
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(f"{payload}|{prev_hash}".encode("utf-8")).hexdigest()

LOGO_PATH = BASE_DIR / "data" / "nova_logo.jpg"

class InvoicePDF(FPDF):
    def header(self):
        # Logo si existe
        if LOGO_PATH.exists():
            self.image(str(LOGO_PATH), x=10, y=8, w=18)
            self.set_x(32)
        self.set_font("Helvetica","B",22)
        self.set_text_color(0, 0, 0)
        self.cell(0,12,"NOVA CLUB",align="L")
        self.ln(8)
        if LOGO_PATH.exists():
            self.set_x(32)
        self.set_font("Helvetica","",9)
        self.set_text_color(120,120,120)
        self.cell(0,5,"DJ Management & Booking",align="L")
        self.ln(10)
        self.set_draw_color(100,50,180)
        self.set_line_width(0.8)
        self.line(10,self.get_y(),200,self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-25)
        self.set_draw_color(100,50,180)
        self.set_line_width(0.4)
        self.line(10,self.get_y(),200,self.get_y())
        self.ln(3)
        self.set_font("Helvetica","I",7)
        self.set_text_color(150,150,150)
        self.cell(0,4,"Documento generado por Nova Engine | Verifactu Ready",align="C")

def generate_pdf(inv_num, date, venue, cif, calc, chain_hash, out_dir, dj_name, dj_nif, dj_address):
    pdf = InvoicePDF()
    pdf.add_page()
    # Numero y fecha
    pdf.set_font("Helvetica","B",14)
    pdf.set_text_color(40,40,40)
    pdf.cell(100,8,f"Factura: {inv_num}")
    pdf.set_font("Helvetica","",11)
    pdf.cell(0,8,f"Fecha: {date}",align="R")
    pdf.ln(12)
    # Emisor
    pdf.set_font("Helvetica","B",10)
    pdf.set_text_color(100,50,180)
    pdf.cell(0,6,"EMISOR"); pdf.ln(6)
    pdf.set_font("Helvetica","",10)
    pdf.set_text_color(40,40,40)
    for line in [dj_name, f"NIF: {dj_nif}", dj_address]:
        pdf.cell(0,5,line); pdf.ln(5)
    pdf.ln(8)
    # Receptor
    pdf.set_font("Helvetica","B",10)
    pdf.set_text_color(100,50,180)
    pdf.cell(0,6,"CLIENTE (SALA)"); pdf.ln(6)
    pdf.set_font("Helvetica","",10)
    pdf.set_text_color(40,40,40)
    pdf.cell(0,5,venue); pdf.ln(5)
    pdf.cell(0,5,f"CIF: {cif}"); pdf.ln(12)
    # Tabla
    pdf.set_font("Helvetica","B",10)
    pdf.set_fill_color(100,50,180)
    pdf.set_text_color(255,255,255)
    pdf.cell(90,8,"  Concepto",fill=True)
    pdf.cell(50,8,"Tipo",align="C",fill=True)
    pdf.cell(50,8,"Importe",align="R",fill=True)
    pdf.ln()
    pdf.set_text_color(40,40,40)
    pdf.set_font("Helvetica","",10)
    rows = [
        ("Servicio DJ / Actuacion", "", f"{calc['gross']:.2f} EUR"),
        ("Base imponible", "", f"{calc['base_imponible']:.2f} EUR"),
        ("IVA", "21%", f"+{calc['iva']:.2f} EUR"),
        ("Retencion IRPF", "-15%", f"-{calc['irpf']:.2f} EUR"),
        ("Comision Nova Club", "-10%", f"-{calc['comision']:.2f} EUR"),
    ]
    for i,(c,t,im) in enumerate(rows):
        bg = (245,240,255) if i%2==0 else (255,255,255)
        pdf.set_fill_color(*bg)
        pdf.cell(90,7,f"  {c}",fill=True)
        pdf.cell(50,7,t,align="C",fill=True)
        pdf.cell(50,7,im,align="R",fill=True)
        pdf.ln()
    # Total neto
    pdf.ln(2)
    pdf.set_font("Helvetica","B",13)
    pdf.set_fill_color(40,40,40)
    pdf.set_text_color(255,255,255)
    pdf.cell(140,10,"  TOTAL NETO A PERCIBIR",fill=True)
    pdf.cell(50,10,f"{calc['neto']:.2f} EUR",align="R",fill=True)
    pdf.ln(15)
    # QR
    qr_data = json.dumps({"invoice":inv_num,"amount":calc["gross"],"net":calc["neto"],"hash":chain_hash[:16]})
    qr = qrcode.QRCode(version=1,box_size=6,border=2)
    qr.add_data(qr_data); qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black",back_color="white")
    qr_path = out_dir / "qr.png"
    qr_img.save(str(qr_path))
    pdf.set_font("Helvetica","B",9)
    pdf.set_text_color(100,50,180)
    pdf.cell(0,5,"VERIFICACION VERIFACTU"); pdf.ln(6)
    pdf.image(str(qr_path),x=10,y=pdf.get_y(),w=30)
    qr_y = pdf.get_y()
    pdf.set_xy(45,qr_y)
    pdf.set_font("Courier","",7)
    pdf.set_text_color(100,100,100)
    pdf.cell(0,4,f"Hash SHA-256: {chain_hash}")
    pdf.set_xy(45,qr_y+6)
    pdf.set_font("Helvetica","I",7)
    pdf.cell(0,4,"Hash encadenado con factura anterior (inmutabilidad)")
    # Save
    pdf_path = out_dir / f"{inv_num}.pdf"
    pdf.output(str(pdf_path))
    qr_path.unlink(missing_ok=True)
    return pdf_path

def create_invoice(data, user_id=0):
    logger.info(f"Generando factura: {data.venue_name} | {data.gross_amount} EUR")
    inv_num = _get_next_number()
    calc = calculate_invoice(data.gross_amount)
    prev_hash = _get_last_hash()
    chain_hash = compute_chain_hash({"number":inv_num,"date":data.date,"cif":data.venue_cif,"gross":calc["gross"],"net":calc["neto"]}, prev_hash)
    out_dir = BASE_DIR / "data" / "pdfs"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = generate_pdf(inv_num, data.date, data.venue_name, data.venue_cif, calc, chain_hash, out_dir, data.dj_name, data.dj_nif, data.dj_address)
    result = InvoiceResult(inv_num, data.date, data.venue_name, data.venue_cif,
        calc["gross"], calc["base_imponible"], calc["iva"], calc["irpf"],
        calc["comision"], calc["neto"], chain_hash, pdf_path)
    _save_invoice(result, prev_hash, user_id)
    logger.info(f"Factura {inv_num} OK | Neto: {calc['neto']} EUR | Hash: {chain_hash[:16]}...")
    return result
