"""Document generation: fill the docx template with student data and convert to PDF."""
import io
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from docxtpl import DocxTemplate


def _resource_base() -> Path:
    """Base directory for bundled resources (works both in dev and PyInstaller onefile)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).parent


TEMPLATE_PATH = _resource_base() / "templates" / "contract_template.docx"

# LibreOffice binary — configurable for Windows (e.g. C:\Program Files\LibreOffice\program\soffice.exe)
SOFFICE_BIN = os.environ.get("SOFFICE_BIN", "soffice")

# Ordered contract fields with Russian labels + Excel column-matching keywords.
FIELDS = [
    {"key": "contract_number", "label": "Номер договора", "keywords": ["номер договора", "№ договора", "договор"]},
    {"key": "sign_date", "label": "Дата подписания", "keywords": ["дата подписания", "дата договора", "подписан"]},
    {"key": "order_number", "label": "Номер приказа", "keywords": ["номер приказа", "№ приказа", "приказ"]},
    {"key": "order_date", "label": "Дата приказа", "keywords": ["дата приказа"]},
    {"key": "citizenship", "label": "Гражданство", "keywords": ["гражданство"]},
    {"key": "full_name", "label": "ФИО нанимателя", "keywords": ["фио", "ф.и.о", "ф. и. о", "наниматель", "студент"]},
    {"key": "birth_date", "label": "Дата рождения", "keywords": ["дата рождения", "рождения", "д.р", "др"]},
    {"key": "room_number", "label": "Номер комнаты", "keywords": ["комната", "номер комнаты", "№ комнаты", "комнат"]},
    {"key": "contract_end_date", "label": "Срок договора (до)", "keywords": ["срок договора", "до какой", "действует до", "срок"]},
    {"key": "registration_address", "label": "Адрес регистрации", "keywords": ["адрес регистрации", "прописка", "регистрац", "адрес"]},
    {"key": "passport_number", "label": "Паспорт: номер", "keywords": ["номер паспорта", "паспорт №", "паспорт номер", "паспорт", "удостоверение"]},
    {"key": "passport_issue_date", "label": "Паспорт: дата выдачи", "keywords": ["дата выдачи", "выдачи"]},
    {"key": "passport_valid_until", "label": "Паспорт: срок действия", "keywords": ["срок действия", "действителен до", "действия паспорта"]},
    {"key": "passport_issued_by", "label": "Паспорт: кем выдан", "keywords": ["кем выдан", "выдан"]},
    {"key": "id_number", "label": "Идентификационный номер (ИИН)", "keywords": ["идентификационный", "иин", "инн", "идентификац"]},
    {"key": "phone", "label": "Номер телефона", "keywords": ["телефон", "тел.", "тел ", "phone", "моб", "контакт"]},
    {"key": "note", "label": "Дополнительно (вручную)", "keywords": ["дополнительно", "примечание"]},
]

FIELD_KEYS = [f["key"] for f in FIELDS]

# Moderation sections — custom text injected into specific clauses of the contract.
EXTRA_KEYS = [
    "extra_subject", "extra_tenant", "extra_landlord",
    "extra_liability", "extra_term", "extra_other",
]
ALL_TEMPLATE_KEYS = FIELD_KEYS + EXTRA_KEYS


def auto_map_columns(headers):
    """Return {field_key: column_header} best-guess mapping from Excel headers."""
    norm = {h: str(h).strip().lower() for h in headers}
    mapping = {}
    used = set()
    # Score every (field, column) pair by longest matched keyword; assign greedily.
    scored = []
    for field in FIELDS:
        for h in headers:
            best = 0
            for kw in field["keywords"]:
                if kw in norm[h]:
                    best = max(best, len(kw))
            if best:
                scored.append((best, field["key"], h))
    scored.sort(reverse=True)
    for _score, key, h in scored:
        if key in mapping or h in used:
            continue
        mapping[key] = h
        used.add(h)
    return mapping


def render_docx(fields: dict) -> bytes:
    tpl = DocxTemplate(str(TEMPLATE_PATH))
    context = {k: (fields.get(k) or "") for k in ALL_TEMPLATE_KEYS}
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    return buf.getvalue()


def merge_pdfs(pdf_list) -> bytes:
    """Merge multiple PDF byte-strings into a single PDF."""
    from pypdf import PdfWriter, PdfReader
    writer = PdfWriter()
    for b in pdf_list:
        reader = PdfReader(io.BytesIO(b))
        for page in reader.pages:
            writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def convert_to_pdf(docx_bytes: bytes) -> bytes:
    """Convert docx bytes to PDF using LibreOffice headless.

    Each call uses its OWN isolated LibreOffice user profile (`-env:UserInstallation`)
    so concurrent conversions (e.g. live preview firing while another request runs)
    don't collide on the shared default profile lock. A short retry adds robustness.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        docx_file = tmp_path / "contract.docx"
        docx_file.write_bytes(docx_bytes)
        profile_dir = tmp_path / "lo_profile"
        profile_uri = "file://" + str(profile_dir)

        last_err = None
        for attempt in range(2):
            try:
                subprocess.run(
                    [
                        SOFFICE_BIN,
                        "-env:UserInstallation=" + profile_uri,
                        "--headless",
                        "--norestore",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(tmp_path),
                        str(docx_file),
                    ],
                    check=True,
                    capture_output=True,
                    timeout=90,
                )
                pdf_file = tmp_path / "contract.pdf"
                if pdf_file.exists():
                    return pdf_file.read_bytes()
                last_err = RuntimeError("LibreOffice не создал PDF-файл")
            except subprocess.CalledProcessError as e:
                last_err = RuntimeError(
                    f"soffice error: {e.stderr.decode('utf-8', 'ignore')[:300]}"
                )
            time.sleep(0.6)
        raise last_err or RuntimeError("Не удалось конвертировать в PDF")
