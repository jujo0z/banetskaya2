#!/usr/bin/env python3
"""
Backend testing for Форма 19 (Адресный листок прибытия) + regression tests.
Tests all /api/forma19/* endpoints and verifies no regression in main endpoints.
"""
import requests
import sys
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
BASE_URL = f"{BACKEND_URL}/api"

print(f"Testing backend at: {BASE_URL}")
print("=" * 80)

# Test results tracking
tests_passed = 0
tests_failed = 0
failures = []

def test(name, fn):
    """Run a test and track results."""
    global tests_passed, tests_failed
    try:
        print(f"\n[TEST] {name}")
        fn()
        print(f"✅ PASS: {name}")
        tests_passed += 1
        return True
    except AssertionError as e:
        print(f"❌ FAIL: {name}")
        print(f"   Error: {e}")
        tests_failed += 1
        failures.append({"test": name, "error": str(e)})
        return False
    except Exception as e:
        print(f"❌ ERROR: {name}")
        print(f"   Exception: {e}")
        tests_failed += 1
        failures.append({"test": name, "error": f"Exception: {e}"})
        return False


# ============================================================================
# ФОРМА 19 TESTS
# ============================================================================

def test_forma19_fields():
    """Test GET /api/forma19/fields returns groups and keys."""
    r = requests.get(f"{BASE_URL}/forma19/fields", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "groups" in data, "Missing 'groups' key"
    assert "keys" in data, "Missing 'keys' key"
    assert isinstance(data["groups"], list), "groups should be a list"
    assert isinstance(data["keys"], list), "keys should be a list"
    assert len(data["groups"]) > 0, "groups should not be empty"
    assert len(data["keys"]) > 0, "keys should not be empty"
    
    # Check for required keys
    required_keys = ["surname", "first_name", "patronymic", "birth_day", "sex", 
                     "citizenship", "res_city", "purpose", "passport_series"]
    for key in required_keys:
        assert key in data["keys"], f"Missing required key: {key}"
    
    # Verify groups structure
    for group in data["groups"]:
        assert "group" in group, "Each group should have 'group' field"
        assert "fields" in group, "Each group should have 'fields' field"
        assert isinstance(group["fields"], list), "fields should be a list"
        for field in group["fields"]:
            assert "key" in field, "Each field should have 'key'"
            assert "label" in field, "Each field should have 'label'"
    
    print(f"   ✓ Found {len(data['groups'])} groups with {len(data['keys'])} total keys")
    print(f"   ✓ All required keys present: {', '.join(required_keys[:5])}...")


def test_forma19_defaults_get():
    """Test GET /api/forma19/defaults returns defaults object."""
    r = requests.get(f"{BASE_URL}/forma19/defaults", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "defaults" in data, "Missing 'defaults' key"
    assert isinstance(data["defaults"], dict), "defaults should be a dict"
    print(f"   ✓ Defaults retrieved: {data['defaults']}")


def test_forma19_defaults_save():
    """Test POST /api/forma19/defaults saves and persists values."""
    # Save defaults
    test_defaults = {
        "res_city": "Минск",
        "purpose": "на учёбу",
        "reg_authority": "ОГИМ Московского РУВД г. Минска"
    }
    r = requests.post(f"{BASE_URL}/forma19/defaults", 
                     json={"defaults": test_defaults}, 
                     timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data.get("saved") == True, "saved should be true"
    assert "defaults" in data, "Missing 'defaults' in response"
    print(f"   ✓ Saved defaults: {test_defaults}")
    
    # Verify persistence - GET again
    r2 = requests.get(f"{BASE_URL}/forma19/defaults", timeout=10)
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
    data2 = r2.json()
    saved_defaults = data2.get("defaults", {})
    assert saved_defaults.get("res_city") == "Минск", "res_city not persisted"
    assert saved_defaults.get("purpose") == "на учёбу", "purpose not persisted"
    assert saved_defaults.get("reg_authority") == "ОГИМ Московского РУВД г. Минска", "reg_authority not persisted"
    print(f"   ✓ Persistence verified: {saved_defaults}")


def test_forma19_prefill():
    """Test POST /api/forma19/prefill parses student data correctly."""
    students = [{
        "full_name": "Иванов Иван Иванович",
        "birth_date": "01.09.2007",
        "citizenship": "РБ",
        "passport_number": "AB1234567",
        "id_number": "1234567A001PB5",
        "passport_issued_by": "РОВД Минска"
    }]
    
    r = requests.post(f"{BASE_URL}/forma19/prefill", 
                     json={"students": students}, 
                     timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "records" in data, "Missing 'records' key"
    assert len(data["records"]) == 1, "Should have 1 record"
    
    rec = data["records"][0]
    # Check parsed fields
    assert rec.get("surname") == "Иванов", f"surname should be 'Иванов', got {rec.get('surname')}"
    assert rec.get("first_name") == "Иван", f"first_name should be 'Иван', got {rec.get('first_name')}"
    assert rec.get("patronymic") == "Иванович", f"patronymic should be 'Иванович', got {rec.get('patronymic')}"
    assert rec.get("birth_day") == "01", f"birth_day should be '01', got {rec.get('birth_day')}"
    assert rec.get("birth_month") == "сентября", f"birth_month should be 'сентября', got {rec.get('birth_month')}"
    assert rec.get("birth_year") == "2007", f"birth_year should be '2007', got {rec.get('birth_year')}"
    assert rec.get("passport_series") == "AB", f"passport_series should be 'AB', got {rec.get('passport_series')}"
    assert rec.get("passport_number") == "1234567", f"passport_number should be '1234567', got {rec.get('passport_number')}"
    assert rec.get("id_number") == "1234567A001PB5", f"id_number mismatch"
    
    print(f"   ✓ Parsed: {rec.get('surname')} {rec.get('first_name')} {rec.get('patronymic')}")
    print(f"   ✓ Birth: {rec.get('birth_day')} {rec.get('birth_month')} {rec.get('birth_year')}")
    print(f"   ✓ Passport: {rec.get('passport_series')}{rec.get('passport_number')}")


def test_forma19_preview_pdf():
    """Test POST /api/forma19/preview generates valid PDF with 2 A4 pages."""
    try:
        import pymupdf
    except ImportError:
        print("   ⚠ pymupdf not available, installing...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pymupdf"], 
                      capture_output=True, timeout=60)
        import pymupdf
    
    records = [
        {
            "surname": "Петрович",
            "first_name": "Пётр",
            "citizenship": "РБ",
            "purpose": "на учёбу"
        },
        {
            "surname": "Иванов",
            "first_name": "Иван"
        }
    ]
    
    r = requests.post(f"{BASE_URL}/forma19/preview", 
                     json={"records": records, "duplex_flip": "long"}, 
                     timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_data = r.content
    assert pdf_data.startswith(b"%PDF"), "PDF should start with %PDF signature"
    print(f"   ✓ Valid PDF, size: {len(pdf_data)} bytes")
    
    # Check page count and size with pymupdf
    doc = pymupdf.open(stream=pdf_data, filetype="pdf")
    page_count = len(doc)
    assert page_count == 2, f"Expected EXACTLY 2 pages, got {page_count}"
    print(f"   ✓ Page count: {page_count} (correct)")
    
    # Check page size (A4: 595.28 × 841.89 pt)
    page = doc[0]
    rect = page.rect
    width, height = rect.width, rect.height
    print(f"   ✓ Page 0 size: {width:.2f} × {height:.2f} pt")
    
    # Allow ±2pt tolerance
    assert abs(width - 595.28) <= 2, f"Width {width:.2f} not A4 (595.28±2)"
    assert abs(height - 841.89) <= 2, f"Height {height:.2f} not A4 (841.89±2)"
    print(f"   ✓ Page size is A4 (595.28×841.89 pt, tolerance ±2pt)")
    
    # Extract text and check for Cyrillic
    text = page.get_text()
    cyrillic_checks = ["АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ", "Петрович", "на учёбу", "Идентификационный номер"]
    found = []
    for check in cyrillic_checks:
        if check in text:
            found.append(check)
    
    assert len(found) > 0, f"No Cyrillic text found. Expected: {cyrillic_checks}"
    print(f"   ✓ Cyrillic text extracted: {', '.join(found[:3])}...")
    
    doc.close()


def test_forma19_preview_png():
    """Test POST /api/forma19/preview-png returns valid PNG."""
    records = [
        {"surname": "Тестов", "first_name": "Тест"},
        {"surname": "Иванов", "first_name": "Иван"}
    ]
    
    r = requests.post(f"{BASE_URL}/forma19/preview-png", 
                     json={"records": records, "duplex_flip": "long"}, 
                     timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "image/png", \
        f"Expected image/png, got {r.headers.get('Content-Type')}"
    
    png_data = r.content
    assert png_data.startswith(b"\x89PNG"), "PNG should start with PNG signature"
    assert len(png_data) > 1000, f"PNG too small: {len(png_data)} bytes"
    print(f"   ✓ Valid PNG, size: {len(png_data)} bytes")


def test_forma19_preview_duplex_short():
    """Test POST /api/forma19/preview with duplex_flip='short' generates valid PDF."""
    records = [
        {"surname": "Тестов", "first_name": "Тест"},
        {"surname": "Петров", "first_name": "Пётр"}
    ]
    
    r = requests.post(f"{BASE_URL}/forma19/preview", 
                     json={"records": records, "duplex_flip": "short"}, 
                     timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_data = r.content
    assert pdf_data.startswith(b"%PDF"), "PDF should start with %PDF signature"
    
    # Check page count
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page_count = len(doc)
        assert page_count == 2, f"Expected 2 pages, got {page_count}"
        print(f"   ✓ Valid PDF with {page_count} pages (duplex_flip=short)")
        doc.close()
    except ImportError:
        print(f"   ✓ Valid PDF, size: {len(pdf_data)} bytes (pymupdf not available for page check)")


# ============================================================================
# REGRESSION TESTS
# ============================================================================

def test_regression_ping():
    """Regression: GET /api/_ping should return ok:true."""
    r = requests.get(f"{BASE_URL}/_ping", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data.get("ok") == True, "ok should be true"
    print(f"   ✓ Ping successful: {data}")


def test_regression_fields():
    """Regression: GET /api/fields should return contract fields."""
    r = requests.get(f"{BASE_URL}/fields", timeout=10)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert "fields" in data, "Missing 'fields' key"
    assert isinstance(data["fields"], list), "fields should be a list"
    assert len(data["fields"]) > 0, "fields should not be empty"
    print(f"   ✓ Found {len(data['fields'])} contract fields")


def test_regression_contracts_preview():
    """Regression: POST /api/contracts/preview?format=pdf should return valid PDF."""
    try:
        import pymupdf
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pymupdf"], 
                      capture_output=True, timeout=60)
        import pymupdf
    
    minimal_fields = {
        "contract_number": "TEST-FORMA19",
        "full_name": "Тестов Тест Тестович",
        "citizenship": "Республики Беларусь",
        "birth_date": "01.01.2000",
        "room_number": "101",
        "registration_address": "г. Минск, ул. Тестовая, д. 1",
        "passport_number": "AB1234567",
        "phone": "+375291234567"
    }
    
    r = requests.post(f"{BASE_URL}/contracts/preview?format=pdf", 
                     json={"fields": minimal_fields}, 
                     timeout=30)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_data = r.content
    assert pdf_data.startswith(b"%PDF"), "PDF should start with %PDF signature"
    print(f"   ✓ Valid PDF, size: {len(pdf_data)} bytes")
    
    # Verify it's a multi-page document
    doc = pymupdf.open(stream=pdf_data, filetype="pdf")
    page_count = len(doc)
    assert page_count >= 1, f"Expected at least 1 page, got {page_count}"
    print(f"   ✓ PDF has {page_count} pages")
    doc.close()


# ============================================================================
# RUN ALL TESTS
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("ФОРМА 19 TESTS")
    print("=" * 80)
    
    test("1. GET /api/forma19/fields", test_forma19_fields)
    test("2. GET /api/forma19/defaults", test_forma19_defaults_get)
    test("3. POST /api/forma19/defaults (save + persist)", test_forma19_defaults_save)
    test("4. POST /api/forma19/prefill", test_forma19_prefill)
    test("5. POST /api/forma19/preview (PDF, duplex_flip=long)", test_forma19_preview_pdf)
    test("6. POST /api/forma19/preview-png", test_forma19_preview_png)
    test("7. POST /api/forma19/preview (duplex_flip=short)", test_forma19_preview_duplex_short)
    
    print("\n" + "=" * 80)
    print("REGRESSION TESTS")
    print("=" * 80)
    
    test("R1. GET /api/_ping", test_regression_ping)
    test("R2. GET /api/fields", test_regression_fields)
    test("R3. POST /api/contracts/preview?format=pdf", test_regression_contracts_preview)
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"📊 Total:  {tests_passed + tests_failed}")
    
    if failures:
        print("\n" + "=" * 80)
        print("FAILED TESTS DETAILS")
        print("=" * 80)
        for f in failures:
            print(f"\n❌ {f['test']}")
            print(f"   {f['error']}")
    
    print("\n" + "=" * 80)
    
    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
