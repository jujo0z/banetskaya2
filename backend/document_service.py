"""Document generation: fill the docx template with student data and convert to PDF."""
import io
import logging
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from docxtpl import DocxTemplate

logger = logging.getLogger("document_service")



def _resource_base() -> Path:
    """Base directory for bundled resources (works both in dev and PyInstaller onefile)."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).parent


TEMPLATE_PATH = _resource_base() / "templates" / "contract_template.docx"

# LibreOffice binary — configurable for Windows (e.g. C:\Program Files\LibreOffice\program\soffice.exe)
def _soffice_candidates():
    """Ordered list of possible LibreOffice launchers to try."""
    cands = []
    env = os.environ.get("SOFFICE_BIN")
    if env:
        cands.append(env)
    # Desktop build: LibreOffice bundled next to the app (portable, no install).
    cands.append(str(_resource_base() / "libreoffice" / "program" / "soffice.exe"))
    if getattr(sys, "frozen", False):
        cands.append(str(Path(sys.executable).parent / "libreoffice" / "program" / "soffice.exe"))
    # System installs (Windows / Linux / macOS)
    cands += [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        "soffice",
    ]
    # De-duplicate preserving order
    seen, out = set(), []
    for c in cands:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _resolve_soffice():
    for c in _soffice_candidates():
        try:
            if c in ("soffice", "/usr/bin/soffice", "/usr/bin/libreoffice") or Path(c).exists():
                return c
        except Exception:
            pass
    return "soffice"


SOFFICE_BIN = _resolve_soffice()


# ---------- Silent printing (Windows desktop app only) ----------
# SumatraPDF is a tiny, reliable PDF printer that supports "actual size" (noscale)
# printing straight to a named printer with NO dialog — perfect for overlay printing
# onto a pre-inserted 147x103 mm blank.
def _resolve_sumatra():
    env = os.environ.get("SUMATRA_BIN")
    if env:
        return env
    names = ["SumatraPDF.exe", "SumatraPDF-3.5.2-64.exe", "SumatraPDF-64.exe"]
    bases = [_resource_base() / "sumatra"]
    if getattr(sys, "frozen", False):
        bases.append(Path(sys.executable).parent / "sumatra")
    for b in bases:
        for n in names:
            try:
                c = b / n
                if c.exists():
                    return str(c)
            except Exception:
                pass
    return "SumatraPDF.exe"


SUMATRA_BIN = _resolve_sumatra()


def printing_supported() -> bool:
    """Silent printing works only when running on Windows (the desktop app)."""
    return sys.platform.startswith("win")


def list_printers():
    """Return [{'name': str, 'default': bool}] of local Windows printers."""
    if not printing_supported():
        return []
    try:
        import json as _json
        cmd = [
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            "Get-CimInstance Win32_Printer | Select-Object Name,Default | ConvertTo-Json -Compress",
        ]
        out = subprocess.run(cmd, capture_output=True, timeout=20)
        raw = out.stdout.decode("utf-8", "ignore").strip()
        if not raw:
            return []
        parsed = _json.loads(raw)
        if isinstance(parsed, dict):
            parsed = [parsed]
        printers = []
        for p in parsed:
            name = (p.get("Name") or "").strip()
            if name:
                printers.append({"name": name, "default": bool(p.get("Default"))})
        return printers
    except Exception:
        return []


def print_pdf_silent(pdf_bytes: bytes, printer_name: str = "") -> bool:
    """Print a PDF silently at actual size (no scaling) to the given printer.

    Uses SumatraPDF (-print-to / -print-to-default) with 'noscale' so the content
    lands exactly where placed on the 147x103 mm blank. Falls back to LibreOffice
    (soffice --pt) if SumatraPDF is not available.
    """
    if not printing_supported():
        raise RuntimeError("Тихая печать доступна только в Windows-приложении")

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(pdf_bytes)
        pdf_path = tf.name

    try:
        sumatra = SUMATRA_BIN
        have_sumatra = False
        try:
            have_sumatra = Path(sumatra).exists() or sumatra == "SumatraPDF.exe"
        except Exception:
            have_sumatra = False

        if have_sumatra:
            if printer_name:
                cmd = [sumatra, "-print-to", printer_name,
                       "-print-settings", "noscale", "-silent", pdf_path]
            else:
                cmd = [sumatra, "-print-to-default",
                       "-print-settings", "noscale", "-silent", pdf_path]
            res = subprocess.run(cmd, capture_output=True, timeout=120)
            if res.returncode != 0:
                err = res.stderr.decode("utf-8", "ignore")[:300]
                raise RuntimeError(f"SumatraPDF error: {err or res.returncode}")
            return True

        # Fallback: LibreOffice silent print (paper size follows PDF/printer defaults)
        if printer_name:
            cmd = [SOFFICE_BIN, "--headless", "--pt", printer_name, pdf_path]
        else:
            cmd = [SOFFICE_BIN, "--headless", "-p", pdf_path]
        res = subprocess.run(cmd, capture_output=True, timeout=120)
        if res.returncode != 0:
            err = res.stderr.decode("utf-8", "ignore")[:300]
            raise RuntimeError(f"soffice print error: {err or res.returncode}")
        return True
    finally:
        try:
            time.sleep(1.0)  # let the spooler read the file before deletion
            os.unlink(pdf_path)
        except Exception:
            pass



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


def _to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("1", "true", "да", "yes", "on")


def is_minor(birth_date_str, ref_date=None) -> bool:
    """True если человек НЕ достиг 18 лет на дату ref_date (по умолчанию — сегодня)."""
    import datetime as _dt
    d, mo, y = _parse_dmy(birth_date_str)
    if not (d and mo and y):
        return False
    try:
        y = int(y)
        if y < 100:
            y += 2000 if y < 30 else 1900
        bd = _dt.date(y, int(mo), int(d))
    except Exception:
        return False
    ref = ref_date or _dt.date.today()
    age = ref.year - bd.year - ((ref.month, ref.day) < (bd.month, bd.day))
    return age < 18


def _parse_dmy(s):
    """'01.09.2006' | '2006-09-01' -> ('01','09','2006'); иначе ('','','')."""
    import re
    s = str(s or "").strip()
    if not s:
        return "", "", ""
    m = re.match(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})\s*$", s)
    if m:
        return m.group(1).zfill(2), m.group(2).zfill(2), m.group(3)
    m = re.match(r"^\s*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s*$", s)
    if m:
        return m.group(3).zfill(2), m.group(2).zfill(2), m.group(1)
    return "", "", ""


def render_docx(fields: dict, template_path=None) -> bytes:
    import jinja2
    fields = fields or {}
    tpl = DocxTemplate(str(template_path or TEMPLATE_PATH))
    context = {k: (fields.get(k) or "") for k in ALL_TEMPLATE_KEYS}
    for k, v in fields.items():
        context.setdefault(k, v or "")
    # Согласие за несовершеннолетнего: явное значение галочки имеет приоритет,
    # иначе — автоопределение по дате рождения (совершеннолетие на сегодня).
    raw = fields.get("show_minor_consent", None)
    if raw in (None, ""):
        context["show_minor_consent"] = is_minor(fields.get("birth_date"))
    else:
        context["show_minor_consent"] = _to_bool(raw)
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
_SERIF_READY = False


def _ensure_fonts():
    """Register a Unicode (Cyrillic) TTF font with reportlab once as "AppSans".

    Looks for the bundled Liberation Sans first, then common system locations on
    Linux and Windows. IMPORTANT: only marks fonts as ready when a font was
    actually registered — otherwise _font() would return an unregistered
    "AppSans" and reportlab would raise a "Can't find font: AppSans" error."""
    global _FONTS_READY
    if _FONTS_READY:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    def _first_existing(paths):
        for p in paths:
            try:
                pp = Path(p)
                if pp.exists():
                    return pp
            except Exception:
                pass
        return None
    fonts_dir = _resource_base() / "assets" / "fonts"
    reg = _first_existing([
        fonts_dir / "LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ])
    bold = _first_existing([
        fonts_dir / "LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\tahomabd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
    ])
    try:
        if reg:
            pdfmetrics.registerFont(TTFont("AppSans", str(reg)))
            # Always make a bold face available so _font(bold=True) never fails.
            pdfmetrics.registerFont(TTFont("AppSans-Bold", str(bold or reg)))
            _FONTS_READY = True
        else:
            _FONTS_READY = False
    except Exception:
        _FONTS_READY = False

    # --- Serif (Times New Roman) для официальных бланков ---
    global _SERIF_READY
    s_reg = _first_existing([
        fonts_dir / "LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        r"C:\Windows\Fonts\times.ttf",
    ])
    s_bold = _first_existing([
        fonts_dir / "LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf",
        r"C:\Windows\Fonts\timesbd.ttf",
    ])
    s_italic = _first_existing([
        fonts_dir / "LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSerifItalic.ttf",
        r"C:\Windows\Fonts\timesi.ttf",
    ])
    try:
        if s_reg:
            pdfmetrics.registerFont(TTFont("AppSerif", str(s_reg)))
            pdfmetrics.registerFont(TTFont("AppSerif-Bold", str(s_bold or s_reg)))
            pdfmetrics.registerFont(TTFont("AppSerif-Italic", str(s_italic or s_reg)))
            _SERIF_READY = True
        else:
            _SERIF_READY = False
    except Exception:
        _SERIF_READY = False


def _serif(bold=False, italic=False):
    """Times New Roman-совместимый шрифт (Liberation Serif) для бланков."""
    if _SERIF_READY:
        if bold:
            return "AppSerif-Bold"
        if italic:
            return "AppSerif-Italic"
        return "AppSerif"
    return _font(bold)


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
        # ВАЖНО: правильный file:// URI на всех ОС. На Windows str(path) = "C:\..."
        # и "file://" + str(path) даёт БИТЫЙ URI (file://C:\...), из-за чего
        # LibreOffice не создаёт профиль и падает с ошибкой soffice.bin.
        # Path.as_uri() формирует корректный file:///C:/... (и file:///tmp/... на Linux).
        profile_dir.mkdir(parents=True, exist_ok=True)
        profile_uri = profile_dir.as_uri()

        last_err = None
        candidates = []
        for c in _soffice_candidates():
            try:
                if c in ("soffice", "/usr/bin/soffice", "/usr/bin/libreoffice") or Path(c).exists():
                    candidates.append(c)
            except Exception:
                pass
        if not candidates:
            candidates = [SOFFICE_BIN]
        for soffice in candidates:
            for attempt in range(2):
                try:
                    subprocess.run(
                        [
                            soffice,
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
                except FileNotFoundError:
                    last_err = RuntimeError(f"LibreOffice не найден: {soffice}")
                    break  # try next candidate
                except subprocess.CalledProcessError as e:
                    last_err = RuntimeError(
                        f"soffice error: {e.stderr.decode('utf-8', 'ignore')[:300]}"
                    )
                except Exception as e:
                    last_err = RuntimeError(f"soffice error: {e}")
                time.sleep(0.6)
        raise last_err or RuntimeError(
            "Не удалось конвертировать в PDF (LibreOffice недоступен). "
            "Скачайте документ в формате DOCX."
        )



# ============================================================================
#  OVERLAY PRINTING — печать данных поверх готового (пред-распечатанного) бланка
# ============================================================================

MM = 72.0 / 25.4  # points per millimetre

# Физический размер бланка «СООБЩЕНИЕ» (альбомная ориентация), мм
SOOBSHENIE_PAGE_MM = (147.0, 103.0)

# Дефолтная раскладка полей: координаты в процентах от листа (0..100),
# x_pct — от левого края, y_pct — от ВЕРХНЕГО края. Пользователь двигает мышкой.
SOOBSHENIE_LAYOUT = [
    {"key": "reg_organ",       "label": "Орган регистрации",        "x_pct": 58.0, "y_pct": 9.0,  "font_pt": 9,  "group": "Шапка"},
    {"key": "date_day",        "label": "День (дата сообщения)",    "x_pct": 8.0,  "y_pct": 15.5, "font_pt": 9,  "group": "Шапка"},
    {"key": "date_month",      "label": "Месяц (дата сообщения)",   "x_pct": 13.5, "y_pct": 15.5, "font_pt": 9,  "group": "Шапка"},
    {"key": "date_year",       "label": "Год (20__)",               "x_pct": 29.5, "y_pct": 15.5, "font_pt": 9,  "group": "Шапка"},
    {"key": "number",          "label": "№ сообщения",              "x_pct": 11.0, "y_pct": 20.0, "font_pt": 9,  "group": "Шапка"},
    {"key": "fio",             "label": "ФИО",                       "x_pct": 11.0, "y_pct": 28.5, "font_pt": 10, "group": "Гражданин"},
    {"key": "fio2",            "label": "ФИО (2-я строка)",          "x_pct": 7.0,  "y_pct": 36.0, "font_pt": 10, "group": "Гражданин"},
    {"key": "birth",           "label": "Год и место рождения",      "x_pct": 7.0,  "y_pct": 41.5, "font_pt": 10, "group": "Гражданин"},
    {"key": "address",         "label": "Адрес пребывания",          "x_pct": 44.5, "y_pct": 44.5, "font_pt": 9,  "group": "Регистрация"},
    {"key": "address2",        "label": "Адрес (2-я строка)",        "x_pct": 7.0,  "y_pct": 50.5, "font_pt": 9,  "group": "Регистрация"},
    {"key": "passport_series", "label": "Серия",                     "x_pct": 13.0, "y_pct": 61.0, "font_pt": 9,  "group": "Документ"},
    {"key": "passport_number", "label": "Номер",                     "x_pct": 24.0, "y_pct": 61.0, "font_pt": 9,  "group": "Документ"},
    {"key": "issue_day",       "label": "День выдачи",               "x_pct": 61.5, "y_pct": 61.0, "font_pt": 9,  "group": "Документ"},
    {"key": "issue_month",     "label": "Месяц выдачи",              "x_pct": 68.0, "y_pct": 61.0, "font_pt": 9,  "group": "Документ"},
    {"key": "issue_year",      "label": "Год выдачи (20__)",         "x_pct": 88.0, "y_pct": 61.0, "font_pt": 9,  "group": "Документ"},
    {"key": "issued_by",       "label": "Кем выдан",                 "x_pct": 16.5, "y_pct": 65.5, "font_pt": 8,  "group": "Документ"},
    {"key": "from_day",        "label": "С: день",                   "x_pct": 10.5, "y_pct": 72.5, "font_pt": 9,  "group": "Срок"},
    {"key": "from_month",      "label": "С: месяц",                  "x_pct": 17.0, "y_pct": 72.5, "font_pt": 9,  "group": "Срок"},
    {"key": "from_year",       "label": "С: год (20__)",             "x_pct": 36.0, "y_pct": 72.5, "font_pt": 9,  "group": "Срок"},
    {"key": "to_day",          "label": "По: день",                  "x_pct": 45.0, "y_pct": 72.5, "font_pt": 9,  "group": "Срок"},
    {"key": "to_month",        "label": "По: месяц",                 "x_pct": 52.5, "y_pct": 72.5, "font_pt": 9,  "group": "Срок"},
    {"key": "to_year",         "label": "По: год (20__)",            "x_pct": 70.5, "y_pct": 72.5, "font_pt": 9,  "group": "Срок"},
    {"key": "chief",           "label": "Начальник",                 "x_pct": 17.5, "y_pct": 79.0, "font_pt": 9,  "group": "Подпись"},
]


def _overlay_bg_path():
    p = _resource_base() / "assets" / "soobshenie_blank.png"
    return p if p.exists() else None


def _draw_soobshenie_form(c, zone_w, zone_h, zone_top):
    """Draw a clean, typed СООБЩЕНИЕ form (vector) matching the paper blank 1:1,
    so «Полная печать» prints a crisp document on plain white paper instead of a
    photo scan. Coordinates are in percent from the TOP-LEFT of the 147x103 zone,
    matching SOOBSHENIE_LAYOUT so the data lands on the right lines.
    """
    def PX(xp):
        return xp / 100.0 * zone_w

    def PY(yp):
        return zone_top - yp / 100.0 * zone_h

    def text(xp, yp, s, size=8, bold=False):
        c.setFont(_font(bold), size)
        c.drawString(PX(xp), PY(yp), s)

    def center(xp, yp, s, size=5.2, bold=False):
        c.setFont(_font(bold), size)
        c.drawCentredString(PX(xp), PY(yp), s)

    def rule(xp1, xp2, yp):
        # underline rule slightly below the text baseline
        y = PY(yp) - 1.2
        c.setLineWidth(0.4)
        c.setStrokeColorRGB(0.15, 0.15, 0.2)
        c.line(PX(xp1), y, PX(xp2), y)

    c.setFillColorRGB(0.1, 0.1, 0.15)

    # --- Штамп block (top-left) ---
    text(12, 5.5, "Штамп", 8)
    text(8.5, 8.8, "органа регистрации", 8)
    # right: наименование органа регистрации
    rule(55, 93, 9.0)
    center(74, 12.2, "(наименование органа регистрации)", 5.2)
    # date line: «__» ____ 20__ г.
    text(6, 15.5, "«", 8)
    rule(7.8, 12.5, 15.5)
    text(12.6, 15.5, "»", 8)
    rule(13.8, 25.5, 15.5)
    text(26.0, 15.5, "20", 8)
    rule(29.0, 33.5, 15.5)
    text(34.0, 15.5, "г.", 8)
    # № line
    text(6, 20.0, "№", 8)
    rule(9.5, 24.0, 20.0)

    # --- Title ---
    center(50, 25.2, "СООБЩЕНИЕ", 13, bold=True)

    # --- Citizen ---
    text(6, 28.5, "Гр.", 8)
    rule(11.5, 93, 28.5)
    center(45, 32.0, "(фамилия, собственное имя, отчество, год и место рождения)", 5.2)
    rule(6, 93, 36.5)
    rule(6, 93, 42.0)

    # --- Registration ---
    text(6, 45.0, "зарегистрирован(а) по месту пребывания", 8)
    rule(43, 93, 45.0)
    rule(6, 93, 51.0)
    center(45, 54.0, "(адрес)", 5.2)

    # --- Identity document ---
    text(6, 57.5, "Документ, удостоверяющий личность: паспорт, вид на жительство", 8)
    rule(78, 93, 57.5)
    text(6, 61.0, "серия", 8)
    rule(11.5, 21.0, 61.0)
    text(21.5, 61.0, ", №", 8)
    rule(24.5, 46.0, 61.0)
    text(46.5, 61.0, ", дата выдачи «", 8)
    rule(60.5, 66.5, 61.0)
    text(66.8, 61.0, "»", 8)
    rule(67.8, 80.0, 61.0)
    text(85.5, 61.0, "20", 8)
    rule(88.0, 92.5, 61.0)
    text(93.0, 61.0, "г.", 8)
    text(6, 65.8, "кем выдан", 8)
    rule(16.0, 93, 65.8)
    center(48, 68.6, "(наименование органа внутренних дел)", 5.2)

    # --- Term ---
    text(6, 72.5, "с «", 8)
    rule(9.8, 16.0, 72.5)
    text(16.2, 72.5, "»", 8)
    rule(17.2, 33.0, 72.5)
    text(33.3, 72.5, "20", 8)
    rule(35.3, 40.0, 72.5)
    text(40.3, 72.5, "г. по «", 8)
    rule(44.0, 50.0, 72.5)
    text(50.2, 72.5, "»", 8)
    rule(51.2, 68.0, 72.5)
    text(68.3, 72.5, "20", 8)
    rule(70.0, 74.5, 72.5)
    text(74.8, 72.5, "г.", 8)

    # --- Signature ---
    text(6, 79.0, "Начальник", 8)
    rule(17, 55, 79.0)
    rule(60, 90, 79.0)
    center(36, 81.6, "(наименование органа регистрации)", 5.0)
    center(75, 81.6, "(подпись)", 5.0)
    text(6, 85.5, "М.П.", 8)

    # reset for data drawing
    c.setFillColorRGB(0.05, 0.05, 0.12)


def _rot_page_dims(rotate, w, h):
    """Page dimensions after rotating a card: 90/270 swap width and height."""
    return (h, w) if (int(rotate) % 360) in (90, 270) else (w, h)


def _apply_card_rotation(c, rotate, zone_w, zone_h):
    """Set up a transform so drawing in the natural card space
    (origin bottom-left, card spans zone_w x zone_h) lands rotated on the page.
    Used when the pre-printed blank is fed into the printer in a rotated
    orientation (e.g. short edge / 103 mm first -> rotate 90)."""
    r = int(rotate) % 360
    if r == 90:
        c.translate(zone_h, 0)
        c.rotate(90)
    elif r == 180:
        c.translate(zone_w, zone_h)
        c.rotate(180)
    elif r == 270:
        c.translate(0, zone_w)
        c.rotate(270)


def _draw_card_content(c, zone_w, zone_h, layout, rec, ddx=0.0, ddy=0.0,
                       with_form=False, bg=None):
    """Draw one СООБЩЕНИЕ card in the CURRENT coordinate system, assuming the
    card occupies (0,0)..(zone_w, zone_h) with the origin at the bottom-left."""
    if bg is not None:
        try:
            c.drawImage(bg, 0, 0, width=zone_w, height=zone_h,
                        preserveAspectRatio=False, mask=None)
        except Exception:
            pass
    if with_form:
        _draw_soobshenie_form(c, zone_w, zone_h, zone_h)
    c.setFillColorRGB(0.05, 0.05, 0.12)
    for f in (layout or []):
        key = f.get("key")
        val = rec.get(key, "")
        if val is None:
            val = ""
        val = str(val).strip()
        if not val:
            continue
        font_pt = float(f.get("font_pt", 9) or 9)
        x = float(f.get("x_pct", 0)) / 100.0 * zone_w + ddx
        y = zone_h - (float(f.get("y_pct", 0)) / 100.0 * zone_h) - ddy
        c.setFont(_font(False), font_pt)
        c.drawString(x, y, val)


_A4_POSITIONS = {"top-left", "top-center", "top-right", "center"}


def build_overlay(records, layout=None, blank_mm=SOOBSHENIE_PAGE_MM, page_size="card",
                  dx_mm=0.0, dy_mm=0.0, with_background=False, with_form=False,
                  rotate=0, a4_position="top-left"):
    """Generate a multi-page PDF where only the field VALUES are drawn at exact
    positions, sized to the physical blank. Printed on top of a pre-printed form.

    records: list of dicts {field_key: value}
    layout:  list of {key, x_pct, y_pct, font_pt}
    blank_mm: physical size of the pre-printed form (the "zone"), default 147x103
    page_size: "card" -> page equals the blank; "a4" -> A4 sheet with the blank
               anchored in a chosen corner (universal-printer friendly)
    dx_mm/dy_mm: global calibration shift (right/down positive), in card space
    with_background: draw the scanned blank behind (preview / plain-paper test)
    rotate: 0/90/180/270 — rotate the whole card to match how the blank is fed
            into the printer (card mode only; ignored for A4 carrier).
    a4_position: where the card sits on the A4 carrier (A4 mode only).
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    _ensure_fonts()
    layout = layout or SOOBSHENIE_LAYOUT
    rotate = int(rotate or 0) % 360
    zone_w = blank_mm[0] * MM
    zone_h = blank_mm[1] * MM
    ddx = dx_mm * MM
    ddy = dy_mm * MM

    bg = None
    if with_background:
        bp = _overlay_bg_path()
        if bp:
            try:
                bg = ImageReader(str(bp))
            except Exception:
                bg = None

    if not records:
        records = [{}]

    is_a4 = str(page_size).lower() == "a4"
    if is_a4:
        pw, ph = 210 * MM, 297 * MM
    else:
        pw, ph = _rot_page_dims(rotate, zone_w, zone_h)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))
    for rec in records:
        c.saveState()
        if is_a4:
            pos = a4_position if a4_position in _A4_POSITIONS else "top-left"
            if pos == "top-left":
                ox, oy = 0.0, ph - zone_h
            elif pos == "top-center":
                ox, oy = (pw - zone_w) / 2.0, ph - zone_h
            elif pos == "top-right":
                ox, oy = pw - zone_w, ph - zone_h
            else:  # center
                ox, oy = (pw - zone_w) / 2.0, (ph - zone_h) / 2.0
            c.translate(ox + ddx, oy - ddy)
            if bg is None and not with_form:
                # faint placement guide for positioning the pre-printed card
                c.setStrokeColorRGB(0.75, 0.75, 0.8)
                c.setLineWidth(0.4)
                c.rect(0.3 * MM, 0.3 * MM, zone_w - 0.6 * MM, zone_h - 0.6 * MM,
                       stroke=1, fill=0)
            _draw_card_content(c, zone_w, zone_h, layout, rec, 0, 0, with_form, bg)
        else:
            _apply_card_rotation(c, rotate, zone_w, zone_h)
            _draw_card_content(c, zone_w, zone_h, layout, rec, ddx, ddy, with_form, bg)
        c.restoreState()
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def build_carrier_frame(a4_position="top-left", blank_mm=SOOBSHENIE_PAGE_MM):
    """A4 "carrier" sheet with an EMPTY 147x103 outline (+ corner marks) at the
    chosen position. Print it once at 100%, tape the pre-printed СООБЩЕНИЕ blank
    inside the outline, then run that carrier through the printer for the data
    overlay (A4 mode, same a4_position). This fixes the blank in the exact same
    spot every time, so the data never lands "in a different place"."""
    from reportlab.pdfgen import canvas

    _ensure_fonts()
    zone_w = blank_mm[0] * MM
    zone_h = blank_mm[1] * MM
    pw, ph = 210 * MM, 297 * MM

    pos = a4_position if a4_position in _A4_POSITIONS else "top-left"
    if pos == "top-left":
        ox, oy = 0.0, ph - zone_h
    elif pos == "top-center":
        ox, oy = (pw - zone_w) / 2.0, ph - zone_h
    elif pos == "top-right":
        ox, oy = pw - zone_w, ph - zone_h
    else:  # center
        ox, oy = (pw - zone_w) / 2.0, (ph - zone_h) / 2.0

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))

    # outline of the blank
    c.setStrokeColorRGB(0.55, 0.55, 0.62)
    c.setLineWidth(0.7)
    c.setDash(4, 3)
    c.rect(ox, oy, zone_w, zone_h, stroke=1, fill=0)
    c.setDash()

    # solid corner L-marks for precise taping
    m = 8 * MM
    c.setStrokeColorRGB(0.1, 0.1, 0.15)
    c.setLineWidth(1.1)
    corners = [
        (ox, oy),                       # bottom-left
        (ox + zone_w, oy),              # bottom-right
        (ox, oy + zone_h),              # top-left
        (ox + zone_w, oy + zone_h),     # top-right
    ]
    for i, (cx, cy) in enumerate(corners):
        sx = 1 if i in (0, 2) else -1   # inward x direction
        sy = 1 if i in (0, 1) else -1   # inward y direction
        c.line(cx, cy, cx + sx * m, cy)
        c.line(cx, cy, cx, cy + sy * m)

    # instructions inside the frame
    c.setFillColorRGB(0.35, 0.35, 0.42)
    c.setFont(_font(True), 11)
    c.drawCentredString(ox + zone_w / 2.0, oy + zone_h / 2.0 + 6,
                        "Приклейте бланк «СООБЩЕНИЕ» сюда")
    c.setFont(_font(False), 8)
    c.drawCentredString(ox + zone_w / 2.0, oy + zone_h / 2.0 - 8,
                        "147 × 103 мм · по уголкам · печать 100%")

    # header note
    c.setFillColorRGB(0.1, 0.1, 0.15)
    c.setFont(_font(False), 8)
    c.drawString(12 * MM, ph - 12 * MM,
                 "Лист-держатель. Печатать в масштабе 100% (Фактический размер). "
                 "Наклейте бланк точно по уголкам, затем печатайте данные в режиме «Лист A4».")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()



