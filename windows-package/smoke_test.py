"""CI smoke-test — быстрая проверка генерации документов ДО сборки .exe.

Запускается в GitHub Actions на ubuntu (см. windows-installer.yml, job "smoke").
Если что-то в document_service сломано (PDF-бланк, повороты, мульти-A4,
диагностика) — job падает и битый установщик НЕ публикуется.

Не требует MongoDB. Использует только document_service.
"""
import os
import sys

# document_service лежит в backend/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import document_service as d  # noqa: E402

MM = 72.0 / 25.4
FAILS = []


def check(name, cond, detail=""):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not cond:
        FAILS.append(name)


def page_size(pdf_bytes, idx=0):
    import pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    r = doc[idx].rect
    n = doc.page_count
    doc.close()
    return round(r.width, 1), round(r.height, 1), n


REC = [{"fio": "Иванов Иван Иванович,", "address": "г. Мозырь, ул. Советская, 7",
        "from_day": "01", "from_month": "марта", "from_year": "25",
        "to_day": "01", "to_month": "марта", "to_year": "26"}]


def approx(a, b, tol=1.5):
    return abs(a - b) <= tol


# 1. Базовый бланк 147x103 (card, без поворота)
w, h, n = page_size(d.build_overlay(REC, page_size="card", with_form=True))
check("overlay card 147x103", approx(w, 147 * MM) and approx(h, 103 * MM), f"{w}x{h}")

# 2. Поворот 90 -> портрет 103x147
w, h, n = page_size(d.build_overlay(REC, page_size="card", rotate=90))
check("overlay rotate=90 -> 103x147", approx(w, 103 * MM) and approx(h, 147 * MM), f"{w}x{h}")

# 3. Полная печать landscape: 4/лист, 3 записи -> 1 лист A4 landscape
w, h, n = page_size(d.build_full_sheets(REC * 3, orientation="landscape"))
check("full landscape A4 + pages", approx(w, 297 * MM) and approx(h, 210 * MM) and n == 1, f"{w}x{h} pages={n}")

# 4. Полная печать portrait: 2/лист, 3 записи -> 2 листа
w, h, n = page_size(d.build_full_sheets(REC * 3, orientation="portrait"))
check("full portrait A4 + pages", approx(w, 210 * MM) and approx(h, 297 * MM) and n == 2, f"{w}x{h} pages={n}")

# 5. Пробный лист с поворотом
pdf = d.build_overlay_test_sheet(rotate=90)
check("test-sheet rotate=90 -> pdf", pdf[:4] == b"%PDF")

# 6. Рендер первой страницы в PNG (превью)
png = d.render_pdf_first_page_png(d.build_full_sheets(REC * 2, orientation="landscape"))
check("preview png", png[:4] == b"\x89PNG" and len(png) > 1000, f"{len(png)} bytes")

# 7. Самодиагностика (без принтеров/soffice на CI это допустимо, проверяем что не падает)
checks = d.run_diagnostics()
keys = {c["key"] for c in checks}
check("diagnostics runs", {"fonts", "assets", "template", "pdf"}.issubset(keys), f"keys={sorted(keys)}")
pdf_check = next((c for c in checks if c["key"] == "pdf"), None)
check("diagnostics pdf ok", bool(pdf_check and pdf_check["ok"]))

if FAILS:
    print("\nSMOKE TEST FAILED:", ", ".join(FAILS))
    sys.exit(1)
print("\nSMOKE TEST PASSED")
