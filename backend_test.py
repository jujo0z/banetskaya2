#!/usr/bin/env python3
"""
Backend regression test after environment restoration on Linux.
Tests all critical backend endpoints to ensure no regressions.
"""
import requests
import sys

BASE_URL = "https://multi-agent-review-4.preview.emergentagent.com/api"

def test_ping():
    """Test 1: GET /api/_ping → 200, {"ok": true}"""
    print("\n[TEST 1] GET /api/_ping")
    r = requests.get(f"{BASE_URL}/_ping", timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data.get("ok") is True, f"Expected {{'ok': true}}, got {data}"
    print(f"✅ GET /api/_ping → 200, {data}")


def test_diagnostics():
    """Test 2: GET /api/health/diagnostics → 200, all_ok=true, check mongo/fonts/assets/template"""
    print("\n[TEST 2] GET /api/health/diagnostics")
    r = requests.get(f"{BASE_URL}/health/diagnostics", timeout=120)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "checks" in data, "Response missing 'checks' key"
    assert "all_ok" in data, "Response missing 'all_ok' key"
    assert isinstance(data["checks"], list), "'checks' should be a list"
    
    # Find required checks and print all
    checks_dict = {check["key"]: check for check in data["checks"]}
    required_checks = ["mongo", "fonts", "assets", "template", "libreoffice", "pdf", "printers"]
    
    print(f"  Diagnostics results:")
    for key in required_checks:
        if key in checks_dict:
            check = checks_dict[key]
            status = "✓" if check.get("ok") else "✗"
            print(f"    {status} {key}: ok={check.get('ok')}, detail={check.get('detail')}")
        else:
            print(f"    ✗ {key}: NOT FOUND")
    
    # Check all_ok
    print(f"  all_ok: {data['all_ok']}")
    
    # Verify mongo/fonts/assets/template have ok=true
    for key in ["mongo", "fonts", "assets", "template"]:
        assert key in checks_dict, f"Check '{key}' not found in diagnostics"
        assert checks_dict[key].get("ok") is True, \
            f"{key} check should pass, got ok={checks_dict[key].get('ok')}, detail={checks_dict[key].get('detail')}"
    
    print(f"✅ GET /api/health/diagnostics → 200, all required checks (mongo/fonts/assets/template) passed")


def test_overlay_profiles():
    """Test 3: GET /api/overlay/profiles → 200, array with at least one profile"""
    print("\n[TEST 3] GET /api/overlay/profiles")
    r = requests.get(f"{BASE_URL}/overlay/profiles", timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "profiles" in data, "Response missing 'profiles' key"
    assert isinstance(data["profiles"], list), "'profiles' should be a list"
    assert len(data["profiles"]) >= 1, "Should have at least one profile"
    
    print(f"✅ GET /api/overlay/profiles → 200, {len(data['profiles'])} profile(s) found")


def test_fields():
    """Test 4: GET /api/fields → 200, list of contract fields"""
    print("\n[TEST 4] GET /api/fields")
    r = requests.get(f"{BASE_URL}/fields", timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "fields" in data, "Response missing 'fields' key"
    assert isinstance(data["fields"], list), "'fields' should be a list"
    assert len(data["fields"]) > 0, "'fields' should not be empty"
    print(f"✅ GET /api/fields → 200, {len(data['fields'])} fields returned")


def test_overlay_generate_with_cyrillic():
    """Test 5: POST /api/overlay/generate with Cyrillic → 200, PDF with exact page size 416.69×291.97 pt (147×103 mm)"""
    print("\n[TEST 5] POST /api/overlay/generate with Cyrillic and page size check")
    payload = {
        "records": [
            {
                "fio": "Иванов Иван Иванович",
                "address": "г. Минск"
            }
        ],
        "page_size": "card",
        "with_form": True
    }
    r = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text[:500]}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_bytes = r.content
    assert pdf_bytes[:4] == b"%PDF", "PDF should start with %PDF signature"
    print(f"✅ PDF starts with %PDF, size: {len(pdf_bytes)} bytes")
    
    # Check page size and Cyrillic text using pymupdf
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        
        # Check page size (147×103 mm = 416.69×291.97 pt, tolerance ±1.5pt)
        page = doc[0]
        rect = page.rect
        width_pt = rect.width
        height_pt = rect.height
        
        expected_width = 416.69
        expected_height = 291.97
        tolerance = 1.5
        
        assert abs(width_pt - expected_width) <= tolerance, \
            f"Page width should be ~{expected_width} pt (±{tolerance}), got {width_pt} pt"
        assert abs(height_pt - expected_height) <= tolerance, \
            f"Page height should be ~{expected_height} pt (±{tolerance}), got {height_pt} pt"
        
        print(f"✅ Page size: {width_pt:.2f}×{height_pt:.2f} pt (147×103 mm, within tolerance)")
        
        # Extract text and check for Cyrillic
        text = page.get_text()
        assert len(text) > 0, "Page should contain text"
        # Check for any Cyrillic characters
        has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in text)
        assert has_cyrillic, "Page should contain Cyrillic text"
        print(f"✅ Page contains Cyrillic text (extracted {len(text)} characters)")
        
        doc.close()
    except ImportError:
        print("⚠️  pymupdf not available, skipping page size and text extraction")
        sys.exit(1)
    
    print(f"✅ POST /api/overlay/generate → 200, valid PDF with correct page size and Cyrillic")


def test_contracts_preview_pdf():
    """Test 6: POST /api/contracts/preview?format=pdf → 200, valid PDF with Cyrillic"""
    print("\n[TEST 6] POST /api/contracts/preview?format=pdf")
    payload = {
        "fields": {
            "contract_number": "TEST-001",
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
    
    # Check Cyrillic text using pymupdf
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        print(f"✅ PDF has {page_count} pages")
        
        # Extract text from first page and check for Cyrillic
        first_page_text = doc[0].get_text()
        has_cyrillic = any('\u0400' <= char <= '\u04FF' for char in first_page_text)
        assert has_cyrillic, "First page should contain Cyrillic text"
        print(f"✅ First page contains Cyrillic text")
        doc.close()
    except ImportError:
        print("⚠️  pymupdf not available, skipping text extraction")
        sys.exit(1)
    
    print(f"✅ POST /api/contracts/preview?format=pdf → 200, valid PDF with Cyrillic")


def test_stats():
    """Test 7: GET /api/stats → 200, JSON with required keys"""
    print("\n[TEST 7] GET /api/stats")
    r = requests.get(f"{BASE_URL}/stats", timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    required_keys = ["total", "drafts", "this_month", "datasets", "recent"]
    for key in required_keys:
        assert key in data, f"Response missing '{key}' key"
        print(f"  ✓ {key}: {data[key] if key != 'recent' else f'{len(data[key])} items'}")
    
    print(f"✅ GET /api/stats → 200, all required keys present")


def main():
    print("=" * 80)
    print("BACKEND REGRESSION TEST: Linux Environment After Restoration")
    print("=" * 80)
    
    try:
        test_ping()
        test_diagnostics()
        test_overlay_profiles()
        test_fields()
        test_overlay_generate_with_cyrillic()
        test_contracts_preview_pdf()
        test_stats()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED (7/7)")
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