def build_full_sheets(records, layout=None, orientation="portrait", per_sheet=0,
                      draw_guides=True):
    """Full-document print: draw complete СООБЩЕНИЕ forms (typed form + data)
    laid out as a GRID on real A4 pages, so a normal printer prints reliably.

    orientation: "portrait"  -> A4 210x297, 1 col x 2 rows  (max 2 per sheet)
                 "landscape" -> A4 297x210, 2 cols x 2 rows (max 4 per sheet)
    per_sheet:   how many cards per sheet (1..max); 0 = max for the orientation.
    """
    from reportlab.pdfgen import canvas

    _ensure_fonts()
    layout = layout or SOOBSHENIE_LAYOUT
    card_w = SOOBSHENIE_PAGE_MM[0] * MM
    card_h = SOOBSHENIE_PAGE_MM[1] * MM
    orientation = (orientation or "portrait").lower()
    if orientation == "landscape":
        pw, ph = 297 * MM, 210 * MM
        cols, rows = 2, 2
    else:
        pw, ph = 210 * MM, 297 * MM
        cols, rows = 1, 2
    max_per = cols * rows
    if per_sheet and int(per_sheet) > 0:
        per_sheet = min(int(per_sheet), max_per)
    else:
        per_sheet = max_per

    gap_x = 6 * MM
    gap_y = 8 * MM

    if not records:
        records = [{}]

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))
    for start in range(0, len(records), per_sheet):
        chunk = records[start:start + per_sheet]
        rows_used = (len(chunk) + cols - 1) // cols
        block_w = cols * card_w + (cols - 1) * gap_x
        block_h = rows_used * card_h + (rows_used - 1) * gap_y
        left = (pw - block_w) / 2.0
        top = (ph + block_h) / 2.0  # top edge of the grid block
        for i, rec in enumerate(chunk):
            col = i % cols
            row = i // cols
            x0 = left + col * (card_w + gap_x)
            y_top = top - row * (card_h + gap_y)
            y0 = y_top - card_h
            c.saveState()
            c.translate(x0, y0)
            if draw_guides:
                c.setStrokeColorRGB(0.8, 0.8, 0.85)
                c.setLineWidth(0.3)
                c.setDash(2, 2)
                c.rect(0, 0, card_w, card_h, stroke=1, fill=0)
                c.setDash()
            _draw_card_content(c, card_w, card_h, layout, rec, 0, 0,
                               with_form=True, bg=None)
            c.restoreState()
        c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def build_overlay_test_sheet(blank_mm=SOOBSHENIE_PAGE_MM, page_size="card",
                             dx_mm=0.0, dy_mm=0.0, rotate=0):
    """Alignment test sheet: frame, corner crosses, 1 cm ruler and centre cross,
    drawn within the blank zone. page_size 'a4' puts the zone in the top-left of A4.
    rotate 0/90/180/270 matches how the blank is fed into the printer."""
    from reportlab.pdfgen import canvas

    _ensure_fonts()
    zw = blank_mm[0] * MM
    zh = blank_mm[1] * MM
    rotate = int(rotate or 0) % 360
    ddx = dx_mm * MM
    ddy = dy_mm * MM
    is_a4 = str(page_size).lower() == "a4"
    if is_a4:
        pw, ph = 210 * MM, 297 * MM
    else:
        pw, ph = _rot_page_dims(rotate, zw, zh)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))

    # Establish a coordinate system where the card occupies (0,0)..(zw,zh) with
    # the origin at the bottom-left, then apply calibration + rotation.
    c.saveState()
    if is_a4:
        c.translate(ddx, (ph - zh) - ddy)
    else:
        _apply_card_rotation(c, rotate, zw, zh)
        c.translate(ddx, -ddy)

    # outer frame of the zone
    c.setStrokeColorRGB(0.7, 0.1, 0.25)
    c.setLineWidth(0.6)
    c.rect(0.3 * MM, 0.3 * MM, zw - 0.6 * MM, zh - 0.6 * MM, stroke=1, fill=0)

    inset = 5 * MM

    def cross(cx, cy, s=4 * MM):
        c.line(cx - s, cy, cx + s, cy)
        c.line(cx, cy - s, cx, cy + s)

    c.setStrokeColorRGB(0.1, 0.1, 0.15)
    for cx in (inset, zw - inset):
        for cy in (inset, zh - inset):
            cross(cx, cy)
    # centre cross
    c.setStrokeColorRGB(0.7, 0.1, 0.25)
    cross(zw / 2, zh / 2, 6 * MM)

    # ruler ticks every 10 mm along top and left of the zone, labelled in cm
    c.setStrokeColorRGB(0.3, 0.3, 0.4)
    c.setFillColorRGB(0.3, 0.3, 0.4)
    c.setFont(_font(False), 6)
    n_x = int(blank_mm[0] // 10)
    for i in range(0, n_x + 1):
        x = i * 10 * MM
        c.line(x, zh - inset, x, zh - inset - 3 * MM)
        c.drawString(x + 1, zh - inset - 3 * MM - 6, str(i))
    n_y = int(blank_mm[1] // 10)
    for i in range(0, n_y + 1):
        y = zh - i * 10 * MM
        c.line(inset, y, inset + 3 * MM, y)
        c.drawString(inset + 3 * MM + 1, y - 2, str(i))

    # title + calibration note, drawn INSIDE the card so it rotates with it
    c.setFillColorRGB(0.7, 0.1, 0.25)
    c.setFont(_font(True), 9)
    c.drawCentredString(zw / 2, zh - 6 * MM,
                        "ПРОБНЫЙ ЛИСТ — %.0f×%.0f мм" % (blank_mm[0], blank_mm[1]))
    c.setFillColorRGB(0.3, 0.3, 0.4)
    c.setFont(_font(False), 6.5)
    c.drawCentredString(zw / 2, 3 * MM,
                        "Сдвиг X=%.1f Y=%.1f мм · Поворот %d° · Масштаб 100%%"
                        % (dx_mm, dy_mm, rotate))

    c.restoreState()

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()



# --- Clean vector form background (no data) for the "Полная печать" preview ---
_FORM_BG_CACHE = None


def render_pdf_first_page_png(pdf_bytes: bytes, scale: float = 2.0) -> bytes:
    """Render the FIRST page of a PDF to PNG (used for on-screen previews that
    must display reliably everywhere, even where inline PDF is blocked)."""
    return render_pdf_page_png(pdf_bytes, 0, scale)


def render_pdf_page_png(pdf_bytes: bytes, index: int = 0, scale: float = 2.0) -> bytes:
    """Render a specific page (by index, clamped) of a PDF to PNG."""
    import pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    i = max(0, min(int(index or 0), len(doc) - 1))
    pix = doc[i].get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
    png = pix.tobytes("png")
    doc.close()
    return png


def render_form_background_png(scale: float = 3.0) -> bytes:
    """Render the clean vector СООБЩЕНИЕ form (no data) as a PNG image.

    Used by the "Полная печать" live preview so the operator sees exactly the
    typed document that will be printed on plain paper — NOT the scanned photo
    (that scan stays only in the overlay-on-blank mode).
    """
    global _FORM_BG_CACHE
    if _FORM_BG_CACHE is not None:
        return _FORM_BG_CACHE

    import pymupdf

    pdf_bytes = build_overlay([], layout=SOOBSHENIE_LAYOUT, page_size="card", with_form=True)
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
    png = pix.tobytes("png")
    doc.close()
    _FORM_BG_CACHE = png
    return png


# ---------- System self-diagnostics (для экрана «Проверка системы») ----------
def run_diagnostics():
    """Проверяет ключевые компоненты на МАШИНЕ, где запущен backend
    (в десктоп-приложении — на компьютере пользователя). Возвращает список
    проверок [{key, label, ok, detail, info?}]. Не требует БД."""
    checks = []

    # Шрифты (кириллица)
    try:
        _ensure_fonts()
        checks.append({
            "key": "fonts", "label": "Шрифты (кириллица)", "ok": bool(_FONTS_READY),
            "detail": "Шрифт AppSans зарегистрирован" if _FONTS_READY else "Используется системный fallback",
        })
    except Exception as e:
        checks.append({"key": "fonts", "label": "Шрифты (кириллица)", "ok": False, "detail": str(e)})

    # Скан бланка (assets)
    bp = _overlay_bg_path()
    checks.append({
        "key": "assets", "label": "Скан бланка (assets)", "ok": bool(bp),
        "detail": (str(bp) if bp else "Файл soobshenie_blank.png не найден"),
    })

    # Шаблон договора
    checks.append({
        "key": "template", "label": "Шаблон договора найма", "ok": TEMPLATE_PATH.exists(),
        "detail": (str(TEMPLATE_PATH) if TEMPLATE_PATH.exists() else "contract_template.docx не найден"),
    })

    # LibreOffice (реальный тест конвертации DOCX→PDF)
    soffice = SOFFICE_BIN
    try:
        from docx import Document as _Docx
        _buf = io.BytesIO()
        _doc = _Docx()
        _doc.add_paragraph("Тест конвертации — проверка LibreOffice (кириллица)")
        _doc.save(_buf)
        pdf = convert_to_pdf(_buf.getvalue())
        ok_soffice = pdf[:4] == b"%PDF"
        detail = f"OK · {soffice}" if ok_soffice else f"Не создан PDF · {soffice}"
    except Exception as e:
        ok_soffice = False
        detail = f"{str(e)[:220]} · {soffice}"
    checks.append({"key": "libreoffice", "label": "LibreOffice (экспорт в PDF)", "ok": ok_soffice, "detail": detail})

    # Самотест генерации PDF бланка
    try:
        pdf = build_overlay([{"fio": "тест"}], page_size="card", with_form=True)
        ok_pdf = pdf[:4] == b"%PDF"
        checks.append({"key": "pdf", "label": "Генерация PDF бланка", "ok": ok_pdf, "detail": f"{len(pdf)} байт"})
    except Exception as e:
        checks.append({"key": "pdf", "label": "Генерация PDF бланка", "ok": False, "detail": str(e)})

    # Принтеры (только Windows)
    supported = printing_supported()
    if supported:
        prs = list_printers()
        checks.append({
            "key": "printers", "label": "Принтеры", "ok": len(prs) > 0,
            "detail": (f"Найдено принтеров: {len(prs)}" if prs else "Принтеры не найдены"),
        })
    else:
        checks.append({
            "key": "printers", "label": "Принтеры", "ok": True, "info": True,
            "detail": "Проверка доступна только в Windows-приложении",
        })

    return checks



# ==========================================================================
#  ФОРМА 19 — «Адресный листок прибытия» (полная векторная отрисовка)
#  Печать на чистом листе A4: зона формы 105×145 мм, сетка 2×2 (2 человека
#  на лист, по 2 копии каждому). Лист-лицо и лист-оборот чередуются для
#  двусторонней печати.
# ==========================================================================

FORMA19_MM = (105.0, 145.0)  # физический размер одного листка, мм

# Безопасные поля листа: блок карт вписывается 1:1 без автоподгонки/обрезки
# принтера. Поля симметричны — это КЛЮЧЕВО для совмещения лицевой и оборотной
# сторон при двусторонней печати (дуплексе).
FORMA_MARGIN_X = 5.0 * MM
FORMA_MARGIN_Y = 6.0 * MM


def _fit_grid(pw, ph, zw, zh, cols, rows):
    """Вписать сетку cols×rows карт zw×zh в лист pw×ph с безопасными полями.
    Возвращает (scale, sw, sh, side_margin, top_margin); блок центрирован."""
    sx = (pw - 2 * FORMA_MARGIN_X) / (cols * zw)
    sy = (ph - 2 * FORMA_MARGIN_Y) / (rows * zh)
    scale = min(sx, sy, 1.0)
    sw, sh = zw * scale, zh * scale
    side_margin = (pw - cols * sw) / 2.0
    top_margin = (ph - rows * sh) / 2.0
    return scale, sw, sh, side_margin, top_margin

# Поля формы, сгруппированные для UI (порядок = порядок ввода).
FORMA19_FIELDS = [
    {"group": "Идентификация", "fields": [
        {"key": "top_date", "label": "Дата вверху (над бланком, напр. «вр. по 30.06.27»)"},
        {"key": "id_number", "label": "Идентификационный номер (13 цифр)"},
        {"key": "surname", "label": "1. Фамилия"},
        {"key": "first_name", "label": "2. Собственное имя"},
        {"key": "patronymic", "label": "3. Отчество"},
        {"key": "birth_day", "label": "4. Дата рождения — день"},
        {"key": "birth_month", "label": "4. Дата рождения — месяц (словом)"},
        {"key": "birth_year", "label": "4. Дата рождения — год"},
        {"key": "sex", "label": "6. Пол (М/Ж)"},
        {"key": "citizenship", "label": "7. Гражданство"},
    ]},
    {"group": "5. Место рождения", "fields": [
        {"key": "bp_obl", "label": "обл. (республика)"},
        {"key": "bp_raion", "label": "район"},
        {"key": "bp_city", "label": "город (пгт)"},
        {"key": "bp_village", "label": "село (деревня)"},
    ]},
    {"group": "8. Место жительства", "fields": [
        {"key": "res_obl", "label": "обл. (республика)"},
        {"key": "res_raion", "label": "район"},
        {"key": "res_city", "label": "город (пгт)"},
        {"key": "res_village", "label": "село (деревня)"},
        {"key": "res_street", "label": "улица"},
        {"key": "res_house", "label": "дом"},
        {"key": "res_korpus", "label": "корпус"},
        {"key": "res_apartment", "label": "квартира"},
        {"key": "reg_authority", "label": "Орган, оформивший регистрацию"},
    ]},
    {"group": "9. Откуда прибыл и когда", "fields": [
        {"key": "from_obl", "label": "обл. (республика)"},
        {"key": "from_raion", "label": "район"},
        {"key": "from_city", "label": "город (пгт)"},
        {"key": "from_village", "label": "село (деревня)"},
        {"key": "arrival_date", "label": "дата прибытия"},
        {"key": "moved_street", "label": "Переехал с улицы"},
        {"key": "moved_house", "label": "дом"},
        {"key": "moved_korpus", "label": "корпус"},
        {"key": "moved_apartment", "label": "квартира"},
        {"key": "name_changed_from", "label": "Изменил ФИО с"},
        {"key": "other_reasons", "label": "Другие причины"},
    ]},
    {"group": "Оборотная сторона", "fields": [
        {"key": "purpose", "label": "10. Цель приезда"},
        {"key": "purpose_term", "label": "10. Срок (по ...)"},
        {"key": "employment", "label": "11. Где и кем работает"},
        {"key": "passport_series", "label": "12. Паспорт: серия"},
        {"key": "passport_number", "label": "12. Паспорт: номер"},
        {"key": "passport_issued", "label": "12. Паспорт: кем выдан"},
        {"key": "passport_valid_until", "label": "12. Паспорт: срок действия"},
    ]},
]

FORMA19_FIELD_KEYS = [f["key"] for g in FORMA19_FIELDS for f in g["fields"]]


def forma19_from_contract(fields: dict) -> dict:
    """Пред-заполнение полей Формы 19 из данных договора (student dict).
    Разбивает ФИО, дату рождения и паспорт на компоненты."""
    fields = fields or {}
    rec = {}
    # ИИН -> идентификационный номер
    rec["id_number"] = str(fields.get("id_number") or "").strip()
    # ФИО -> фамилия / имя / отчество
    fio = str(fields.get("full_name") or "").strip()
    parts = fio.split()
    if len(parts) >= 1:
        rec["surname"] = parts[0]
    if len(parts) >= 2:
        rec["first_name"] = parts[1]
    if len(parts) >= 3:
        rec["patronymic"] = " ".join(parts[2:])
    # Дата рождения -> день / месяц / год
    bd = str(fields.get("birth_date") or "").strip()
    d, m, y = _split_ru_date(bd)
    if d:
        rec["birth_day"] = d
    if m:
        rec["birth_month"] = m
    if y:
        rec["birth_year"] = y
    # Гражданство
    if fields.get("citizenship"):
        rec["citizenship"] = str(fields["citizenship"]).strip()
    # Паспорт -> серия + номер
    pas = str(fields.get("passport_number") or "").strip()
    ser, num = _split_passport(pas)
    if ser:
        rec["passport_series"] = ser
    if num:
        rec["passport_number"] = num
    if fields.get("passport_issued_by"):
        rec["passport_issued"] = str(fields["passport_issued_by"]).strip()
    return {k: v for k, v in rec.items() if v}


_RU_MONTHS = {
    "01": "января", "02": "февраля", "03": "марта", "04": "апреля",
    "05": "мая", "06": "июня", "07": "июля", "08": "августа",
    "09": "сентября", "10": "октября", "11": "ноября", "12": "декабря",
}


def _split_ru_date(s: str):
    """'01.01.2008' | '2008-01-01' | '1 января 2008' -> (day, month_word, year)."""
    s = (s or "").strip()
    if not s:
        return "", "", ""
    import re
    m = re.match(r"^\s*(\d{1,2})[.\-/](\d{1,2})[.\-/](\d{2,4})\s*$", s)
    if m:
        d, mo, y = m.group(1), m.group(2), m.group(3)
        return d.zfill(2), _RU_MONTHS.get(mo.zfill(2), mo), y
    m = re.match(r"^\s*(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})\s*$", s)
    if m:
        y, mo, d = m.group(1), m.group(2), m.group(3)
        return d.zfill(2), _RU_MONTHS.get(mo.zfill(2), mo), y
    # уже словами — оставить как есть в поле дня
    return s, "", ""


def _split_passport(s: str):
    """'AB1234567' | 'AB 1234567' -> ('AB', '1234567')."""
    import re
    s = (s or "").strip().replace(" ", "")
    m = re.match(r"^([A-Za-zА-Яа-я]{1,3})\s*(\d{5,})$", s)
    if m:
        return m.group(1).upper(), m.group(2)
    return "", s


def _f19_helpers(c, zw, zh):
    """Рисующие замыкания в системе координат зоны (mm от верх-лев)."""
    DARK = (0.10, 0.10, 0.16)
    GREY = (0.36, 0.36, 0.42)
    INK = (0.03, 0.06, 0.32)
    SHADE = (0.90, 0.90, 0.91)

    def X(mm):
        return mm * MM

    def Y(mm_top):
        return zh - mm_top * MM

    def hline(x1, x2, ytop, w=0.5):
        c.setLineWidth(w)
        c.setStrokeColorRGB(*DARK)
        c.line(X(x1), Y(ytop), X(x2), Y(ytop))

    def vline(x, y1, y2, w=0.5):
        c.setLineWidth(w)
        c.setStrokeColorRGB(*DARK)
        c.line(X(x), Y(y1), X(x), Y(y2))

    def shade(x1, yt1, x2, yt2):
        c.setFillColorRGB(*SHADE)
        c.rect(X(x1), Y(yt2), X(x2) - X(x1), Y(yt1) - Y(yt2), fill=1, stroke=0)

    def lbl(x, ybase, s, size=6.0, bold=False):
        c.setFillColorRGB(*DARK)
        c.setFont(_font(bold), size)
        c.drawString(X(x), Y(ybase), s)

    def cap(cx, ybase, s, size=4.2):
        c.setFillColorRGB(*GREY)
        c.setFont(_font(False), size)
        c.drawCentredString(X(cx), Y(ybase), s)

    def val(x, ybase, s, size=7.5, bold=True):
        if s is None or str(s) == "":
            return
        c.setFillColorRGB(*INK)
        c.setFont(_font(bold), size)
        c.drawString(X(x), Y(ybase), str(s))

    def cval(cx, ybase, s, size=7.5, bold=True):
        if s is None or str(s) == "":
            return
        c.setFillColorRGB(*INK)
        c.setFont(_font(bold), size)
        c.drawCentredString(X(cx), Y(ybase), str(s))

    return X, Y, hline, vline, lbl, cap, val, cval, shade


def _g(rec, key):
    return str((rec or {}).get(key) or "")


def _draw_forma19_front(c, zw, zh, rec):
    """ЛИЦЕВАЯ сторона Формы 19 (поля 1–9). Габарит: 2..103 × 2..143 мм."""
    X, Y, hline, vline, lbl, cap, val, cval, shade = _f19_helpers(c, zw, zh)
    G = _g
    L, R, T, B = 2.0, 103.0, 2.0, 143.0
    LX = 30.0    # верхние строки: label|значение
    BX1 = 18.0   # блок: правый край объединённой левой колонки
    BX2 = 48.0   # блок: правый край под-label-колонки (начало значения)
    PG = 43.0
    GV = 66.0
    PB = 17.0

    def cb(a, b):
        return (a + b) / 2.0 + 0.9

    # --- серые заливки (label-ячейки) ---
    shade(L, 11.5, LX, 38.2)            # идент. номер + строки 1-4
    shade(L, 38.2, BX1, 58.9)           # 5 — объединённая левая
    shade(BX1, 38.2, BX2, 58.9)         # 5 — под-label
    shade(L, 58.9, BX1, 64.6)           # 6. Пол
    shade(PG, 58.9, GV, 64.6)           # 7. Гражданство
    shade(L, 64.6, BX1, 92.9)           # 8 — объединённая левая
    shade(BX1, 64.6, BX2, 88.0)         # 8 — под-label
    shade(L, 101.0, BX1, 124.0)         # 9 — объединённая левая
    shade(BX1, 101.0, BX2, 124.0)       # 9 — под-label
    shade(L, 138.25, 25.0, 143.0)       # Другие причины

    # --- внешняя рамка ---
    hline(L, R, T, 0.9)
    hline(L, R, B, 0.9)
    vline(L, T, B, 0.9)
    vline(R, T, B, 0.9)

    lbl(82, 1.3, "Форма № 19", 6.0)
    val(4, 1.5, G(rec, "top_date"), 6.5)

    # --- заголовок ---
    hline(L, R, 11.5)
    vline(PB, T, 11.5)
    lbl(6.0, 9.0, "П", 12, bold=True)
    cval((PB + R) / 2, 8.8, "АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ", 9.5, bold=True)

    # --- идентификационный номер (14 ячеек) ---
    hline(L, R, 16.9)
    vline(LX, 11.5, 38.2)
    lbl(4, cb(11.5, 16.9), "Идентификационный номер", 5.6)
    ncell = 14
    cw = (R - LX) / ncell
    for i in range(1, ncell):
        vline(LX + i * cw, 11.5, 16.9, 0.4)
    idn = G(rec, "id_number")
    for i, ch in enumerate(idn[:ncell]):
        cval(LX + (i + 0.5) * cw, cb(11.5, 16.9), ch, 7.5)

    # --- 1..3 (справа — объединённый бокс) ---
    hline(L, R, 22.5)
    lbl(4, cb(16.9, 22.5), "1. Фамилия", 5.8)
    val(LX + 2, cb(16.9, 22.5), G(rec, "surname"), 7.5)
    vline(88, 16.9, 22.5)
    hline(L, R, 28.2)
    lbl(4, cb(22.5, 28.2), "2. Собственное имя", 5.8)
    val(LX + 2, cb(22.5, 28.2), G(rec, "first_name"), 7.5)
    vline(70, 22.5, 28.2)
    hline(L, R, 32.7)
    lbl(4, cb(28.2, 32.7), "3. Отчество", 5.8)
    val(LX + 2, cb(28.2, 32.7), G(rec, "patronymic"), 7.5)

    # --- 4. дата рождения (день | месяц | год) ---
    hline(L, R, 38.2)
    vline(52, 32.7, 38.2)
    vline(80, 32.7, 38.2)
    lbl(4, cb(32.7, 38.2), "4. Дата рождения", 5.8)
    val(LX + 2, cb(32.7, 38.2), G(rec, "birth_day"), 7.5)
    cval(66, cb(32.7, 38.2), G(rec, "birth_month"), 7.5)
    cval(91.5, cb(32.7, 38.2), G(rec, "birth_year"), 7.5)

    # --- 5. место рождения (объединённая левая; линии подстрок только BX1..R) ---
    b5 = [38.2, 44.1, 49.5, 54.4, 58.9]
    vline(BX1, 38.2, 58.9)
    vline(BX2, 38.2, 58.9)
    for yb in b5[1:-1]:
        hline(BX1, R, yb)
    hline(L, R, 58.9)
    lbl(4, 47.3, "5. Место", 6.0)
    lbl(4, 50.6, "рождения", 6.0)
    sub5 = ["обл. (край, республика)", "район", "город (пгт)", "село (деревня)"]
    k5 = ["bp_obl", "bp_raion", "bp_city", "bp_village"]
    for i, (s, k) in enumerate(zip(sub5, k5)):
        yb = cb(b5[i], b5[i + 1])
        lbl(BX1 + 1.5, yb, s, 5.4)
        val(BX2 + 2, yb, G(rec, k), 7.0)

    # --- 6. пол | 7. гражданство ---
    hline(L, R, 64.6)
    vline(BX1, 58.9, 64.6)
    vline(PG, 58.9, 64.6)
    vline(GV, 58.9, 64.6)
    lbl(4, cb(58.9, 64.6), "6. Пол", 6.0)
    cval((BX1 + PG) / 2, cb(58.9, 64.6), G(rec, "sex"), 7.5)
    lbl(PG + 2, cb(58.9, 64.6), "7. Гражданство", 6.0)
    val(GV + 2, cb(58.9, 64.6), G(rec, "citizenship"), 7.5)

    # --- 8. место жительства (объединённая левая на всю высоту блока) ---
    b8 = [64.6, 70.2, 75.1, 79.6, 83.2, 88.0]
    vline(BX1, 64.6, 92.9)
    vline(BX2, 64.6, 88.0)
    for yb in b8[1:]:
        hline(BX1, R, yb)
    hline(L, R, 92.9)
    lbl(4, 77.5, "8. Место", 6.0)
    lbl(4, 80.8, "жительства", 6.0)
    sub8 = ["обл. (республика)", "район", "город (пгт)", "село (деревня)", "улица"]
    k8 = ["res_obl", "res_raion", "res_city", "res_village", "res_street"]
    for i, (s, k) in enumerate(zip(sub8, k8)):
        yb = cb(b8[i], b8[i + 1])
        lbl(BX1 + 1.5, yb, s, 5.4)
        val(BX2 + 2, yb, G(rec, k), 7.0)
    # дом / корпус / квартира
    vline(45, 88.0, 92.9)
    vline(75, 88.0, 92.9)
    ycb = cb(88.0, 92.9)
    lbl(BX1 + 2, ycb, "дом", 5.6)
    val(29, ycb, G(rec, "res_house"), 7.0)
    lbl(47, ycb, "корпус", 5.6)
    val(61, ycb, G(rec, "res_korpus"), 7.0)
    lbl(77, ycb, "квартира", 5.6)
    val(92, ycb, G(rec, "res_apartment"), 7.0)

    # --- орган регистрации ---
    hline(L, R, 101.0)
    val(6, 98.8, G(rec, "reg_authority"), 7.0)
    cap(52, 100.4, "указать орган, оформивший регистрацию", 4.4)

    # --- 9. откуда прибыл (объединённая левая) ---
    b9 = [101.0, 106.1, 110.6, 115.2, 119.6, 124.0]
    vline(BX1, 101.0, 124.0)
    vline(BX2, 101.0, 124.0)
    for yb in b9[1:-1]:
        hline(BX1, R, yb)
    hline(L, R, 124.0)
    lbl(4, 109.5, "9. Откуда", 6.0)
    lbl(4, 112.8, "прибыл и", 6.0)
    lbl(4, 116.1, "когда", 6.0)
    sub9 = ["обл. (край, республика)", "район", "город (пгт)", "село (деревня)", "дата прибытия"]
    k9 = ["from_obl", "from_raion", "from_city", "from_village", "arrival_date"]
    for i, (s, k) in enumerate(zip(sub9, k9)):
        yb = cb(b9[i], b9[i + 1])
        lbl(BX1 + 1.5, yb, s, 5.4)
        val(BX2 + 2, yb, G(rec, k), 7.0)

    # --- переехал / изменил / другие ---
    hline(L, R, 128.75)
    lbl(4, cb(124.0, 128.75), "Переехал в том же населённом пункте с улицы", 6.0)
    val(72, cb(124.0, 128.75), G(rec, "moved_street"), 7.0)
    hline(L, R, 133.5)
    vline(30, 128.75, 133.5)
    vline(62, 128.75, 133.5)
    ymv = cb(128.75, 133.5)
    lbl(4, ymv, "дом", 6.0)
    val(14, ymv, G(rec, "moved_house"), 7.0)
    lbl(33, ymv, "корпус", 6.0)
    val(46, ymv, G(rec, "moved_korpus"), 7.0)
    lbl(65, ymv, "квартира", 6.0)
    val(85, ymv, G(rec, "moved_apartment"), 7.0)
    hline(L, R, 138.25)
    lbl(4, cb(133.5, 138.25), "Изменил фамилию, собственное имя или отчество с", 6.0)
    val(80, cb(133.5, 138.25), G(rec, "name_changed_from"), 7.0)
    cap(82, 140.6, "указать прежние данные", 4.4)
    lbl(4, cb(138.25, 143.0), "Другие причины", 6.0)
    val(27, cb(138.25, 143.0), G(rec, "other_reasons"), 7.0)



def _draw_forma19_back(c, zw, zh, rec):
    """ОБОРОТНАЯ сторона Формы 19 (поля 10–15). Габарит идентичен лицевой."""
    X, Y, hline, vline, lbl, cap, val, cval, shade = _f19_helpers(c, zw, zh)
    G = _g
    L, R, T, B = 2.0, 103.0, 2.0, 143.0

    # --- серые заливки ---
    shade(L, T, 27.0, 8.2)              # 10 label
    shade(L, 8.2, R, 11.7)             # caption
    shade(L, 15.1, 40.0, 21.0)         # 11 label
    shade(L, 21.0, R, 24.3)           # caption
    shade(L, 30.8, 40.0, 41.3)         # 12 label
    shade(44.7, 30.8, 51.8, 41.3)      # «номер»
    shade(85.0, 30.8, R, 41.3)         # «выдан»
    shade(L, 41.3, R, 44.7)           # caption
    shade(L, 59.0, R, 68.3)           # шапка таблицы
    shade(L, 112.2, 52.0, 119.1)       # 14 label
    shade(L, 119.1, 48.0, 125.3)       # подпись label
    shade(L, 125.3, R, 131.4)         # 15 label
    shade(L, 136.1, R, 143.0)         # дата/подпись

    # --- внешняя рамка ---
    hline(L, R, T, 0.9)
    hline(L, R, B, 0.9)
    vline(L, T, B, 0.9)
    vline(R, T, B, 0.9)

    # --- 10. цель приезда ---
    hline(L, R, 8.2)
    vline(27.0, T, 8.2)
    lbl(4, 6.6, "10. Цель приезда", 6.0)
    val(29, 6.6, G(rec, "purpose"), 7.5)
    hline(L, R, 11.7)
    cap(52, 10.6, "на работу, учебу, к месту жительства и т.п. и на какой срок", 4.4)
    hline(L, R, 15.1)
    val(6, 13.8, G(rec, "purpose_term"), 7.5)

    # --- 11. где и кем работает ---
    hline(L, R, 21.0)
    vline(40.0, 15.1, 21.0)
    lbl(4, 19.4, "11. Где и кем работает", 6.0)
    val(42, 19.4, G(rec, "employment"), 7.5)
    hline(L, R, 24.3)
    cap(52, 23.2, "если не работает, то указать: пенсионер, учащийся, иждивенец и т.п.", 4.4)
    hline(L, R, 30.8)

    # --- 12. паспорт ---
    hline(L, R, 41.3)
    vline(32.7, 30.8, 41.3)
    vline(44.7, 30.8, 41.3)
    vline(51.8, 30.8, 41.3)
    vline(85.0, 30.8, 41.3)
    lbl(4, 35.0, "12. Паспорт, вид на", 6.0)
    lbl(4, 38.5, "жительство, серия", 6.0)
    val(35, 37.0, G(rec, "passport_series"), 7.5)
    lbl(45.5, 37.0, "номер", 5.6)
    val(53, 37.0, G(rec, "passport_number"), 7.0)
    lbl(87, 37.0, "выдан", 6.0)
    hline(L, R, 44.7)
    cap(52, 43.6, "наименование органа внутренних дел", 4.4)
    hline(L, R, 50.6)
    val(6, 48.8, G(rec, "passport_issued"), 7.0)
    lbl(80, 48.8, "20", 6.0)
    hline(85, 93, 48.8)
    lbl(94, 48.8, "г.", 6.0)

    # --- 13. дети до 14 лет ---
    hline(L, R, 59.0)
    lbl(4, 54.0, "13. Вместе с ним (ней) прибыли дети до 14 лет, не имеющие", 5.8)
    lbl(4, 57.5, "паспортов, видов на жительство:", 5.8)
    hline(L, R, 68.3)
    vline(75, 59.0, 104.5)
    vline(86, 59.0, 104.5)
    cval((L + 75) / 2, 64.6, "Фамилия, собственное имя, отчество", 5.4)
    cval((75 + 86) / 2, 64.6, "Пол", 5.4)
    cval((86 + R) / 2, 63.0, "Дата", 5.4)
    cval((86 + R) / 2, 66.4, "рождения", 5.4)
    for yb in [72.83, 77.35, 81.88, 86.4, 90.93, 95.45, 99.98, 104.5]:
        hline(L, R, yb)

    # --- примечание ---
    hline(L, R, 112.2)
    lbl(4, 109.6, "Примечание:", 5.8, bold=True)
    lbl(23, 109.6, "Дети вносятся в адресный листок прибытия только одного из родителей.", 5.4)

    # --- 14. листок составлен ---
    hline(L, R, 119.1)
    vline(52, 112.2, 119.1)
    vline(72, 112.2, 119.1)
    lbl(4, 117.2, "14. Листок составлен", 6.0)
    lbl(80, 117.2, "20", 6.0)
    hline(85, 93, 117.2)
    lbl(94, 117.2, "г.", 6.0)
    hline(L, R, 125.3)
    vline(48, 119.1, 125.3)
    lbl(4, 123.4, "Подпись должностного лица", 6.0)

    # --- 15. сведения проверил ---
    hline(L, R, 131.4)
    lbl(4, 129.5, "15. Сведения проверил и регистрацию оформил", 6.0)
    vline(52, 131.4, 143.0)
    lbl(20, 135.0, "20", 6.0)
    hline(25, 34, 135.0)
    lbl(35, 135.0, "г.", 6.0)
    hline(L, R, 136.1)
    cap(27, 140.2, "дата", 4.6)
    cap(78, 140.2, "подпись", 4.6)



def build_forma19(people, per_sheet=2, duplex_flip="long", copies=2, draw_guides=True, template=None):
    """PDF Формы 19: A4-сетка 2×2. per_sheet = сколько ЧЕЛОВЕК на лист (по 2 копии).
    Порядок страниц: лист1-лицо, лист1-оборот, лист2-лицо, лист2-оборот … —
    для двусторонней печати каждый физический лист = 2 подряд идущие страницы PDF.
    duplex_flip: 'long' (переворот по длинному краю) | 'short' (по короткому).
    """
    from reportlab.pdfgen import canvas

    _ensure_fonts()
    zw = FORMA19_MM[0] * MM   # 105
    zh = FORMA19_MM[1] * MM   # 145
    pw, ph = 210 * MM, 297 * MM
    cols, rows = 2, 2
    scale, sw, sh, side_margin, top_margin = _fit_grid(pw, ph, zw, zh, cols, rows)

    people = list(people or [])
    if not people:
        people = [{}]
    ppl_per_sheet = 2  # фиксировано: 2 человека (2×2 = по 2 копии)
    duplex_flip = (duplex_flip or "long").lower()
    tpl_by_page = _forma_tpl_by_page(template) if template else None

    def cell_origin(col, row):
        x0 = side_margin + col * sw
        y_top = top_margin + row * sh
        y0 = ph - (y_top + sh)
        return x0, y0

    # позиции ячеек: 0=TL,1=TR (верхний ряд), 2=BL,3=BR (нижний ряд)
    CELLS = [(0, 0), (1, 0), (0, 1), (1, 1)]

    def draw_page(c, sheet_people, is_back):
        # какому человеку какие 2 ячейки достаются
        # лицо: person0 -> верх (0,1); person1 -> низ (2,3)
        # оборот long: так же; оборот short: ряды меняются местами
        order = [0, 1]
        if is_back and duplex_flip == "short":
            order = [1, 0]
        cell_person = {}
        cell_person[CELLS[0]] = order[0]
        cell_person[CELLS[1]] = order[0]
        cell_person[CELLS[2]] = order[1]
        cell_person[CELLS[3]] = order[1]
        for (col, row), pidx in cell_person.items():
            if pidx >= len(sheet_people):
                continue
            rec = sheet_people[pidx]
            x0, y0 = cell_origin(col, row)
            c.saveState()
            c.translate(x0, y0)
            c.scale(scale, scale)
            if draw_guides:
                c.setStrokeColorRGB(0.75, 0.75, 0.82)
                c.setLineWidth(0.3)
                c.setDash(2, 2)
                c.rect(0, 0, zw, zh, stroke=1, fill=0)
                c.setDash()
            if is_back:
                if tpl_by_page:
                    _draw_forma_template_card(c, tpl_by_page, rec, zw, zh, True)
                else:
                    _draw_forma19_back(c, zw, zh, rec)
            else:
                if tpl_by_page:
                    _draw_forma_template_card(c, tpl_by_page, rec, zw, zh, False)
                else:
                    _draw_forma19_front(c, zw, zh, rec)
            c.restoreState()
        c.showPage()

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))
    for start in range(0, len(people), ppl_per_sheet):
        chunk = people[start:start + ppl_per_sheet]
        draw_page(c, chunk, is_back=False)   # лицо
        draw_page(c, chunk, is_back=True)    # оборот
    c.save()
    buf.seek(0)
    return buf.getvalue()


