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


def render_docx(fields: dict, template_path=None) -> bytes:
    import jinja2
    tpl = DocxTemplate(str(template_path or TEMPLATE_PATH))
    context = {k: (fields.get(k) or "") for k in ALL_TEMPLATE_KEYS}
    for k, v in (fields or {}).items():
        context.setdefault(k, v or "")
    # ChainableUndefined -> unknown placeholders in custom templates render empty
    jenv = jinja2.Environment(undefined=jinja2.ChainableUndefined)
    tpl.render(context, jinja_env=jenv)
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


_FONTS_READY = False


def _ensure_fonts():
    """Register bundled Liberation Sans (Cyrillic) fonts with reportlab once."""
    global _FONTS_READY
    if _FONTS_READY:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    fonts_dir = _resource_base() / "assets" / "fonts"
    reg = fonts_dir / "LiberationSans-Regular.ttf"
    bold = fonts_dir / "LiberationSans-Bold.ttf"
    # fallback to common system paths
    if not reg.exists():
        reg = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf")
    if not bold.exists():
        bold = Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")
    try:
        if reg.exists():
            pdfmetrics.registerFont(TTFont("AppSans", str(reg)))
        if bold.exists():
            pdfmetrics.registerFont(TTFont("AppSans-Bold", str(bold)))
        _FONTS_READY = True
    except Exception:
        _FONTS_READY = False


def _font(bold=False):
    if _FONTS_READY:
        return "AppSans-Bold" if bold else "AppSans"
    return "Helvetica-Bold" if bold else "Helvetica"


