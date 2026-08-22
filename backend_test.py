#!/usr/bin/env python3
"""
Backend test for LibreOffice file:// URI profile fix (regression check on Linux).
Tests that the fix (using Path.as_uri() instead of "file://" + str(path)) doesn't
break the working Linux path.
"""
import requests
import sys

BASE_URL = "https://work-progress-49.preview.emergentagent.com/api"

def test_fields():
    """Test 1: GET /api/fields → 200 (список полей договора)"""
    print("\n[TEST 1] GET /api/fields")
    r = requests.get(f"{BASE_URL}/fields", timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "fields" in data, "Response missing 'fields' key"
    assert isinstance(data["fields"], list), "'fields' should be a list"
    assert len(data["fields"]) > 0, "'fields' should not be empty"
    print(f"✅ GET /api/fields → 200, {len(data['fields'])} fields returned")


def test_preview_pdf():
    """Test 2: POST /api/contracts/preview?format=pdf with minimal fields → 200,
    valid PDF with Cyrillic text"""
    print("\n[TEST 2] POST /api/contracts/preview?format=pdf")
    payload = {
        "fields": {
            "contract_number": "TEST-URI",
            "full_name": "Тестов Тест Тестович",
            "citizenship": "Республики Беларусь",
            "birth_date": "01.01.2000",
            "room_number": "101",
            "registration_address": "г. Минск, ул. Тестовая, д. 1",
            "passport_number": "AB1234567",
            "phone": "+375291234567"
        }
    }
    r = requests.post(f"{BASE_URL}/contracts/preview?format=pdf", json=payload, timeout=120)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:500]}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_bytes = r.content
    assert pdf_bytes[:4] == b"%PDF", "PDF should start with %PDF signature"
    print(f"✅ PDF starts with %PDF, size: {len(pdf_bytes)} bytes")
    
    # Check page count and Cyrillic text using pymupdf
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        assert page_count >= 1, f"Expected at least 1 page, got {page_count}"
        print(f"✅ PDF has {page_count} pages")
        
        # Extract text from first page and check for Cyrillic
        first_page_text = doc[0].get_text()
        assert "ДОГОВОР" in first_page_text or "договор" in first_page_text.lower(), \
            "First page should contain 'ДОГОВОР' (Cyrillic)"
        print(f"✅ First page contains Cyrillic text ('ДОГОВОР' found)")
        doc.close()
    except ImportError:
        print("⚠️  pymupdf not available, skipping page count and text extraction")
    
    print(f"✅ POST /api/contracts/preview?format=pdf → 200, valid PDF with Cyrillic")


def test_diagnostics():
    """Test 3: GET /api/health/diagnostics → 200, LibreOffice check passes with real conversion"""
    print("\n[TEST 3] GET /api/health/diagnostics")
    r = requests.get(f"{BASE_URL}/health/diagnostics", timeout=120)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "checks" in data, "Response missing 'checks' key"
    assert "all_ok" in data, "Response missing 'all_ok' key"
    assert isinstance(data["checks"], list), "'checks' should be a list"
    
    # Find LibreOffice check
    libreoffice_check = None
    pdf_check = None
    for check in data["checks"]:
        if check.get("key") == "libreoffice":
            libreoffice_check = check
        if check.get("key") == "pdf":
            pdf_check = check
    
    assert libreoffice_check is not None, "LibreOffice check not found in diagnostics"
    assert pdf_check is not None, "PDF check not found in diagnostics"
    
    # Check LibreOffice
    assert libreoffice_check.get("ok") is True, \
        f"LibreOffice check should pass, got ok={libreoffice_check.get('ok')}, detail={libreoffice_check.get('detail')}"
    detail = libreoffice_check.get("detail", "")
    assert detail.startswith("OK"), \
        f"LibreOffice detail should start with 'OK', got: {detail}"
    print(f"✅ LibreOffice check: ok=true, detail='{detail}'")
    
    # Check PDF generation
    assert pdf_check.get("ok") is True, \
        f"PDF check should pass, got ok={pdf_check.get('ok')}, detail={pdf_check.get('detail')}"
    print(f"✅ PDF check: ok=true, detail='{pdf_check.get('detail')}'")
    
    # Check all_ok
    assert data["all_ok"] is True, \
        f"all_ok should be true, got {data['all_ok']}"
    print(f"✅ all_ok=true")
    
    print(f"✅ GET /api/health/diagnostics → 200, all checks passed")


def test_overlay_generate():
    """Test 4: POST /api/overlay/generate with card page_size → 200 application/pdf"""
    print("\n[TEST 4] POST /api/overlay/generate")
    payload = {
        "records": [{"fio": "Тест"}],
        "page_size": "card"
    }
    r = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:500]}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_bytes = r.content
    assert pdf_bytes[:4] == b"%PDF", "PDF should start with %PDF signature"
    print(f"✅ PDF starts with %PDF, size: {len(pdf_bytes)} bytes")
    print(f"✅ POST /api/overlay/generate → 200 application/pdf")


def main():
    print("=" * 80)
    print("BACKEND TEST: LibreOffice file:// URI Profile Fix (Regression on Linux)")
    print("=" * 80)
    
    try:
        test_fields()
        test_preview_pdf()
        test_diagnostics()
        test_overlay_generate()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED (4/4)")
        print("=" * 80)
        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