# ==========================================================================
#  ФОРМА 24 — «Талон миграционного учёта к адресному листку прибытия» («П»)
#  Та же геометрия, что и Форма 19 (карта 105×145, сетка 2×2, лицо+оборот).
# ==========================================================================
FORMA24_FIELDS = [
    {"group": "Идентификация", "fields": [
        {"key": "top_date", "label": "Дата вверху (над бланком)"},
        {"key": "surname", "label": "1. Фамилия"},
        {"key": "first_name", "label": "2. Собственное имя"},
        {"key": "patronymic", "label": "3. Отчество"},
        {"key": "birth_day", "label": "4. Дата рождения — день"},
        {"key": "birth_month", "label": "4. Месяц (словом)"},
        {"key": "birth_year", "label": "4. Год"},
        {"key": "sex", "label": "6. Пол (1=муж, 2=жен)"},
        {"key": "nationality", "label": "7. Национальность"},
        {"key": "citizenship", "label": "8. Гражданство"},
    ]},
    {"group": "5. Место рождения", "fields": [
        {"key": "bp_obl", "label": "обл. (край, республика)"},
        {"key": "bp_raion", "label": "район"},
        {"key": "bp_city", "label": "город (пгт)"},
        {"key": "bp_village", "label": "село (деревня)"},
    ]},
    {"group": "9. Место жительства", "fields": [
        {"key": "res_obl", "label": "обл. (республика)"},
        {"key": "res_raion", "label": "район"},
        {"key": "res_city", "label": "город (пгт)"},
        {"key": "res_village", "label": "село (деревня)"},
    ]},
    {"group": "10. Откуда прибыл и когда", "fields": [
        {"key": "from_obl", "label": "обл. (край, республика)"},
        {"key": "from_raion", "label": "район"},
        {"key": "from_city", "label": "город (пгт)"},
        {"key": "from_village", "label": "село (деревня)"},
        {"key": "arrival_date", "label": "дата прибытия"},
        {"key": "lived_since", "label": "проживал там с"},
    ]},
    {"group": "11. Цель приезда", "fields": [
        {"key": "purpose_choice", "label": "Цель (1=на работу, 2=на обучение)"},
        {"key": "other_purpose", "label": "другая цель (указать)"},
        {"key": "term", "label": "на какой срок"},
    ]},
    {"group": "Оборот", "fields": [
        {"key": "prev_work", "label": "12. Где и кем работал по прежнему месту"},
        {"key": "education", "label": "13. Образование (1..7)"},
        {"key": "marital", "label": "14. Семейное положение (1..4)"},
        {"key": "spouse_together", "label": "14. Прибыл с супругой(ом) (5=да, 6=нет)"},
        {"key": "children_count", "label": "15. Детей до 14 лет (сколько)"},
        {"key": "passport_valid_until", "label": "Паспорт: срок действия"},
    ]},
]
FORMA24_FIELD_KEYS = [f["key"] for g in FORMA24_FIELDS for f in g["fields"]]