def make_separator_page(index, number="", name="", size=(595.0, 842.0)):
    """A numbered divider sheet (crimson bands + big number) to split the stack."""
    from reportlab.pdfgen import canvas
    from pypdf import PdfReader

    _ensure_fonts()
    w, h = size
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(w, h))
    # crimson bands
    c.setFillColorRGB(225 / 255, 29 / 255, 72 / 255)
    band_h = h * 0.06
    c.rect(0, h * 0.66, w, band_h, stroke=0, fill=1)
    c.rect(0, h * 0.30, w, band_h, stroke=0, fill=1)
    # big number
    c.setFillColorRGB(0.12, 0.12, 0.14)
    c.setFont(_font(True), min(w, h) * 0.20)
    c.drawCentredString(w / 2, h * 0.46, f"№ {index}")
    # sub labels
    c.setFont(_font(False), 16)
    if number:
        c.drawCentredString(w / 2, h * 0.24, f"Договор: {number}")
    if name:
        c.setFont(_font(True), 18)
        c.drawCentredString(w / 2, h * 0.20, str(name))
    c.setFillColorRGB(0.5, 0.5, 0.55)
    c.setFont(_font(False), 12)
    c.drawCentredString(w / 2, h * 0.74, "— РАЗДЕЛИТЕЛЬ —")
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def make_test_page(side="front", size=(595.0, 842.0)):
    """One-sheet duplex test page (front / back) with orientation markers."""
    from reportlab.pdfgen import canvas
    from pypdf import PdfReader

    _ensure_fonts()
    w, h = size
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(w, h))
    is_front = side == "front"

    # top band with arrow + "ВЕРХ ЛИСТА"
    c.setFillColorRGB(225 / 255, 29 / 255, 72 / 255)
    c.rect(0, h - h * 0.08, w, h * 0.08, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont(_font(True), 22)
    c.drawCentredString(w / 2, h - h * 0.058, "\u25B2  ВЕРХ ЛИСТА  \u25B2")

    c.setFillColorRGB(0.12, 0.12, 0.14)
    c.setFont(_font(True), min(w, h) * 0.09)
    c.drawCentredString(w / 2, h * 0.60, "ЛИЦЕВАЯ" if is_front else "ОБОРОТ")
    c.setFont(_font(True), min(w, h) * 0.16)
    c.drawCentredString(w / 2, h * 0.46, "1")

    c.setFont(_font(False), 14)
    lines_front = [
        "Это ЛИЦЕВАЯ сторона пробного листа.",
        "1) Распечатайте её (кнопка «Печать лицевой»).",
        "2) Переверните лист и вставьте обратно в лоток.",
        "3) Распечатайте ОБОРОТ (кнопка «Печать оборота»).",
    ]
    lines_back = [
        "Это ОБОРОТ пробного листа.",
        "Если надпись «ВЕРХ ЛИСТА» вверху и совпала с лицевой,",
        "а текст НЕ перевёрнут — переворот выбран правильно.",
        "Если оборот вверх ногами — переворачивайте лист",
        "по ДРУГОМУ краю (короткому вместо длинного).",
    ]
    y = h * 0.30
    for ln in (lines_front if is_front else lines_back):
        c.drawCentredString(w / 2, y, ln)
        y -= 22
    c.showPage()
    c.save()
    buf.seek(0)
    return PdfReader(buf).pages[0]


def _page_to_pdf_bytes(page, size=(595.0, 842.0)) -> bytes:
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def build_test_sheet(side="front", orientation="portrait") -> bytes:
    """Return a single-page PDF for the duplex orientation test."""
    data = _page_to_pdf_bytes(make_test_page(side))
    if orientation == "landscape":
        data = _rotate_pdf(data, 90)
    return data


def _rotate_pdf(pdf_bytes: bytes, angle: int) -> bytes:
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for p in reader.pages:
        p.rotate(angle)
        writer.add_page(p)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def build_manual_duplex(pdf_list, side="front", back_order="reversed",
                        separators=False, labels=None, orientation="portrait",
                        flip_edge="long") -> bytes:
    """Build a PDF for MANUAL double-sided printing on a single-sided printer.

    Works sheet-by-sheet: each document is padded to an even number of pages so it
    always begins on a fresh sheet FRONT. Optionally inserts a numbered separator
    sheet before each document (front=divider, back=blank) so stacks are easy to sort.

    side="front" -> front side of every sheet (pages 1,3,5,... + separators), normal order.
    side="back"  -> back side of every sheet; when back_order="reversed" the whole
                    back sequence is reversed (flip the entire printed stack at once).
    """
    from pypdf import PdfReader, PdfWriter

    labels = labels or []
    sheets = []  # list of (front_item, back_item); item = ("page", obj) | ("blank", (w,h))
    ref_size = (595.0, 842.0)

    for di, b in enumerate(pdf_list):
        reader = PdfReader(io.BytesIO(b))
        pages = list(reader.pages)
        if not pages:
            continue
        ref = pages[-1]
        w = float(ref.mediabox.width)
        h = float(ref.mediabox.height)
        ref_size = (w, h)

        if separators:
            lbl = labels[di] if di < len(labels) else {}
            sep = make_separator_page(
                index=di + 1,
                number=lbl.get("number", "") if isinstance(lbl, dict) else "",
                name=lbl.get("name", "") if isinstance(lbl, dict) else "",
                size=(w, h),
            )
            sheets.append((("page", sep), ("blank", (w, h))))

        seq = [("page", p) for p in pages]
        if len(pages) % 2 == 1:
            seq.append(("blank", (w, h)))
        for i in range(0, len(seq), 2):
            sheets.append((seq[i], seq[i + 1]))

    if side == "front":
        items = [s[0] for s in sheets]
    else:
        items = [s[1] for s in sheets]
        if back_order == "reversed":
            items = list(reversed(items))

    writer = PdfWriter()
    for kind, val in items:
        if kind == "page":
            writer.add_page(val)
        else:
            writer.add_blank_page(width=val[0], height=val[1])
    if len(writer.pages) == 0:
        writer.add_blank_page(width=ref_size[0], height=ref_size[1])
    # short-edge flip: back pages need an extra 180° so they aren't upside-down
    extra = 180 if (side == "back" and flip_edge == "short") else 0
    rot = (90 if orientation == "landscape" else 0) + extra
    if rot:
        for p in writer.pages:
            p.rotate(rot % 360)
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
