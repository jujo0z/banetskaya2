"""Document generation: fill the docx template with student data and convert to PDF."""
import io
import subprocess
import tempfile
from pathlib import Path

from docxtpl import DocxTemplate

TEMPLATE_PATH = Path(__file__).parent / "templates" / "contract_template.docx"

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
]

FIELD_KEYS = [f["key"] for f in FIELDS]


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
    context = {k: (fields.get(k) or "") for k in FIELD_KEYS}
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    return buf.getvalue()


def convert_to_pdf(docx_bytes: bytes) -> bytes:
    """Convert docx bytes to PDF using LibreOffice headless."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        docx_file = tmp_path / "contract.docx"
        docx_file.write_bytes(docx_bytes)
        subprocess.run(
            ["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp_path), str(docx_file)],
            check=True,
            capture_output=True,
            timeout=90,
        )
        pdf_file = tmp_path / "contract.pdf"
        return pdf_file.read_bytes()