def forma24_from_contract(fields: dict) -> dict:
    return forma19_from_contract(fields)


def _ys(top, raw, total):
    k = total / float(sum(raw))
    ys = [top]
    for h in raw:
        ys.append(ys[-1] + h * k)
    return ys


def _draw_forma24_front(c, zw, zh, rec):
    X, Y, hline, vline, lbl, cap, val, cval, shade = _f19_helpers(c, zw, zh)
    G = _g
    L, R, T = 2.0, 103.0, 2.0
    LX, BX1, BX2, PB = 30.0, 18.0, 48.0, 17.0

    def cb(a, b):
        return (a + b) / 2.0 + 0.9

    def underline(x, ybase, text, on, size=6.0):
        lbl(x, ybase, text, size)
        if on:
            w = c.stringWidth(text, _font(False), size) / MM
            hline(x, x + w, ybase + 1.1, 0.6)

    raw = [1.7, 1.05, 1.05, 1.05, 1.15, 0.95, 0.95, 0.95, 0.95,
           1.1, 1.1, 0.95, 0.95, 0.95, 0.95, 0.9, 0.9, 0.9, 0.9, 0.9, 0.9, 1.1, 1.0, 1.0]
    y = _ys(2.0, raw, 141.0)
    B = y[-1]

    # заливки — серым только ячейки-надписи одиночных строк; группы 5/9/10 остаются белыми
    shade(L, y[1], LX, y[5])           # надписи строк 1..4
    shade(BX1, y[5], BX2, y[9])        # 5: подписи обл/район/город/село
    shade(L, y[9], 85, y[10])          # строка «6. Пол ... 7. Национальность» (кроме значения)
    shade(L, y[10], BX1, y[11])        # «8. Гражданство»
    shade(BX1, y[11], BX2, y[15])      # 9: подписи обл/район/город/село
    shade(BX1, y[15], BX2, y[21])      # 10: обл/район/город/село/дата прибытия/проживал там с
    shade(L, y[21], 48, y[22])         # «11. Цель приезда»
    shade(L, y[22], 38, y[23]); shade(L, y[23], 38, y[24])  # «другая цель» / «на какой срок»

    hline(L, R, T, 0.9); hline(L, R, B, 0.9); vline(L, T, B, 0.9); vline(R, T, B, 0.9)
    lbl(82, 1.3, "Форма 24", 6.0)
    val(4, 1.5, G(rec, "top_date"), 6.5)

    # header
    hline(L, R, y[1]); vline(PB, T, y[1])
    lbl(5.5, cb(T, y[1]) + 1.2, "П", 12, bold=True)
    cval((PB + R) / 2, cb(T, y[1]) - 0.6, "ТАЛОН МИГРАЦИОННОГО УЧЕТА", 7.2, bold=True)
    cval((PB + R) / 2, cb(T, y[1]) + 2.6, "К АДРЕСНОМУ ЛИСТКУ ПРИБЫТИЯ", 7.2, bold=True)

    # 1..3
    for idx, (lab, key) in enumerate([("1. Фамилия", "surname"), ("2. Собственное имя", "first_name"), ("3. Отчество", "patronymic")]):
        yb = y[idx + 2]
        hline(L, R, yb)
        lbl(4, cb(y[idx + 1], yb), lab, 5.8)
        val(LX + 2, cb(y[idx + 1], yb), G(rec, key), 7.5)
    vline(LX, y[1], y[5])
    # 4 дата
    hline(L, R, y[5]); vline(52, y[4], y[5]); vline(80, y[4], y[5])
    lbl(4, cb(y[4], y[5]), "4. Дата рождения", 5.8)
    val(LX + 2, cb(y[4], y[5]), G(rec, "birth_day"), 7.5)
    cval(66, cb(y[4], y[5]), G(rec, "birth_month"), 7.5)
    cval(91.5, cb(y[4], y[5]), G(rec, "birth_year"), 7.5)

    # 5 место рождения
    vline(BX1, y[5], y[9]); vline(BX2, y[5], y[9])
    for i in (6, 7, 8):
        hline(BX1, R, y[i])
    hline(L, R, y[9])
    lbl(4, cb(y[5], y[9]) - 1.6, "5. Место", 6.0)
    lbl(4, cb(y[5], y[9]) + 1.6, "рождения", 6.0)
    for i, (s, k) in enumerate([("обл. (край, республика)", "bp_obl"), ("район", "bp_raion"), ("город (пгт)", "bp_city"), ("село (деревня)", "bp_village")]):
        yb = cb(y[5 + i], y[6 + i])
        lbl(BX1 + 1.5, yb, s, 5.4); val(BX2 + 2, yb, G(rec, k), 7.0)

    # 6 пол | 7 национальность
    hline(L, R, y[10]); vline(30, y[9], y[10]); vline(58, y[9], y[10]); vline(85, y[9], y[10])
    yb = cb(y[9], y[10])
    lbl(4, yb, "6. Пол (подчеркнуть)", 5.0)
    sv = G(rec, "sex").lower()
    underline(31, yb, "муж. - 1", sv in ("1", "м", "муж", "муж.", "мужской"), 5.6)
    underline(45, yb, "жен. - 2", sv in ("2", "ж", "жен", "жен.", "женский"), 5.6)
    lbl(59, yb, "7. Национальность", 5.0); val(87, yb, G(rec, "nationality"), 6.5)
    # 8 гражданство
    hline(L, R, y[11]); vline(BX1, y[10], y[11])
    lbl(4, cb(y[10], y[11]), "8. Гражданство", 5.0); val(BX1 + 2, cb(y[10], y[11]), G(rec, "citizenship"), 7.0)

    # 9 место жительства
    vline(BX1, y[11], y[15]); vline(BX2, y[11], y[15])
    for i in (12, 13, 14):
        hline(BX1, R, y[i])
    hline(L, R, y[15])
    lbl(4, cb(y[11], y[15]) - 1.6, "9. Место", 6.0)
    lbl(4, cb(y[11], y[15]) + 1.6, "жительства", 6.0)
    for i, (s, k) in enumerate([("обл. (республика)", "res_obl"), ("район", "res_raion"), ("город (пгт)", "res_city"), ("село (деревня)", "res_village")]):
        yb = cb(y[11 + i], y[12 + i])
        lbl(BX1 + 1.5, yb, s, 5.4); val(BX2 + 2, yb, G(rec, k), 7.0)

    # 10 откуда прибыл
    vline(BX1, y[15], y[21]); vline(BX2, y[15], y[21])
    for i in (16, 17, 18, 19, 20):
        hline(BX1, R, y[i])
    hline(L, R, y[21])
    lbl(4, cb(y[15], y[21]) - 2.6, "10. Отку-", 6.0)
    lbl(4, cb(y[15], y[21]), "да прибыл", 6.0)
    lbl(4, cb(y[15], y[21]) + 2.6, "и когда", 6.0)
    for i, (s, k) in enumerate([("обл. (край, республика)", "from_obl"), ("район", "from_raion"), ("город (пгт)", "from_city"), ("село (деревня)", "from_village"), ("дата прибытия", "arrival_date"), ("проживал там с", "lived_since")]):
        yb = cb(y[15 + i], y[16 + i])
        lbl(BX1 + 1.5, yb, s, 5.4); val(BX2 + 2, yb, G(rec, k), 7.0)

    # 11 цель приезда
    hline(L, R, y[22]); vline(48, y[21], y[22]); vline(76, y[21], y[22])
    yb = cb(y[21], y[22])
    lbl(4, yb, "11. Цель приезда (подчеркнуть)", 5.0)
    pc = G(rec, "purpose_choice").lower()
    underline(49, yb, "на работу - 1", pc in ("1",) or "работ" in pc, 5.6)
    underline(77, yb, "на обучение - 2", pc in ("2",) or ("обуч" in pc or "учеб" in pc), 5.6)
    hline(L, R, y[23]); vline(38, y[22], y[23]); lbl(4, cb(y[22], y[23]), "другая цель (указать)", 5.6); val(40, cb(y[22], y[23]), G(rec, "other_purpose"), 7.0)
    vline(38, y[23], y[24]); lbl(4, cb(y[23], y[24]), "на какой срок", 5.8); val(40, cb(y[23], y[24]), G(rec, "term"), 7.0)


