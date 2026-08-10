"""Turn the real college contract .docx into a docxtpl template by replacing ONLY the
variable student values with {{ jinja }} placeholders. All formatting/text is preserved.

Source:  templates/real_source.docx  (the exact .docx provided by the college)
Output:  templates/contract_template.docx
"""
from pathlib import Path
from docx import Document

TEMPLATE_DIR = Path(__file__).parent / "templates"
SRC = TEMPLATE_DIR / "real_source.docx"
OUT = TEMPLATE_DIR / "contract_template.docx"


def iter_paragraphs(doc):
    def walk_container(container):
        for p in container.paragraphs:
            yield p
        for t in container.tables:
            for row in t.rows:
                for cell in row.cells:
                    yield from walk_container(cell)
    yield from walk_container(doc)


def replace_first_in_paragraph(p, search, replace):
    """Replace the first occurrence of `search` in a paragraph, preserving run formatting."""
    full = "".join(r.text for r in p.runs)
    if search not in full:
        return False
    start = full.index(search)
    end = start + len(search)
    acc = 0
    for r in p.runs:
        r_start = acc
        r_end = acc + len(r.text)
        acc = r_end
        if r_end <= start or r_start >= end:
            continue
        seg_start = max(start, r_start) - r_start
        seg_end = min(end, r_end) - r_start
        insert = replace if (r_start <= start < r_end) else ""
        r.text = r.text[:seg_start] + insert + r.text[seg_end:]
    return True


# (search, replacement) — ORDER MATTERS (specific/longer strings first).
REPLACEMENTS = [
    # passport issuer (contains "Туркменистана") must go before citizenship
    ("Государственной Миграционной Службой Туркменистана", "{{ passport_issued_by }}"),
    ("А3058202", "{{ passport_number }}"),
    ("08.01.2025", "{{ passport_issue_date }}"),
    ("07.01.2030", "{{ passport_valid_until }}"),
    # registration address (contains "302/2") before room number
    ("пр-т Дзержинского, 85, ком. 302/2", "{{ registration_address }}"),
    ("302/2", "{{ room_number }}"),
    ("Туркменистана", "{{ citizenship }}"),
    ("Шаназаров Мырат", "{{ full_name }}"),
    ("15.05.2007", "{{ birth_date }}"),
    ("LB00258610", "{{ id_number }}"),
    ("+37529354-11-59", "{{ phone }}"),
    ("30.06.2028", "{{ contract_end_date }}"),
    ("0047390 003370", "{{ contract_number }}"),
    ("« 21 »  июля 2026", "{{ sign_date }}"),
    ("«21» июля 2026", "{{ order_date }}"),
    ("№ 228", "№ {{ order_number }}"),
]


def build():
    doc = Document(str(SRC))
    for search, replace in REPLACEMENTS:
        hits = 0
        for p in iter_paragraphs(doc):
            if replace_first_in_paragraph(p, search, replace):
                hits += 1
        print(f"{'OK ' if hits else 'MISS'} [{hits}] {search[:40]!r} -> {replace}")
    # Optional manual-fill line — rendered only when the 'note' field is provided.
    from docx.oxml import OxmlElement
    from docx.text.paragraph import Paragraph

    def insert_after(paragraph, text):
        new_p = OxmlElement("w:p")
        paragraph._p.addnext(new_p)
        np = Paragraph(new_p, paragraph._parent)
        if text:
            run = np.add_run(text)
            run.font.name = "Times New Roman"
        return np

    anchor = None
    for p in iter_paragraphs(doc):
        if "факсимиле личной подписи" in p.text:
            anchor = p
            break
    if anchor is not None:
        p1 = insert_after(anchor, "{%p if note %}")
        p2 = insert_after(p1, "Дополнительно: {{ note }}")
        insert_after(p2, "{%p endif %}")
        print("OK  note section inserted")
    else:
        print("MISS note anchor not found")

    doc.save(str(OUT))
    print(f"\nSaved template to {OUT}")


if __name__ == "__main__":
    build()
