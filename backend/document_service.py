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
    import pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
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