def _draw_forma24_back(c, zw, zh, rec):
    X, Y, hline, vline, lbl, cap, val, cval, shade = _f19_helpers(c, zw, zh)
    G = _g
    L, R, T = 2.0, 103.0, 2.0

    def cb(a, b):
        return (a + b) / 2.0 + 0.9

    def underline(x, ybase, text, on, size=5.6):
        lbl(x, ybase, text, size)
        if on:
            w = c.stringWidth(text, _font(False), size) / MM
            hline(x, x + w, ybase + 1.1, 0.6)

    raw = [4.5, 4.5, 8, 2.5,      # 12: label / пояснение(2 строки) / value / gap -> y1..y4
           6, 6, 6,               # 13 три строки                      -> y5,y6,y7
           6, 6, 6,               # 14 три строки                      -> y8,y9,y10
           7, 2.5,                # 15 строка / пояснение              -> y11,y12
           6,                     # шапка таблицы                      -> y13
           5.5, 5.5, 5.5, 5.5, 5.5,  # 5 строк таблицы детей           -> y14..y18
           6, 6,                  # 16 две строки                      -> y19,y20
           5, 6, 3.5]             # 17: label / дата-строка / подписи   -> y21,y22,y23
    y = _ys(2.0, raw, 141.0)
    B = y[-1]

    # ---- заливки (рисуем первыми, под линиями) ----
    shade(L, T, R, y[1])             # 12 «Где и кем работал» (надпись) серым
    shade(L, y[4], 46, y[5])         # 13 «Образование (подчеркнуть):» надпись
    shade(L, y[7], 62, y[8])         # 14 «Семейное положение (подчеркнуть)» надпись
    shade(L, y[10], 62, y[11])       # 15 левая ячейка
    shade(L, y[12], R, y[13])        # шапка таблицы
    shade(L, y[18], 55, y[19])       # "16. Талон составлен" label
    shade(L, y[19], 55, y[20])       # "Подпись должностного лица" label
    shade(L, y[20], R, y[21])        # "17. Сведения проверил..." строка
    shade(L, y[22], R, B)            # нижние подписи

    hline(L, R, T, 0.9); hline(L, R, B, 0.9); vline(L, T, B, 0.9); vline(R, T, B, 0.9)

    # ===== 12. Где и кем работал =====
    hline(L, R, y[1])
    lbl(4, cb(T, y[1]), "12. Где и кем работал по прежнему месту жительства", 5.8)
    hline(L, R, y[2])
    cap((L + R) / 2, y[1] + 1.9, "наименование предприятия, организации, учреждения, должности", 3.6)
    cap((L + R) / 2, y[2] - 0.6, "если не работает, то указать пенсионер, учащийся, иждивенец и т.п.", 3.6)
    val(6, cb(y[2], y[3]) + 1.0, G(rec, "prev_work"), 7.0)
    hline(L, R, y[3])
    hline(L, R, y[4])   # нижняя граница пустой полосы

    # ===== 13. Образование (подчеркнуть) =====
    ed = G(rec, "education").strip()
    # строка a: label | высшее-1 | среднее специальное-2
    hline(L, R, y[5]); vline(46, y[4], y[5]); vline(74, y[4], y[5])
    ra = cb(y[4], y[5])
    lbl(4, ra, "13. Образование (подчеркнуть):", 5.4)
    underline(49, ra, "высшее - 1", ed == "1", 5.4)
    underline(76, ra, "среднее специальное - 2", ed == "2", 5.0)
    # строка b: проф.-техническое-3 | общее среднее-4 | общее базовое-5
    hline(L, R, y[6]); vline(40, y[5], y[6]); vline(72, y[5], y[6])
    rb = cb(y[5], y[6])
    underline(4, rb, "профессионально-техническое - 3", ed == "3", 4.7)
    underline(42, rb, "общее среднее - 4", ed == "4", 5.0)
    underline(74, rb, "общее базовое - 5", ed == "5", 5.0)
    # строка c: общее начальное-6 | не имеет начального-7
    hline(L, R, y[7]); vline(44, y[6], y[7])
    rc = cb(y[6], y[7])
    underline(4, rc, "общее начальное - 6", ed == "6", 5.0)
    underline(46, rc, "не имеет начального - 7", ed == "7", 5.0)

    # ===== 14. Семейное положение (подчеркнуть) =====
    mv = G(rec, "marital").strip()
    sp = G(rec, "spouse_together").strip()
    # строка a: label | состоит в браке-1
    hline(L, R, y[8]); vline(62, y[7], y[8])
    r14a = cb(y[7], y[8])
    lbl(4, r14a, "14. Семейное положение (подчеркнуть)", 5.2)
    underline(64, r14a, "состоит в браке - 1", mv == "1", 5.2)
    # строка b: никогда не состоял(а) в браке-2 | вдовец(а)-3 | разведен(а)-4
    hline(L, R, y[9]); vline(44, y[8], y[9]); vline(68, y[8], y[9])
    r14b = cb(y[8], y[9])
    underline(4, r14b, "никогда не состоял(а) в браке - 2", mv == "2", 4.7)
    underline(46, r14b, "вдовец(а) - 3", mv == "3", 5.0)
    underline(70, r14b, "разведен(а) - 4", mv == "4", 5.0)
    # строка c: Если состоит в браке, то прибыл вместе с супругой(ом) | да-5 | нет-6
    hline(L, R, y[10]); vline(76, y[9], y[10]); vline(90, y[9], y[10])
    r14c = cb(y[9], y[10])
    lbl(4, r14c, "Если состоит в браке, то прибыл вместе с супругой(ом)", 4.7)
    underline(78, r14c, "да - 5", sp == "5", 5.0)
    underline(92, r14c, "нет - 6", sp == "6", 5.0)

    # ===== 15. Дети до 14 лет =====
    hline(L, R, y[11]); vline(62, y[10], y[11])
    r15 = cb(y[10], y[11])
    lbl(4, r15, "15. Вместе с ним (ней) прибыли дети до 14 лет", 5.2)
    y_sk = y[10] + 0.62 * (y[11] - y[10])   # линия над словом «сколько»
    hline(62, R, y_sk)
    cval(82.5, cb(y_sk, y[11]) + 0.2, "сколько", 5.0, bold=False)
    cval(82.5, cb(y[10], y_sk) + 0.4, G(rec, "children_count"), 7.5)
    hline(L, R, y[12])
    cap((L + R) / 2, cb(y[11], y[12]) + 0.2,
        "Сколько – указывается в талоне каждого из родителей, "
        "поименно дети вносятся в талон только одного из них", 3.4)

    # ===== таблица детей =====
    hline(L, R, y[13]); vline(62, y[12], y[18]); vline(82, y[12], y[18])
    hval = cb(y[12], y[13])
    cval(32, hval, "Фамилия, собственное имя, отчество", 4.8, bold=False)
    cval(72, hval - 1.4, "Пол", 4.6, bold=False); cval(72, hval + 1.6, "(подчеркнуть)", 4.4, bold=False)
    cval(92.5, hval - 1.4, "Дата", 4.6, bold=False); cval(92.5, hval + 1.6, "рождения", 4.6, bold=False)
    for i in (14, 15, 16, 17, 18):
        hline(L, R, y[i])
        cap(72, cb(y[i - 1], y[i]) + 0.3, "муж.-1, жен.-2", 4.6)

    # ===== 16. Талон составлен =====
    hline(L, R, y[19]); vline(55, y[18], y[19]); vline(78, y[18], y[19])
    r16 = cb(y[18], y[19])
    lbl(4, r16, "16. Талон составлен", 5.8)
    lbl(82, r16, "20", 5.8); hline(86, 96, r16 + 0.7); lbl(97, r16, "г.", 5.8)
    hline(L, R, y[20]); vline(55, y[19], y[20])
    lbl(4, cb(y[19], y[20]), "Подпись должностного лица", 5.6)

    # ===== 17. Сведения проверил =====
    hline(L, R, y[21])
    lbl(4, cb(y[20], y[21]), "17. Сведения проверил и регистрацию оформил", 5.8)
    # четыре ячейки снизу: дата | месяц | год | подпись
    for xv in (20, 38, 56):
        vline(xv, y[21], B)
    hline(L, R, y[22])
    cap(11, cb(y[22], B) + 0.3, "дата", 4.4)
    cap(29, cb(y[22], B) + 0.3, "месяц", 4.4)
    cap(47, cb(y[22], B) + 0.3, "год", 4.4)
    cap(79.5, cb(y[22], B) + 0.3, "подпись", 4.4)


def build_forma24(people, duplex_flip="long", draw_guides=True, template=None):
    """PDF Формы 24: как build_forma19, но с отрисовкой талона."""
    from reportlab.pdfgen import canvas
    _ensure_fonts()
    zw = FORMA19_MM[0] * MM
    zh = FORMA19_MM[1] * MM
    pw, ph = 210 * MM, 297 * MM
    scale, sw, sh, side_margin, top_margin = _fit_grid(pw, ph, zw, zh, 2, 2)
    people = list(people or []) or [{}]
    duplex_flip = (duplex_flip or "long").lower()
    tpl_by_page = _forma_tpl_by_page(template) if template else None

    def origin(col, row):
        return side_margin + col * sw, ph - (top_margin + row * sh + sh)

    CELLS = [(0, 0), (1, 0), (0, 1), (1, 1)]

    def page(c, chunk, back):
        order = [1, 0] if (back and duplex_flip == "short") else [0, 1]
        cp = {CELLS[0]: order[0], CELLS[1]: order[0], CELLS[2]: order[1], CELLS[3]: order[1]}
        for (col, row), pidx in cp.items():
            if pidx >= len(chunk):
                continue
            x0, y0 = origin(col, row)
            c.saveState(); c.translate(x0, y0); c.scale(scale, scale)
            if draw_guides:
                c.setStrokeColorRGB(0.75, 0.75, 0.82); c.setLineWidth(0.3); c.setDash(2, 2)
                c.rect(0, 0, zw, zh, stroke=1, fill=0); c.setDash()
            if tpl_by_page:
                _draw_forma_template_card(c, tpl_by_page, chunk[pidx], zw, zh, back)
            else:
                (_draw_forma24_back if back else _draw_forma24_front)(c, zw, zh, chunk[pidx])
            c.restoreState()
        c.showPage()

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))
    for s in range(0, len(people), 2):
        chunk = people[s:s + 2]
        page(c, chunk, False)
        page(c, chunk, True)
    c.save()
    buf.seek(0)
    return buf.getvalue()



def build_forma_combined(rec19, rec24, duplex_flip="long", draw_guides=True,
                         tpl19=None, tpl24=None):
    """Один A4-лист: верхний ряд — Форма 19 (2 копии), нижний ряд — Форма 24
    (2 копии). Лицо + оборот для двусторонней печати. Один формат карты 105×145.
    Экономит бумагу: обе формы на одном листе вместо двух."""
    from reportlab.pdfgen import canvas

    _ensure_fonts()
    zw = FORMA19_MM[0] * MM
    zh = FORMA19_MM[1] * MM
    pw, ph = 210 * MM, 297 * MM
    scale, sw, sh, side_margin, top_margin = _fit_grid(pw, ph, zw, zh, 2, 2)
    duplex_flip = (duplex_flip or "long").lower()
    rec19 = rec19 or {}
    rec24 = rec24 or {}
    tpl19_by = _forma_tpl_by_page(tpl19) if tpl19 else None
    tpl24_by = _forma_tpl_by_page(tpl24) if tpl24 else None

    def origin(col, row):
        return side_margin + col * sw, ph - (top_margin + row * sh + sh)

    def draw_card(c, col, row, which, back):
        x0, y0 = origin(col, row)
        c.saveState()
        c.translate(x0, y0)
        c.scale(scale, scale)
        if draw_guides:
            c.setStrokeColorRGB(0.75, 0.75, 0.82)
            c.setLineWidth(0.3)
            c.setDash(2, 2)
            c.rect(0, 0, zw, zh, stroke=1, fill=0)
            c.setDash()
        if which == 19:
            if tpl19_by:
                _draw_forma_template_card(c, tpl19_by, rec19, zw, zh, back)
            else:
                (_draw_forma19_back if back else _draw_forma19_front)(c, zw, zh, rec19)
        else:
            if tpl24_by:
                _draw_forma_template_card(c, tpl24_by, rec24, zw, zh, back)
            else:
                (_draw_forma24_back if back else _draw_forma24_front)(c, zw, zh, rec24)
        c.restoreState()

    def page(c, back):
        # верхний ряд / нижний ряд — какая форма где
        top, bottom = 19, 24
        if back and duplex_flip == "short":
            top, bottom = 24, 19   # при перевороте по короткому краю ряды меняются
        draw_card(c, 0, 0, top, back)
        draw_card(c, 1, 0, top, back)
        draw_card(c, 0, 1, bottom, back)
        draw_card(c, 1, 1, bottom, back)
        c.showPage()

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))
    page(c, False)   # лицо
    page(c, True)    # оборот
    c.save()
    buf.seek(0)
    return buf.getvalue()


# ==========================================================================
#  ГЕНЕРАЦИЯ РЕДАКТИРУЕМЫХ ШАБЛОНОВ ДЛЯ ФОРМ (Ф19 / Ф24) — как в «Заявлении»
#  Идея: прогоняем существующие функции отрисовки через canvas-рекордер и
#  rec-«зонд» (маркеры полей) → получаем список элементов (text/line/rect/field),
#  который затем можно двигать/править в редакторе и рендерить обратно 1:1.
# ==========================================================================
_FLD_A = "\ue000"
_FLD_B = "\ue001"


class _ProbeRec(dict):
    """rec-«зонд»: любое поле возвращает маркер \ue000key\ue001, кроме iter_keys."""
    def __init__(self, iter_keys=()):
        super().__init__()
        self._iter = set(iter_keys or ())

    def get(self, k, default=None):
        if k in self._iter:
            return ""
        return _FLD_A + str(k) + _FLD_B

    def __bool__(self):
        return True

    def __contains__(self, k):
        return True


def _rgbhex(rgb):
    return "#%02x%02x%02x" % (
        max(0, min(255, int(round(rgb[0] * 255)))),
        max(0, min(255, int(round(rgb[1] * 255)))),
        max(0, min(255, int(round(rgb[2] * 255)))),
    )


class _RecorderCanvas:
    """Мимикрирует подмножество reportlab canvas и складывает элементы шаблона.
    Координаты пунктов переводятся в проценты страницы pw×ph (карта 105×145 мм)."""
    def __init__(self, pw, ph):
        self.pw = pw
        self.ph = ph
        self.elems = []
        self._fill = (0, 0, 0)
        self._stroke = (0, 0, 0)
        self._lw = 0.5
        self._font = "AppSans"
        self._size = 9.0

    # --- state ---
    def setFillColorRGB(self, r, g, b):
        self._fill = (r, g, b)

    def setStrokeColorRGB(self, r, g, b):
        self._stroke = (r, g, b)

    def setLineWidth(self, w):
        self._lw = w

    def setFont(self, name, size):
        self._font = name
        self._size = size

    def setDash(self, *a, **k):
        pass

    def saveState(self):
        pass

    def restoreState(self):
        pass

    def stringWidth(self, s, font=None, size=None):
        from reportlab.pdfbase.pdfmetrics import stringWidth as _sw
        try:
            return _sw(str(s), font or self._font, size or self._size)
        except Exception:
            return len(str(s)) * (size or self._size) * 0.5

    def _fontmeta(self):
        n = self._font or ""
        fam = "serif" if "Serif" in n else "sans"
        return fam, ("Bold" in n), ("Italic" in n)

    def _text(self, x, y, s, align):
        s = "" if s is None else str(s)
        if s == "":
            return
        fam, bold, ital = self._fontmeta()
        base = {
            "x": round(x / self.pw * 100, 3),
            "y": round((self.ph - y) / self.ph * 100, 3),
            "align": align, "size": round(self._size, 2),
            "bold": bold, "italic": ital, "font": fam,
            "color": _rgbhex(self._fill),
        }
        if s.startswith(_FLD_A):
            key = s[len(_FLD_A):].split(_FLD_B)[0]
            base.update({"type": "field", "field": key})
        else:
            base.update({"type": "text", "text": s})
        self.elems.append(base)

    def drawString(self, x, y, s):
        self._text(x, y, s, "left")

    def drawCentredString(self, x, y, s):
        self._text(x, y, s, "center")

    def drawCenteredString(self, x, y, s):
        self._text(x, y, s, "center")

    def drawRightString(self, x, y, s):
        self._text(x, y, s, "right")

    def line(self, x1, y1, x2, y2):
        el = {"type": "line", "thickness": round(self._lw, 2), "color": _rgbhex(self._stroke)}
        el["x"] = round(x1 / self.pw * 100, 3)
        el["y"] = round((self.ph - y1) / self.ph * 100, 3)
        if abs(y1 - y2) < 1e-6:
            el["w"] = round((x2 - x1) / self.pw * 100, 3)
        else:
            el["x2"] = round(x2 / self.pw * 100, 3)
            el["y2"] = round((self.ph - y2) / self.ph * 100, 3)
        self.elems.append(el)

    def rect(self, x, y, w, h, fill=0, stroke=1):
        el = {
            "type": "rect",
            "x": round(x / self.pw * 100, 3),
            "y": round((self.ph - (y + h)) / self.ph * 100, 3),
            "w": round(w / self.pw * 100, 3),
            "h": round(h / self.ph * 100, 3),
        }
        if fill:
            el["fill"] = _rgbhex(self._fill)
        if stroke:
            el["stroke"] = _rgbhex(self._stroke)
            el["thickness"] = round(self._lw, 2)
        self.elems.append(el)


def _forma_vals(rec):
    """Значения полей формы: простое приведение к строкам (без спец-логики)."""
    return {k: ("" if v is None else str(v)) for k, v in (rec or {}).items()}


def _build_forma_default_template(front_fn, back_fn, iter_keys=("id_number",),
                                  extra=None):
    """Собрать дефолтный шаблон-элементы формы из функций отрисовки."""
    _ensure_fonts()
    pw = FORMA19_MM[0] * MM
    ph = FORMA19_MM[1] * MM
    elems = []
    for page, fn in ((1, front_fn), (2, back_fn)):
        rec = _RecorderCanvas(pw, ph)
        try:
            fn(rec, pw, ph, _ProbeRec(iter_keys))
        except Exception:
            logger.exception("recorder failed for page %s", page)
        for e in rec.elems:
            e["page"] = page
            elems.append(e)
    if extra:
        for e in extra:
            elems.append(dict(e))
    for i, e in enumerate(elems):
        e["id"] = "el%03d" % i
    return elems


_FORMA19_TPL_DEFAULT = None
_FORMA24_TPL_DEFAULT = None


def get_forma19_default_template():
    global _FORMA19_TPL_DEFAULT
    if _FORMA19_TPL_DEFAULT is None:
        # идентификационный номер (14 ячеек) — одно поле слева от первой ячейки
        extra = [{
            "type": "field", "field": "id_number", "page": 1,
            "x": 29.5, "y": round(15.1 / 145.0 * 100, 3), "align": "left",
            "size": 7.5, "bold": True, "italic": False, "font": "sans", "color": "#0a0d52",
        }]
        _FORMA19_TPL_DEFAULT = _build_forma_default_template(
            _draw_forma19_front, _draw_forma19_back, iter_keys=("id_number",), extra=extra)
    import copy
    return copy.deepcopy(_FORMA19_TPL_DEFAULT)


_FORMA24_UL_OPTS = [
    ("муж. - 1", "sex", ["1", "м", "муж", "муж.", "мужской"], []),
    ("жен. - 2", "sex", ["2", "ж", "жен", "жен.", "женский"], []),
    ("на работу - 1", "purpose_choice", ["1"], ["работ"]),
    ("на обучение - 2", "purpose_choice", ["2"], ["обуч", "учеб"]),
    ("высшее - 1", "education", ["1"], []),
    ("среднее специальное - 2", "education", ["2"], []),
    ("профессионально-техническое - 3", "education", ["3"], []),
    ("общее среднее - 4", "education", ["4"], []),
    ("общее базовое - 5", "education", ["5"], []),
    ("общее начальное - 6", "education", ["6"], []),
    ("не имеет начального - 7", "education", ["7"], []),
    ("состоит в браке - 1", "marital", ["1"], []),
    ("никогда не состоял(а) в браке - 2", "marital", ["2"], []),
    ("вдовец(а) - 3", "marital", ["3"], []),
    ("разведен(а) - 4", "marital", ["4"], []),
    ("да - 5", "spouse_together", ["5"], []),
    ("нет - 6", "spouse_together", ["6"], []),
]


def build_forma24_ul_elements(elems):
    """Собрать условные подчёркивания «нужное подчеркнуть» под текстами-вариантами.
    Линия рисуется только если значение поля совпадает с вариантом (см. _FORMA24_UL_OPTS)."""
    _ensure_fonts()
    from reportlab.pdfbase import pdfmetrics
    pw_mm, ph_mm = FORMA19_MM[0], FORMA19_MM[1]
    ul_off = 1.1 / ph_mm * 100.0
    by_text = {}
    for e in elems:
        if e.get("type") == "text" and e.get("text") and e["text"] not in by_text:
            by_text[e["text"]] = e
    out = []
    for text, field, eq, contains in _FORMA24_UL_OPTS:
        el = by_text.get(text)
        if not el:
            continue
        size = float(el.get("size", 5.5) or 5.5)
        try:
            w_mm = pdfmetrics.stringWidth(text, _font(False), size) / MM
        except Exception:
            w_mm = len(text) * size * 0.5 / MM
        out.append({
            "type": "ul", "field": field, "page": int(el.get("page", 1) or 1),
            "x": round(float(el.get("x", 0)), 3),
            "y": round(float(el.get("y", 0)) + ul_off, 3),
            "w": round(w_mm / pw_mm * 100.0, 3),
            "thickness": 0.6, "color": el.get("color", "#1a1a29"),
            "on": {"eq": eq, "contains": contains},
        })
    return out


def get_forma24_default_template():
    global _FORMA24_TPL_DEFAULT
    if _FORMA24_TPL_DEFAULT is None:
        base = _build_forma_default_template(
            _draw_forma24_front, _draw_forma24_back, iter_keys=())
        uls = build_forma24_ul_elements(base)
        base.extend(uls)
        for i, e in enumerate(base):
            e["id"] = "el%03d" % i
        _FORMA24_TPL_DEFAULT = base
    import copy
    return copy.deepcopy(_FORMA24_TPL_DEFAULT)


def forma_slots(which):
    """Список слотов-полей формы для выпадающего списка редактора."""
    groups = FORMA19_FIELDS if int(which) == 19 else FORMA24_FIELDS
    out = []
    for g in groups:
        for f in g["fields"]:
            out.append({"slot": f["key"], "label": f["label"]})
    if int(which) == 19:
        out.insert(0, {"slot": "id_number", "label": "Идентификационный номер"})
    return out


def _forma_tpl_by_page(tpl):
    by = {1: [], 2: []}
    for el in (tpl or []):
        try:
            p = int(el.get("page", 1) or 1)
        except Exception:
            p = 1
        if p in by:
            by[p].append(el)
    return by


def _draw_forma_template_card(c, tpl_by_page, rec, zw, zh, back):
    """Отрисовать карту формы из шаблона-элементов (в системе координат карты)."""
    vals = _forma_vals(rec)
    page = 2 if back else 1
    for el in tpl_by_page.get(page, []):
        _draw_zayav_element(c, el, vals, zw, zh)


def _draw_grid_element(c, el, vals, pw, ph):
    """Таблица-«клеточки» (Excel-style). cols/rows — размеры в % страницы;
    cells — словарь 'r_c' -> {text|field, align, size, bold}."""
    x0 = float(el.get("x", 0) or 0) / 100.0 * pw
    y0_top = float(el.get("y", 0) or 0) / 100.0 * ph
    cols = [float(w) / 100.0 * pw for w in (el.get("cols") or [])]
    rows = [float(h) / 100.0 * ph for h in (el.get("rows") or [])]
    if not cols or not rows:
        return
    total_w = sum(cols)
    total_h = sum(rows)
    border = _hex_rgb(el.get("color", "#17171f"))
    c.setStrokeColorRGB(*border)
    c.setLineWidth(float(el.get("thickness", 0.5) or 0.5))
    xs = [x0]
    for w in cols:
        xs.append(xs[-1] + w)
    ys_top = [y0_top]
    for h in rows:
        ys_top.append(ys_top[-1] + h)
    top_pdf = ph - y0_top
    bot_pdf = ph - (y0_top + total_h)
    for xx in xs:
        c.line(xx, top_pdf, xx, bot_pdf)
    for yt in ys_top:
        c.line(x0, ph - yt, x0 + total_w, ph - yt)
    cells = el.get("cells") or {}
    dsize = float(el.get("size", 8) or 8)
    for k, cell in cells.items():
        try:
            r, cc = k.split("_")
            r = int(r)
            cc = int(cc)
        except Exception:
            continue
        if r >= len(rows) or cc >= len(cols):
            continue
        cx0 = xs[cc]
        cy0_top = ys_top[r]
        cw = cols[cc]
        ch = rows[r]
        if cell.get("field"):
            txt = vals.get(cell.get("field"), "")
        else:
            txt = cell.get("text", "")
        txt = "" if txt is None else str(txt)
        if txt == "":
            continue
        size = float(cell.get("size", dsize) or dsize)
        bold = bool(cell.get("bold"))
        font = _font(bold) if el.get("font", "sans") == "sans" else _serif(bold)
        c.setFont(font, size)
        c.setFillColorRGB(*_hex_rgb(cell.get("color", "#0a0d52")))
        baseline = ph - (cy0_top + ch / 2.0) - size * 0.35
        c.drawCentredString(cx0 + cw / 2.0, baseline, txt)




# ============================================================================
#  ЗАЯВЛЕНИЕ о регистрации по месту жительства
#  Векторная отрисовка 1:1 по бланку. Раскладка: 2 заявления на листе A4
#  (ландшафт) — левая и правая половины = по A5-портрет. Лицо листа — стр.1
#  двух человек, оборот — стр.2 тех же людей (двусторонняя печать). Разрезав
#  лист по центру, получаем 2 готовых двусторонних заявления A5.
# ============================================================================

ZAYAV_ZONE_MM = (148.5, 210.0)  # одно заявление = A5-портрет

ZAYAVLENIE_FIELDS = [
    {"group": "Заявитель", "fields": [
        {"key": "fio", "label": "ФИО (полностью)"},
        {"key": "birth_year", "label": "Год рождения"},
        {"key": "doc_name", "label": "Документ, удостоверяющий личность"},
        {"key": "passport_series", "label": "Паспорт: серия"},
        {"key": "passport_number", "label": "Паспорт: номер"},
        {"key": "passport_issued_by", "label": "Паспорт: кем выдан"},
        {"key": "passport_issue_date", "label": "Паспорт: дата выдачи (ДД.ММ.ГГГГ)"},
    ]},
    {"group": "Регистрация (пребывание)", "fields": [
        {"key": "reg_who", "label": "Зарегистрировать (одного / с семьёй)"},
        {"key": "reg_count", "label": "Всего человек"},
        {"key": "address_locality", "label": "Адрес пребывания: населённый пункт"},
        {"key": "res_street", "label": "Улица"},
        {"key": "res_house", "label": "Дом"},
        {"key": "res_korpus", "label": "Корпус"},
        {"key": "res_apartment", "label": "Квартира / комната"},
    ]},
    {"group": "Прибытие и основание", "fields": [
        {"key": "stay_term", "label": "Прибыл(а) на (срок пребывания)"},
        {"key": "from_place", "label": "Прибыл(а) из (государство, область, район, нас. пункт)"},
        {"key": "basis", "label": "Основание (договор найма № … от …)"},
    ]},
    {"group": "Дата и площадь", "fields": [
        {"key": "sign_date", "label": "Дата заявления (ДД.ММ.ГГГГ)"},
        {"key": "area", "label": "Общая площадь помещения, кв. м (стр. 2)"},
    ]},
]
ZAYAVLENIE_FIELD_KEYS = [f["key"] for g in ZAYAVLENIE_FIELDS for f in g["fields"]]


def _zayav_helpers(c, x0, y_bottom, zh_pt):
    """Замыкания рисования в координатах зоны (мм от верх-лев угла), шрифт Times."""
    DARK = (0.09, 0.09, 0.14)
    GREY = (0.30, 0.30, 0.36)
    INK = (0.03, 0.05, 0.32)

    def Xmm(mm):
        return x0 + mm * MM

    def Ymm(mm_top):
        return y_bottom + zh_pt - mm_top * MM

    def text(x, y, s, size=6.8, bold=False, color=DARK):
        c.setFillColorRGB(*color)
        c.setFont(_serif(bold), size)
        c.drawString(Xmm(x), Ymm(y), "" if s is None else str(s))

    def center(x, y, s, size=6.8, bold=False, color=DARK):
        c.setFillColorRGB(*color)
        c.setFont(_serif(bold), size)
        c.drawCentredString(Xmm(x), Ymm(y), "" if s is None else str(s))

    def right(x, y, s, size=6.8, bold=False, color=DARK):
        c.setFillColorRGB(*color)
        c.setFont(_serif(bold), size)
        c.drawRightString(Xmm(x), Ymm(y), "" if s is None else str(s))

    def cap(x, y, s, size=3.6):
        c.setFillColorRGB(*GREY)
        c.setFont(_serif(False, italic=True), size)
        c.drawCentredString(Xmm(x), Ymm(y), "" if s is None else str(s))

    def rule(x1, x2, y, w=0.5):
        yy = Ymm(y) - 1.2
        c.setStrokeColorRGB(0.12, 0.12, 0.16)
        c.setLineWidth(w)
        c.line(Xmm(x1), yy, Xmm(x2), yy)

    def val(x, y, s, size=6.2, bold=False):
        if s is None or str(s).strip() == "":
            return
        c.setFillColorRGB(*INK)
        c.setFont(_serif(bold), size)
        c.drawString(Xmm(x), Ymm(y), str(s))

    def cval(x, y, s, size=6.2, bold=False):
        if s is None or str(s).strip() == "":
            return
        c.setFillColorRGB(*INK)
        c.setFont(_serif(bold), size)
        c.drawCentredString(Xmm(x), Ymm(y), str(s))

    return text, center, right, cap, rule, val, cval


def _draw_zayavlenie_page1(c, x0, y_bottom, zw_pt, zh_pt, rec):
    rec = rec or {}
    text, center, right, cap, rule, val, cval = _zayav_helpers(c, x0, y_bottom, zh_pt)

    fio = rec.get("fio", "")
    by = str(rec.get("birth_year", "") or "").strip()
    applicant = fio + (f", {by} г.р." if by else "")
    doc_name = rec.get("doc_name", "")
    ser = rec.get("passport_series", "")
    num = rec.get("passport_number", "")
    issued = rec.get("passport_issued_by", "")
    idate = rec.get("passport_issue_date", "")
    reg_who = rec.get("reg_who", "") or "одного"
    reg_count = rec.get("reg_count", "") or "1"
    locality = rec.get("address_locality", "")
    street = rec.get("res_street", "")
    house = rec.get("res_house", "")
    korp = rec.get("res_korpus", "")
    apt = rec.get("res_apartment", "")
    stay_term = rec.get("stay_term", "")
    from_place = rec.get("from_place", "")
    basis = rec.get("basis", "")
    sd, smon, sy = _split_ru_date(rec.get("sign_date", ""))
    sy2 = sy[-2:] if sy else ""

    XR = 45.0   # левый край правого блока
    RB = 142.0  # правый край
    CXR = (XR + RB) / 2.0

    # --- Получатель: правый блок, ПРАВОЕ выравнивание ---
    ry = 7.0
    for ln in [
        "В орган внутренних дел, сельский (поселковый)",
        "исполнительный комитет (в сельских населённых",
        "пунктах и посёлках городского типа, в которых не",
        "имеется органов внутренних дел)",
    ]:
        right(RB, ry, ln, 6.0)
        ry += 3.2

    # --- ФИО заявителя: 2 линии под блоком, по ширине блока ---
    rule(XR, RB, 24)
    rule(XR, RB, 28.5)
    cval(CXR, 23, applicant, 6.8)
    cap(CXR, 31.6, "(фамилия, собственное имя, отчество (если таковое", 3.7)
    cap(CXR, 34.0, "имеется), год рождения)", 3.7)

    # --- Паспорт (под блоком, линии по ширине) ---
    text(XR, 40, "паспорт или иной документ, удостоверяющий", 6.4)
    text(XR, 44.2, "личность", 6.4)
    rule(60, RB, 44.2)
    val(61, 43.3, doc_name, 5.8)
    text(XR, 49.2, "серия (при наличии)", 6.4)
    rule(74, RB, 49.2)
    cval((74 + RB) / 2, 48.3, ser, 6.4)
    text(XR, 54.2, "№", 6.4)
    rule(51, RB, 54.2)
    val(52, 53.3, num, 6.4)
    text(XR, 59.2, "выдан", 6.4)
    rule(58, RB, 59.2)
    val(59, 58.3, issued, 5.6)
    cap(CXR, 62.4, "(наименование (код) органа, выдавшего документ,", 3.5)
    cap(CXR, 64.8, "удостоверяющий личность)", 3.5)
    rule(XR, RB, 71)
    val(XR + 2, 70, idate, 6.2)
    cap(CXR, 74.2, "(дата выдачи)", 3.7)

    # --- Заголовок ---
    center(74.25, 82, "ЗАЯВЛЕНИЕ", 12, bold=True)
    center(74.25, 87.5, "о регистрации по месту пребывания", 8.4, bold=True)

    # --- Прошу зарегистрировать ---
    text(7, 95, "Прошу зарегистрировать меня", 6.9)
    rule(52, 100, 95)
    val(54, 94, reg_who, 6.2)
    cap(76, 98.3, "(одного, с семьёй)", 3.7)
    text(101, 95, ", всего", 6.9)
    rule(115, 130, 95)
    cval(122.5, 94, reg_count, 6.2)
    text(131, 95, "чел.,", 6.9)

    # --- Адрес пребывания ---
    text(7, 103, "по месту пребывания по адресу:", 6.9)
    rule(58, RB, 103)
    val(59, 102, locality, 6.0)
    text(7, 109, "ул.", 6.9)
    rule(14, 66, 109)
    val(15, 108, street, 5.8)
    text(67, 109, ", дом", 6.9)
    rule(80, 95, 109)
    cval(87.5, 108, house, 6.0)
    text(96, 109, ", корп.", 6.9)
    rule(110, 120, 109)
    cval(115, 108, korp, 6.0)
    text(121, 109, "кв.", 6.9)
    rule(127, RB, 109)
    cval(134.5, 108, apt, 6.0)

    # --- Прибыл(а) на … из … ---
    text(7, 116, "Прибыл(а) на", 6.9)
    rule(31, 72, 116)
    val(32, 115, stay_term, 5.6)
    text(73, 116, "из", 6.9)
    rule(80, RB, 116)
    val(81, 115, from_place, 5.6)
    cap(90, 119.2, "(название государства, наименование области, района, населённого пункта)", 3.3)

    # --- Вместе прибыли (5 линий, для руки) ---
    text(7, 125, "Вместе прибыли:", 6.9)
    ccap = ("(фамилия, собственное имя, отчество (если таковое имеется), "
            "год рождения; подпись совершеннолетнего гражданина)")
    yy = 130.0
    for _ in range(5):
        rule(7, RB, yy)
        cap(74.5, yy + 2.6, ccap, 3.1)
        yy += 6.0

    # --- Основание (всегда «Договор найма № … от …») ---
    text(7, 163, "Жилое помещение предоставлено на основании (находится в собственности)", 6.1)
    rule(7, RB, 168)
    val(9, 167, basis, 6.0)
    cap(74.5, 171, "(документы, являющиеся основанием для регистрации гражданина по месту пребывания)", 3.3)

    # --- Подпись гражданина + дата ---
    text(7, 177, "Подпись гражданина:", 6.9)
    rule(7, 92, 184)
    cap(45, 187.2, "(подпись, фамилия, инициалы)", 3.7)
    text(95, 184, "«", 6.6)
    rule(97, 104, 184)
    cval(100.5, 184, sd, 6.0)
    text(104.5, 184, "»", 6.6)
    rule(107, 126, 184)
    cval(116.5, 184, smon, 5.4)
    text(127, 184, "20", 6.6)
    rule(131, 138, 184)
    cval(134.5, 184, sy2, 6.0)
    text(139, 184, "г.", 6.6)


def _draw_zayavlenie_page2(c, x0, y_bottom, zw_pt, zh_pt, rec):
    rec = rec or {}
    text, center, right, cap, rule, val, cval = _zayav_helpers(c, x0, y_bottom, zh_pt)
    area = rec.get("area", "") or ""
    RB = 142.0

    # --- Подпись собственника / нанимателя ---
    text(7, 12, "Подпись собственника либо нанимателя жилого помещения,", 6.5)
    text(7, 15.8, "предоставившего гражданину жилое помещение:", 6.5)
    rule(7, 82, 27)
    text(90, 26, "«", 6.6)
    rule(93, 101, 26)
    text(102, 26, "»", 6.6)
    rule(104, 124, 26)
    text(125, 26, "20", 6.6)
    rule(130, 138, 26)
    text(139, 26, "г.", 6.6)
    cap(44, 30.2, "(подпись, фамилия, собственное имя,", 3.6)
    cap(44, 32.6, "отчество (если таковое имеется))", 3.6)

    # --- Подписи иных граждан ---
    text(7, 39, "Подписи иных граждан, проживающих совместно с собственником либо", 6.3)
    text(7, 42.8, "нанимателем и (или) имеющих право пользования жилым помещением:", 6.3)
    ccap = "(подпись, фамилия, собственное имя, отчество (если таковое имеется))"
    yy = 54.0
    for _ in range(3):
        rule(7, 92, yy)
        text(97, yy, "(", 6.6)
        rule(101, 132, yy)
        text(133, yy, ")", 6.6)
        cap(49.5, yy + 3.0, ccap, 3.5)
        cap(116, yy + 3.0, "(год рождения)", 3.6)
        yy += 11.0

    # --- Общая площадь (единственное автозаполнение стр. 2) ---
    text(7, 90, "Общая площадь жилого помещения составляет", 6.4)
    rule(63, 84, 90)
    cval(73.5, 89, area, 6.4, bold=True)
    text(85, 90, "кв. метров, в нём", 6.4)
    text(7, 94.5, "проживает", 6.4)
    rule(25, 40, 94.5)
    text(41, 94.5, "чел., в том числе несовершеннолетних", 6.4)
    rule(112, 132, 94.5)
    text(133, 94.5, "чел.*", 6.4)

    # --- Лицо, ответственное за регистрацию ---
    text(7, 102, "Лицо, ответственное за регистрацию (при его отсутствии – должностное", 6.3)
    text(7, 105.8, "лицо органа регистрации):", 6.3)
    rule(7, 52, 118)
    cap(29.5, 121.2, "(должность)", 3.8)
    rule(58, 96, 118)
    cap(77, 121.2, "(подпись)", 3.8)
    rule(102, RB, 118)
    cap(122, 121.2, "(фамилия, инициалы)", 3.8)
    text(72, 123.2, "М.П.", 6.4)

    # --- Дата ---
    text(7, 132, "«", 6.6)
    rule(10, 22, 132)
    text(23, 132, "»", 6.6)
    rule(25, 66, 132)
    text(67, 132, "20", 6.6)
    rule(73, 83, 132)
    text(84, 132, "г.", 6.6)

    # --- Сноска ---
    rule(7, 44, 143)
    text(7, 148, "* Заполняется лицом, ответственным за регистрацию (при его", 5.4)
    text(7, 151.5, "отсутствии – должностным лицом органа регистрации).", 5.4)




# =====================================================================
#  НОВАЯ АРХИТЕКТУРА ЗАЯВЛЕНИЯ (по требованию пользователя):
#  фон = чистый бланк-изображение «по месту пребывания» (A4-портрет),
#  данные накладываются поверх по КООРДИНАТАМ (% страницы) из конфигурации.
#  Preview (фронт) и PDF (бэк) используют ОДНУ систему координат.
#  Пустой бланк рисуется теми же статическими элементами, что и раньше,
#  но масштабируется с зоны A5 (148.5×210) на полный A4 (210×297) —
#  пропорции A5 и A4 идентичны (1:√2), поэтому % координаты не меняются.
# =====================================================================

_SQRT2 = 1.41421356237

def _zayav_static_page1(H):
    """Только статические элементы стр.1 (без данных) — «пустой бланк»."""
    text, center, right, cap, rule = H
    XR = 45.0
    RB = 142.0
    CXR = (XR + RB) / 2.0
    ry = 7.0
    for ln in [
        "В орган внутренних дел, сельский (поселковый)",
        "исполнительный комитет (в сельских населённых",
        "пунктах и посёлках городского типа, в которых не",
        "имеется органов внутренних дел)",
    ]:
        right(RB, ry, ln, 6.0)
        ry += 3.2
    rule(XR, RB, 24)
    rule(XR, RB, 28.5)
    cap(CXR, 31.6, "(фамилия, собственное имя, отчество (если таковое", 3.7)
    cap(CXR, 34.0, "имеется), год рождения)", 3.7)
    text(XR, 40, "паспорт или иной документ, удостоверяющий", 6.4)
    text(XR, 44.2, "личность", 6.4)
    rule(60, RB, 44.2)
    text(XR, 49.2, "серия (при наличии)", 6.4)
    rule(74, RB, 49.2)
    text(XR, 54.2, "№", 6.4)
    rule(51, RB, 54.2)
    text(XR, 59.2, "выдан", 6.4)
    rule(58, RB, 59.2)
    cap(CXR, 62.4, "(наименование (код) органа, выдавшего документ,", 3.5)
    cap(CXR, 64.8, "удостоверяющий личность)", 3.5)
    rule(XR, RB, 71)
    cap(CXR, 74.2, "(дата выдачи)", 3.7)
    center(74.25, 82, "ЗАЯВЛЕНИЕ", 12, bold=True)
    center(74.25, 87.5, "о регистрации по месту пребывания", 8.4, bold=True)
    text(7, 95, "Прошу зарегистрировать меня", 6.9)
    rule(52, 100, 95)
    cap(76, 98.3, "(одного, с семьёй)", 3.7)
    text(101, 95, ", всего", 6.9)
    rule(115, 130, 95)
    text(131, 95, "чел.,", 6.9)
    text(7, 103, "по месту пребывания по адресу:", 6.9)
    rule(58, RB, 103)
    text(7, 109, "ул.", 6.9)
    rule(14, 66, 109)
    text(67, 109, ", дом", 6.9)
    rule(80, 95, 109)
    text(96, 109, ", корп.", 6.9)
    rule(110, 120, 109)
    text(121, 109, "кв.", 6.9)
    rule(127, RB, 109)
    text(7, 116, "Прибыл(а) на", 6.9)
    rule(31, 72, 116)
    text(73, 116, "из", 6.9)
    rule(80, RB, 116)
    cap(90, 119.2, "(название государства, наименование области, района, населённого пункта)", 3.3)
    text(7, 125, "Вместе прибыли:", 6.9)
    ccap = ("(фамилия, собственное имя, отчество (если таковое имеется), "
            "год рождения; подпись совершеннолетнего гражданина)")
    yy = 130.0
    for _ in range(5):
        rule(7, RB, yy)
        cap(74.5, yy + 2.6, ccap, 3.1)
        yy += 6.0
    text(7, 163, "Жилое помещение предоставлено на основании (находится в собственности)", 6.1)
    rule(7, RB, 168)
    cap(74.5, 171, "(документы, являющиеся основанием для регистрации гражданина по месту пребывания)", 3.3)
    text(7, 177, "Подпись гражданина:", 6.9)
    rule(7, 92, 184)
    cap(45, 187.2, "(подпись, фамилия, инициалы)", 3.7)
    text(95, 184, "«", 6.6)
    rule(97, 104, 184)
    text(104.5, 184, "»", 6.6)
    rule(107, 126, 184)
    text(127, 184, "20", 6.6)
    rule(131, 138, 184)
    text(139, 184, "г.", 6.6)


def _zayav_static_page2(H):
    """Только статические элементы стр.2 (без данных)."""
    text, center, right, cap, rule = H
    RB = 142.0
    text(7, 12, "Подпись собственника либо нанимателя жилого помещения,", 6.5)
    text(7, 15.8, "предоставившего гражданину жилое помещение:", 6.5)
    rule(7, 82, 27)
    text(90, 26, "«", 6.6)
    rule(93, 101, 26)
    text(102, 26, "»", 6.6)
    rule(104, 124, 26)
    text(125, 26, "20", 6.6)
    rule(130, 138, 26)
    text(139, 26, "г.", 6.6)
    cap(44, 30.2, "(подпись, фамилия, собственное имя,", 3.6)
    cap(44, 32.6, "отчество (если таковое имеется))", 3.6)
    text(7, 39, "Подписи иных граждан, проживающих совместно с собственником либо", 6.3)
    text(7, 42.8, "нанимателем и (или) имеющих право пользования жилым помещением:", 6.3)
    ccap = "(подпись, фамилия, собственное имя, отчество (если таковое имеется))"
    yy = 54.0
    for _ in range(3):
        rule(7, 92, yy)
        text(97, yy, "(", 6.6)
        rule(101, 132, yy)
        text(133, yy, ")", 6.6)
        cap(49.5, yy + 3.0, ccap, 3.5)
        cap(116, yy + 3.0, "(год рождения)", 3.6)
        yy += 11.0
    text(7, 90, "Общая площадь жилого помещения составляет", 6.4)
    rule(63, 84, 90)
    text(85, 90, "кв. метров, в нём", 6.4)
    text(7, 94.5, "проживает", 6.4)
    rule(25, 40, 94.5)
    text(41, 94.5, "чел., в том числе несовершеннолетних", 6.4)
    rule(112, 132, 94.5)
    text(133, 94.5, "чел.*", 6.4)
    text(7, 102, "Лицо, ответственное за регистрацию (при его отсутствии – должностное", 6.3)
    text(7, 105.8, "лицо органа регистрации):", 6.3)
    rule(7, 52, 118)
    cap(29.5, 121.2, "(должность)", 3.8)
    rule(58, 96, 118)
    cap(77, 121.2, "(подпись)", 3.8)
    rule(102, RB, 118)
    cap(122, 121.2, "(фамилия, инициалы)", 3.8)
    text(72, 123.2, "М.П.", 6.4)
    text(7, 132, "«", 6.6)
    rule(10, 22, 132)
    text(23, 132, "»", 6.6)
    rule(25, 66, 132)
    text(67, 132, "20", 6.6)
    rule(73, 83, 132)
    text(84, 132, "г.", 6.6)
    rule(7, 44, 143)
    text(7, 148, "* Заполняется лицом, ответственным за регистрацию (при его", 5.4)
    text(7, 151.5, "отсутствии – должностным лицом органа регистрации).", 5.4)


# ---- Слоты-наложения (данные) и их метки для редактора координат ----
ZAYAV_OVERLAY_SLOTS = [
    {"slot": "applicant", "page": 1, "label": "ФИО заявителя + год рождения"},
    {"slot": "doc_name", "page": 1, "label": "Документ, удостоверяющий личность"},
    {"slot": "passport_series", "page": 1, "label": "Серия"},
    {"slot": "passport_number", "page": 1, "label": "№ (номер)"},
    {"slot": "passport_issued_by", "page": 1, "label": "Кем выдан"},
    {"slot": "passport_issue_date", "page": 1, "label": "Дата выдачи"},
    {"slot": "reg_who", "page": 1, "label": "Зарегистрировать (одного / с семьёй)"},
    {"slot": "reg_count", "page": 1, "label": "Всего человек"},
    {"slot": "address_locality", "page": 1, "label": "Адрес (населённый пункт)"},
    {"slot": "res_street", "page": 1, "label": "Улица"},
    {"slot": "res_house", "page": 1, "label": "Дом"},
    {"slot": "res_korpus", "page": 1, "label": "Корпус"},
    {"slot": "res_apartment", "page": 1, "label": "Квартира"},
    {"slot": "stay_term", "page": 1, "label": "Прибыл(а) на (срок)"},
    {"slot": "from_place", "page": 1, "label": "Прибыл(а) из"},
    {"slot": "basis", "page": 1, "label": "Основание (договор найма …)"},
    {"slot": "sign_day", "page": 1, "label": "Дата подписи: день"},
    {"slot": "sign_month", "page": 1, "label": "Дата подписи: месяц"},
    {"slot": "sign_year", "page": 1, "label": "Дата подписи: год (2 цифры)"},
    {"slot": "area", "page": 2, "label": "Общая площадь, кв. м"},
    {"slot": "occupancy_count", "page": 2, "label": "Проживает, чел."},
    {"slot": "minors_count", "page": 2, "label": "Несовершеннолетних, чел."},
]

# raw: (slot, page, x_mm, y_mm, w_mm, align, size_a5_pt, bold)
_ZAYAV_LAYOUT_RAW = [
    ("applicant", 1, 45, 23, 97, "center", 6.8, False),
    ("doc_name", 1, 61, 43.3, 81, "left", 5.8, False),
    ("passport_series", 1, 74, 48.3, 68, "center", 6.4, False),
    ("passport_number", 1, 52, 53.3, 90, "left", 6.4, False),
    ("passport_issued_by", 1, 59, 58.3, 83, "left", 5.6, False),
    ("passport_issue_date", 1, 47, 70.0, 95, "left", 6.2, False),
    ("reg_who", 1, 54, 94.0, 46, "left", 6.2, False),
    ("reg_count", 1, 115, 94.0, 15, "center", 6.2, False),
    ("address_locality", 1, 59, 102.0, 83, "left", 6.0, False),
    ("res_street", 1, 15, 108.0, 51, "left", 5.8, False),
    ("res_house", 1, 80, 108.0, 15, "center", 6.0, False),
    ("res_korpus", 1, 110, 108.0, 10, "center", 6.0, False),
    ("res_apartment", 1, 127, 108.0, 15, "center", 6.0, False),
    ("stay_term", 1, 32, 115.0, 40, "left", 5.6, False),
    ("from_place", 1, 81, 115.0, 61, "left", 5.6, False),
    ("basis", 1, 9, 167.0, 133, "left", 6.0, False),
    ("sign_day", 1, 97, 184.0, 7, "center", 6.0, False),
    ("sign_month", 1, 107, 184.0, 19, "center", 5.4, False),
    ("sign_year", 1, 131, 184.0, 7, "center", 6.0, False),
    ("area", 2, 63, 89.0, 21, "center", 6.4, True),
    ("occupancy_count", 2, 25, 94.5, 15, "center", 6.4, False),
    ("minors_count", 2, 112, 94.5, 20, "center", 6.4, False),
]


def _mk_zayav_layout():
    zw, zh = ZAYAV_ZONE_MM  # 148.5, 210
    out = {"1": {}, "2": {}}
    for slot, page, x, y, w, align, sz, bold in _ZAYAV_LAYOUT_RAW:
        out[str(page)][slot] = {
            "x": round(x / zw * 100, 2),
            "y": round(y / zh * 100, 2),
            "w": round(w / zw * 100, 2),
            "align": align,
            "size": round(sz * _SQRT2, 2),  # pt на A4
            "bold": bool(bold),
        }
    return out


ZAYAV_LAYOUT_DEFAULT = _mk_zayav_layout()


def _merge_zayav_layout(overrides):
    import copy
    base = copy.deepcopy(ZAYAV_LAYOUT_DEFAULT)
    if isinstance(overrides, dict):
        for pg, slots in overrides.items():
            pg = str(pg)
            if pg not in base:
                base[pg] = {}
            if isinstance(slots, dict):
                for k, cfg in slots.items():
                    if isinstance(cfg, dict) and k in base[pg]:
                        base[pg][k].update(cfg)
                    else:
                        base[pg][k] = cfg
    return base


def zayav_overlay_text(rec):
    """Отображаемые значения слотов-наложения из записи (та же логика в JS фронта)."""
    rec = rec or {}

    def g(k):
        v = rec.get(k, "")
        return "" if v is None else str(v)

    fio = g("fio").strip()
    by = g("birth_year").strip()
    applicant = fio + ((", %s г.р." % by) if by else "")
    sd, smon, sy = _split_ru_date(rec.get("sign_date", ""))
    sy2 = sy[-2:] if sy else ""
    out = {
        "applicant": applicant,
        "doc_name": g("doc_name"),
        "passport_series": g("passport_series"),
        "passport_number": g("passport_number"),
        "passport_issued_by": g("passport_issued_by"),
        "passport_issue_date": g("passport_issue_date"),
        "reg_who": g("reg_who") or "одного",
        "reg_count": g("reg_count") or "1",
        "address_locality": g("address_locality"),
        "res_street": g("res_street"),
        "res_house": g("res_house"),
        "res_korpus": g("res_korpus"),
        "res_apartment": g("res_apartment"),
        "stay_term": g("stay_term"),
        "from_place": g("from_place"),
        "basis": g("basis"),
        "sign_day": sd,
        "sign_month": smon,
        "sign_year": sy2,
        "area": g("area"),
        "occupancy_count": g("occupancy_count"),
        "minors_count": g("minors_count"),
    }
    # свои столбцы (cc_*) — прокидываем как есть, чтобы поставленные в редакторе поля печатались
    for k, v in rec.items():
        if isinstance(k, str) and k.startswith("cc_") and str(v).strip():
            out[k] = str(v)
    return out


_SQRT2 = 1.41421356237
_ZW_MM, _ZH_MM = ZAYAV_ZONE_MM  # 148.5, 210
_HEX_DARK = "#17171f"
_HEX_GREY = "#4d4d5c"
_HEX_INK = "#0a0d52"


def _hex_rgb(h):
    h = (h or "#000000").lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    try:
        return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)
    except Exception:
        return (0.0, 0.0, 0.0)


def _cap_helpers(elems, page):
    """Хелперы-«рекордеры»: вместо рисования складывают элементы шаблона.
    Координаты мм (зона A5) -> проценты страницы; кегль A5 pt -> A4 pt."""
    def _push_text(x, y, s, size, align, bold=False, italic=False, color=_HEX_DARK):
        if s is None or str(s) == "":
            return
        elems.append({
            "type": "text", "page": page,
            "x": round(x / _ZW_MM * 100, 3), "y": round(y / _ZH_MM * 100, 3),
            "align": align, "text": str(s),
            "size": round(size * _SQRT2, 2),
            "bold": bool(bold), "italic": bool(italic), "color": color,
        })

    def text(x, y, s, size=6.8, bold=False, color=None):
        _push_text(x, y, s, size, "left", bold, False, _HEX_DARK)

    def center(x, y, s, size=6.8, bold=False, color=None):
        _push_text(x, y, s, size, "center", bold, False, _HEX_DARK)

    def right(x, y, s, size=6.8, bold=False, color=None):
        _push_text(x, y, s, size, "right", bold, False, _HEX_DARK)

    def cap(x, y, s, size=3.6):
        _push_text(x, y, s, size, "center", False, True, _HEX_GREY)

    def rule(x1, x2, y, w=0.5):
        elems.append({
            "type": "line", "page": page,
            "x": round(x1 / _ZW_MM * 100, 3), "y": round(y / _ZH_MM * 100, 3),
            "w": round((x2 - x1) / _ZW_MM * 100, 3),
            "thickness": round(float(w), 2), "color": _HEX_DARK,
        })

    return (text, center, right, cap, rule)


_ZAYAV_TEMPLATE_DEFAULT = None


def _build_zayav_default_template():
    elems = []
    _zayav_static_page1(_cap_helpers(elems, 1))
    _zayav_static_page2(_cap_helpers(elems, 2))
    # поля-данные из ZAYAV_LAYOUT_DEFAULT (переводим бокс -> якорь)
    for pg, slots in ZAYAV_LAYOUT_DEFAULT.items():
        for slot, cfg in slots.items():
            al = cfg.get("align", "left")
            if al == "center":
                ax = cfg["x"] + cfg["w"] / 2.0
            elif al == "right":
                ax = cfg["x"] + cfg["w"]
            else:
                ax = cfg["x"]
            elems.append({
                "type": "field", "page": int(pg), "field": slot,
                "x": round(ax, 3), "y": cfg["y"], "align": al,
                "size": cfg["size"], "bold": bool(cfg.get("bold")), "italic": False,
                "w": cfg["w"], "color": _HEX_INK,
            })
    for i, e in enumerate(elems):
        e["id"] = "el%03d" % i
    return elems


def get_zayav_default_template():
    global _ZAYAV_TEMPLATE_DEFAULT
    if _ZAYAV_TEMPLATE_DEFAULT is None:
        _ZAYAV_TEMPLATE_DEFAULT = _build_zayav_default_template()
    import copy
    return copy.deepcopy(_ZAYAV_TEMPLATE_DEFAULT)


def _resolve_zayav_template(template):
    if isinstance(template, list) and template:
        return template
    return get_zayav_default_template()


_ZAYAV_BG_CACHE = {}


def render_zayav_background_png(page=1, scale=2.1):
    """PNG чистого бланка (без данных) — совместимость со старым эндпоинтом."""
    page = 2 if int(page) == 2 else 1
    key = (page, round(float(scale), 2))
    if key in _ZAYAV_BG_CACHE:
        return _ZAYAV_BG_CACHE[key]
    pdf = build_zayavlenie([{}])  # пустая запись -> только бланк
    png = render_pdf_page_png(pdf, page - 1, scale=scale)
    _ZAYAV_BG_CACHE[key] = png
    return png


def _draw_zayav_element(c, el, vals, pw, ph):
    """Рисует ОДИН элемент шаблона заявления в текущей системе координат холста c.
    pw/ph — размеры «страницы шаблона» в пунктах (A4-портрет). Используется и в
    обычном режиме (1 на лист), и в режиме «2 на лист» (внутри translate/scale)."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    t = el.get("type", "text")
    col = _hex_rgb(el.get("color", "#000000"))
    if t == "rect":
        # прямоугольник-заливка: x,y — верх-левый угол (%), w,h — размеры (%)
        x = float(el.get("x", 0) or 0) / 100.0 * pw
        w = float(el.get("w", 0) or 0) / 100.0 * pw
        h = float(el.get("h", 0) or 0) / 100.0 * ph
        y_top = float(el.get("y", 0) or 0) / 100.0 * ph
        yb = ph - y_top - h
        fill = el.get("fill", el.get("color", "#e6e6e8"))
        if fill:
            c.setFillColorRGB(*_hex_rgb(fill))
        stroke = el.get("stroke")
        if stroke:
            c.setStrokeColorRGB(*_hex_rgb(stroke))
        c.setLineWidth(float(el.get("thickness", 0.4) or 0.4))
        c.rect(x, yb, w, h, fill=1 if fill else 0, stroke=1 if stroke else 0)
        return
    if t == "grid":
        _draw_grid_element(c, el, vals, pw, ph)
        return
    if t == "line":
        x = float(el.get("x", 0) or 0) / 100.0 * pw
        y = float(el.get("y", 0) or 0) / 100.0 * ph
        c.setStrokeColorRGB(*col)
        c.setLineWidth(float(el.get("thickness", 0.5) or 0.5))
        if el.get("x2") is not None or el.get("y2") is not None:
            x2 = float(el.get("x2", el.get("x", 0)) or 0) / 100.0 * pw
            y2 = float(el.get("y2", el.get("y", 0)) or 0) / 100.0 * ph
            c.line(x, ph - y, x2, ph - y2)
        else:
            w = float(el.get("w", 0) or 0) / 100.0 * pw
            c.line(x, ph - y, x + w, ph - y)
        return
    if t == "ul":
        # условное подчёркивание «нужное подчеркнуть»: линия рисуется,
        # только если значение поля совпадает с одним из вариантов (on.eq / on.contains)
        v = vals.get(el.get("field"), "")
        v = "" if v is None else str(v).strip().lower()
        if v == "":
            return
        on = el.get("on", {}) or {}
        eq = [str(s).strip().lower() for s in on.get("eq", [])]
        contains = [str(s).strip().lower() for s in on.get("contains", [])]
        hit = (v in eq) or any(sub and sub in v for sub in contains)
        if not hit:
            return
        x = float(el.get("x", 0) or 0) / 100.0 * pw
        y = float(el.get("y", 0) or 0) / 100.0 * ph
        w = float(el.get("w", 0) or 0) / 100.0 * pw
        c.setStrokeColorRGB(*col)
        c.setLineWidth(float(el.get("thickness", 0.6) or 0.6))
        c.line(x, ph - y, x + w, ph - y)
        return
    if t == "spread":
        # раскладка каждого символа значения по отдельной клетке:
        # x — левый край первой клетки (%), cw — ширина клетки (%), n — число клеток
        txt = vals.get(el.get("field"), "") if el.get("field") else el.get("text", "")
        txt = "" if txt is None else str(txt)
        if txt.strip() == "":
            return
        x0 = float(el.get("x", 0) or 0) / 100.0 * pw
        cw = float(el.get("cw", 0) or 0) / 100.0 * pw
        n = int(el.get("n", len(txt)) or len(txt))
        yb = ph - float(el.get("y", 0) or 0) / 100.0 * ph
        size = float(el.get("size", 7.5) or 7.5)
        if el.get("font") == "serif":
            font = _serif(bool(el.get("bold")), bool(el.get("italic")))
        else:
            font = _font(bool(el.get("bold")))
        c.setFont(font, size)
        c.setFillColorRGB(*_hex_rgb(el.get("color", "#0a0d52")))
        for i, ch in enumerate(txt[:n]):
            c.drawCentredString(x0 + (i + 0.5) * cw, yb, ch)
        return
    if t == "field":
        txt = vals.get(el.get("field"), "")
    else:
        txt = el.get("text", "")
    if txt is None or str(txt).strip() == "":
        return
    txt = str(txt)
    if el.get("font") == "sans":
        font = _font(bool(el.get("bold")))
    else:
        font = _serif(bool(el.get("bold")), bool(el.get("italic")))
    size = float(el.get("size", 9) or 9)
    w = float(el.get("w", 0) or 0) / 100.0 * pw
    if w > 0:
        tw = stringWidth(txt, font, size)
        if tw > w:
            size = max(4.0, size * w / tw)
    c.setFont(font, size)
    c.setFillColorRGB(*col)
    x = float(el.get("x", 0) or 0) / 100.0 * pw
    yb = ph - float(el.get("y", 0) or 0) / 100.0 * ph
    align = el.get("align", "left")
    if align == "center":
        c.drawCentredString(x, yb, txt)
    elif align == "right":
        c.drawRightString(x, yb, txt)
    else:
        c.drawString(x, yb, txt)
    if el.get("underline"):
        tw = stringWidth(txt, font, size)
        if align == "center":
            ux = x - tw / 2.0
        elif align == "right":
            ux = x - tw
        else:
            ux = x
        uy = yb - size * 0.13
        c.setStrokeColorRGB(*col)
        c.setLineWidth(max(0.4, size * 0.05))
        c.line(ux, uy, ux + tw, uy)


def _zayav_pages_by_page(tpl):
    by_page = {1: [], 2: []}
    for el in tpl:
        try:
            p = int(el.get("page", 1) or 1)
        except Exception:
            p = 1
        if p in by_page:
            by_page[p].append(el)
    return by_page


def _build_zayavlenie_2up(people, tpl, duplex_flip="long"):
    """2 заявления на ОДНОМ листе A4-АЛЬБОМ (297×210 мм): каждое уменьшено до A5-портрет
    (148.5×210 мм) и стоит рядом (левое/правое), вдвоём полностью занимая лист.
    Двусторонняя печать: лицо листа = стр.1 обоих людей, оборот = стр.2 обоих.
    Компенсация переворота принтера: duplex_flip='long' (по ДЛИННОМУ краю) — оборот
    поворачивается на 180°; 'short' (по КОРОТКОМУ краю) — половины меняются местами.
    Разрезав лист по центру, получаем 2 готовых двусторонних заявления.
    Шаблон ОБЩИЙ — правка применяется к обоим."""
    from reportlab.pdfgen import canvas
    _ensure_fonts()
    src_w, src_h = 210 * MM, 297 * MM      # система координат шаблона (A4-портрет)
    sw, sh = 297 * MM, 210 * MM            # физический лист A4-альбом
    half_w = sw / 2.0                      # 148.5 мм
    scale = half_w / src_w                 # ≈0.7071; при этом src_h*scale == sh (точно)
    by_page = _zayav_pages_by_page(_resolve_zayav_template(tpl))
    people = list(people or []) or [{}]
    pairs = [people[i:i + 2] for i in range(0, len(people), 2)]

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(sw, sh))
    flip = str(duplex_flip or "long").lower()
    for pair in pairs:
        left_rec = pair[0] if len(pair) >= 1 else None
        right_rec = pair[1] if len(pair) >= 2 else None
        for page in (1, 2):
            is_back = (page == 2)
            # Компенсация переворота принтера при двусторонней печати АЛЬБОМНОГО листа:
            #  - 'long' (переворот по ДЛИННОМУ краю): оборот выходит повёрнутым на 180° →
            #    поворачиваем всю оборотную страницу на 180°, чтобы скомпенсировать.
            #  - 'short' (по КОРОТКОМУ краю): оборот зеркалится лево/право →
            #    меняем половины местами (без поворота).
            rotate_back = is_back and flip == "long"
            slots = [(0.0, left_rec), (half_w, right_rec)]
            if is_back and flip == "short":
                slots = [(0.0, right_rec), (half_w, left_rec)]
            c.saveState()
            if rotate_back:
                c.translate(sw, sh)
                c.rotate(180)
            for x_off, rec in slots:
                if rec is None:
                    continue
                vals = zayav_overlay_text(rec)
                c.saveState()
                c.translate(x_off, 0)
                c.scale(scale, scale)
                for el in by_page[page]:
                    _draw_zayav_element(c, el, vals, src_w, src_h)
                c.restoreState()
            c.restoreState()
            # пунктирная линия реза по центру листа (в координатах листа)
            c.saveState()
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            c.setLineWidth(0.4)
            c.setDash(3, 3)
            c.line(half_w, 4 * MM, half_w, sh - 4 * MM)
            c.restoreState()
            c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()


def build_zayavlenie(people, template=None, layout=None, duplex_flip="long", draw_guides=False, two_up=False):
    """PDF «Заявлений» из РЕДАКТИРУЕМОГО ШАБЛОНА (список элементов).
    two_up=False: A4-портрет, по 2 страницы на человека (1 заявление = 1 лист).
    two_up=True: 2 заявления рядом на A4-альбом (см. _build_zayavlenie_2up).
    Элементы: text | line | field. field.field -> значение из zayav_overlay_text(rec)."""
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase.pdfmetrics import stringWidth

    _ensure_fonts()
    pw, ph = 210 * MM, 297 * MM
    tpl = _resolve_zayav_template(template)
    if two_up:
        return _build_zayavlenie_2up(people, tpl, duplex_flip=duplex_flip)
    people = list(people or []) or [{}]
    by_page = _zayav_pages_by_page(tpl)

    def draw_element(el, vals):
        t = el.get("type", "text")
        col = _hex_rgb(el.get("color", "#000000"))
        if t == "line":
            x = float(el.get("x", 0) or 0) / 100.0 * pw
            y = float(el.get("y", 0) or 0) / 100.0 * ph
            w = float(el.get("w", 0) or 0) / 100.0 * pw
            c.setStrokeColorRGB(*col)
            c.setLineWidth(float(el.get("thickness", 0.5) or 0.5))
            c.line(x, ph - y, x + w, ph - y)
            return
        if t == "field":
            txt = vals.get(el.get("field"), "")
        else:
            txt = el.get("text", "")
        if txt is None or str(txt).strip() == "":
            return
        txt = str(txt)
        if el.get("font") == "sans":
            font = _font(bool(el.get("bold")))
        else:
            font = _serif(bool(el.get("bold")), bool(el.get("italic")))
        size = float(el.get("size", 9) or 9)
        w = float(el.get("w", 0) or 0) / 100.0 * pw
        if w > 0:
            tw = stringWidth(txt, font, size)
            if tw > w:
                size = max(4.0, size * w / tw)
        c.setFont(font, size)
        c.setFillColorRGB(*col)
        x = float(el.get("x", 0) or 0) / 100.0 * pw
        yb = ph - float(el.get("y", 0) or 0) / 100.0 * ph
        align = el.get("align", "left")
        if align == "center":
            c.drawCentredString(x, yb, txt)
        elif align == "right":
            c.drawRightString(x, yb, txt)
        else:
            c.drawString(x, yb, txt)
        if el.get("underline"):
            tw = stringWidth(txt, font, size)
            if align == "center":
                ux = x - tw / 2.0
            elif align == "right":
                ux = x - tw
            else:
                ux = x
            uy = yb - size * 0.13
            c.setStrokeColorRGB(*col)
            c.setLineWidth(max(0.4, size * 0.05))
            c.line(ux, uy, ux + tw, uy)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(pw, ph))
    for rec in people:
        vals = zayav_overlay_text(rec)
        for page in (1, 2):
            for el in by_page[page]:
                draw_element(el, vals)
            c.showPage()
    c.save()
    buf.seek(0)
    return buf.getvalue()
