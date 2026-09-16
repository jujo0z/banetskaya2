#!/usr/bin/env python3
"""
Backend testing for editable templates feature (Forms 19/24).
Tests ONLY backend API endpoints.
"""
import requests
import json
import sys
from io import BytesIO

# Get backend URL from frontend/.env
BACKEND_URL = "https://root-monitor-1.preview.emergentagent.com/api"

def test_forma19_template_get():
    """Test 1: GET /api/forma19/template"""
    print("\n=== TEST 1: GET /api/forma19/template ===")
    r = requests.get(f"{BACKEND_URL}/forma19/template")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    # Check required keys
    assert "template" in data, "Missing 'template' key"
    assert "slots" in data, "Missing 'slots' key"
    assert "is_custom" in data, "Missing 'is_custom' key"
    assert "page_count" in data, "Missing 'page_count' key"
    assert "page_w_mm" in data, "Missing 'page_w_mm' key"
    assert "page_h_mm" in data, "Missing 'page_h_mm' key"
    
    # Check values
    assert isinstance(data["template"], list), "template should be a list"
    assert len(data["template"]) > 0, "template should not be empty"
    assert isinstance(data["slots"], list), "slots should be a list"
    assert len(data["slots"]) > 0, "slots should not be empty"
    assert data["is_custom"] == False, f"is_custom should be False initially, got {data['is_custom']}"
    assert data["page_count"] == 2, f"page_count should be 2, got {data['page_count']}"
    assert data["page_w_mm"] == 105, f"page_w_mm should be 105, got {data['page_w_mm']}"
    assert data["page_h_mm"] == 145, f"page_h_mm should be 145, got {data['page_h_mm']}"
    
    # Check template elements have required types
    element_types = set()
    field_count = 0
    for el in data["template"]:
        el_type = el.get("type")
        element_types.add(el_type)
        if el_type == "field":
            field_count += 1
    
    assert "text" in element_types, "template should have 'text' elements"
    assert "line" in element_types, "template should have 'line' elements"
    assert "rect" in element_types, "template should have 'rect' elements"
    assert "field" in element_types, "template should have 'field' elements"
    assert field_count > 10, f"template should have many 'field' elements, got {field_count}"
    
    # Check slots structure
    for slot in data["slots"]:
        assert "slot" in slot, "Each slot should have 'slot' key"
        assert "label" in slot, "Each slot should have 'label' key"
    
    print(f"✅ PASS: template has {len(data['template'])} elements, {field_count} fields")
    print(f"✅ PASS: slots has {len(data['slots'])} items")
    print(f"✅ PASS: is_custom={data['is_custom']}, page_count={data['page_count']}, dimensions={data['page_w_mm']}×{data['page_h_mm']} mm")
    
    return data["template"]


def test_forma24_template_get():
    """Test 2: GET /api/forma24/template"""
    print("\n=== TEST 2: GET /api/forma24/template ===")
    r = requests.get(f"{BACKEND_URL}/forma24/template")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    # Check required keys
    assert "template" in data, "Missing 'template' key"
    assert "slots" in data, "Missing 'slots' key"
    assert "is_custom" in data, "Missing 'is_custom' key"
    assert data["is_custom"] == False, f"is_custom should be False initially, got {data['is_custom']}"
    
    # Check template is non-empty
    assert isinstance(data["template"], list), "template should be a list"
    assert len(data["template"]) > 0, "template should not be empty"
    
    field_count = sum(1 for el in data["template"] if el.get("type") == "field")
    
    print(f"✅ PASS: template has {len(data['template'])} elements, {field_count} fields")
    print(f"✅ PASS: is_custom={data['is_custom']}")
    
    return data["template"]


def test_forma19_template_save(original_template):
    """Test 3: POST /api/forma19/template (modify and save)"""
    print("\n=== TEST 3: POST /api/forma19/template (save custom) ===")
    
    # Modify one text element
    modified_template = []
    modified = False
    for el in original_template:
        el_copy = dict(el)
        if not modified and el.get("type") == "text":
            # Add " ТЕСТ" to the text
            el_copy["text"] = el.get("text", "") + " ТЕСТ"
            modified = True
            print(f"Modified element: {el.get('text', '')} -> {el_copy['text']}")
        modified_template.append(el_copy)
    
    assert modified, "Should have modified at least one text element"
    
    # Save the modified template
    r = requests.post(f"{BACKEND_URL}/forma19/template", 
                     json={"template": modified_template})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "saved" in data, "Missing 'saved' key"
    assert data["saved"] == True, f"saved should be True, got {data['saved']}"
    assert "count" in data, "Missing 'count' key"
    assert data["count"] == len(modified_template), f"count should be {len(modified_template)}, got {data['count']}"
    
    print(f"✅ PASS: saved={data['saved']}, count={data['count']}")
    
    # Verify the change persisted
    print("\n=== TEST 3b: Verify custom template persisted ===")
    r = requests.get(f"{BACKEND_URL}/forma19/template")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert data["is_custom"] == True, f"is_custom should be True after save, got {data['is_custom']}"
    
    # Find the modified element
    found_modification = False
    for el in data["template"]:
        if el.get("type") == "text" and " ТЕСТ" in el.get("text", ""):
            found_modification = True
            print(f"Found modified element: {el.get('text')}")
            break
    
    assert found_modification, "Modified text element not found in saved template"
    
    print(f"✅ PASS: is_custom={data['is_custom']}, modification present")


def test_forma19_preview():
    """Test 4: POST /api/forma19/preview (PDF generation)"""
    print("\n=== TEST 4: POST /api/forma19/preview ===")
    
    payload = {
        "records": [
            {
                "surname": "Иванов",
                "first_name": "Иван",
                "birth_year": "2005",
                "citizenship": "РБ"
            }
        ],
        "duplex_flip": "long"
    }
    
    r = requests.post(f"{BACKEND_URL}/forma19/preview", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_data = r.content
    assert pdf_data[:4] == b"%PDF", "PDF should start with %PDF signature"
    
    # Check page count using pymupdf
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page_count = len(doc)
        doc.close()
        assert page_count == 2, f"PDF should have 2 pages (front+back), got {page_count}"
        print(f"✅ PASS: Valid PDF, {page_count} pages, {len(pdf_data)} bytes")
    except ImportError:
        print(f"⚠️  WARNING: pymupdf not available, skipping page count check")
        print(f"✅ PASS: Valid PDF, {len(pdf_data)} bytes")


def test_forma24_preview():
    """Test 4b: POST /api/forma24/preview (PDF generation)"""
    print("\n=== TEST 4b: POST /api/forma24/preview ===")
    
    payload = {
        "records": [
            {
                "surname": "Петров",
                "first_name": "Пётр"
            }
        ],
        "duplex_flip": "long"
    }
    
    r = requests.post(f"{BACKEND_URL}/forma24/preview", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_data = r.content
    assert pdf_data[:4] == b"%PDF", "PDF should start with %PDF signature"
    
    # Check page count
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page_count = len(doc)
        doc.close()
        assert page_count == 2, f"PDF should have 2 pages (front+back), got {page_count}"
        print(f"✅ PASS: Valid PDF, {page_count} pages, {len(pdf_data)} bytes")
    except ImportError:
        print(f"⚠️  WARNING: pymupdf not available, skipping page count check")
        print(f"✅ PASS: Valid PDF, {len(pdf_data)} bytes")


def test_forma19_preview_png():
    """Test 5: POST /api/forma19/preview-png (PNG generation)"""
    print("\n=== TEST 5: POST /api/forma19/preview-png ===")
    
    payload = {
        "records": [
            {
                "surname": "Тестов",
                "first_name": "Тест"
            }
        ],
        "side": "front"
    }
    
    # Test front side
    r = requests.post(f"{BACKEND_URL}/forma19/preview-png", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "image/png", \
        f"Expected image/png, got {r.headers.get('Content-Type')}"
    
    png_data = r.content
    assert png_data[:4] == b"\x89PNG", "PNG should start with PNG signature"
    print(f"✅ PASS: Valid PNG (front), {len(png_data)} bytes")
    
    # Test back side
    payload["side"] = "back"
    r = requests.post(f"{BACKEND_URL}/forma19/preview-png", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "image/png", \
        f"Expected image/png, got {r.headers.get('Content-Type')}"
    
    png_data_back = r.content
    assert png_data_back[:4] == b"\x89PNG", "PNG should start with PNG signature"
    print(f"✅ PASS: Valid PNG (back), {len(png_data_back)} bytes")


def test_package():
    """Test 6: POST /api/package (combined package)"""
    print("\n=== TEST 6: POST /api/package ===")
    
    payload = {
        "people": [
            {
                "ФИО": "Иванов Иван Иванович",
                "Номер комнаты": "902/2"
            }
        ],
        "duplex_flip": "long",
        "include": {
            "forma19": True,
            "forma24": True,
            "contract": False,
            "soobshenie": False,
            "zayavlenie": False
        }
    }
    
    r = requests.post(f"{BACKEND_URL}/package", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert r.headers.get("Content-Type") == "application/pdf", \
        f"Expected application/pdf, got {r.headers.get('Content-Type')}"
    
    pdf_data = r.content
    assert pdf_data[:4] == b"%PDF", "PDF should start with %PDF signature"
    
    # Check it's a valid PDF
    try:
        import pymupdf
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page_count = len(doc)
        doc.close()
        print(f"✅ PASS: Valid combined PDF (F19+F24), {page_count} pages, {len(pdf_data)} bytes")
    except ImportError:
        print(f"✅ PASS: Valid combined PDF (F19+F24), {len(pdf_data)} bytes")


def test_forma24_template_save():
    """Test 7: POST /api/forma24/template (save default as-is)"""
    print("\n=== TEST 7: POST /api/forma24/template (save default) ===")
    
    # Get default template
    r = requests.get(f"{BACKEND_URL}/forma24/template")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    template = data["template"]
    
    # Save it as-is
    r = requests.post(f"{BACKEND_URL}/forma24/template", 
                     json={"template": template})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    result = r.json()
    
    assert result["saved"] == True, f"saved should be True, got {result['saved']}"
    print(f"✅ PASS: saved={result['saved']}, count={result['count']}")
    
    # Verify is_custom is now True
    r = requests.get(f"{BACKEND_URL}/forma24/template")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["is_custom"] == True, f"is_custom should be True after save, got {data['is_custom']}"
    print(f"✅ PASS: is_custom={data['is_custom']}")


def test_regression_fields():
    """Test 8: Regression - GET /api/forma19/fields and /api/forma24/fields"""
    print("\n=== TEST 8: REGRESSION - GET /api/forma19/fields ===")
    
    r = requests.get(f"{BACKEND_URL}/forma19/fields")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "groups" in data, "Missing 'groups' key"
    assert "keys" in data, "Missing 'keys' key"
    assert isinstance(data["groups"], list), "groups should be a list"
    assert isinstance(data["keys"], list), "keys should be a list"
    print(f"✅ PASS: forma19/fields returns {len(data['groups'])} groups, {len(data['keys'])} keys")
    
    print("\n=== TEST 8b: REGRESSION - GET /api/forma24/fields ===")
    r = requests.get(f"{BACKEND_URL}/forma24/fields")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "groups" in data, "Missing 'groups' key"
    assert "keys" in data, "Missing 'keys' key"
    print(f"✅ PASS: forma24/fields returns {len(data['groups'])} groups, {len(data['keys'])} keys")


def test_regression_prefill():
    """Test 8c: Regression - POST /api/forma19/prefill"""
    print("\n=== TEST 8c: REGRESSION - POST /api/forma19/prefill ===")
    
    payload = {
        "students": [
            {
                "full_name": "Иванов Иван Иванович",
                "birth_date": "01.01.2005",
                "passport_number": "AB1234567"
            }
        ]
    }
    
    r = requests.post(f"{BACKEND_URL}/forma19/prefill", json=payload)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "records" in data, "Missing 'records' key"
    assert len(data["records"]) > 0, "records should not be empty"
    
    rec = data["records"][0]
    assert rec.get("surname") == "Иванов", f"surname should be 'Иванов', got {rec.get('surname')}"
    assert rec.get("first_name") == "Иван", f"first_name should be 'Иван', got {rec.get('first_name')}"
    assert rec.get("patronymic") == "Иванович", f"patronymic should be 'Иванович', got {rec.get('patronymic')}"
    
    print(f"✅ PASS: prefill works correctly, parsed ФИО: {rec.get('surname')} {rec.get('first_name')} {rec.get('patronymic')}")


def test_forma19_template_reset():
    """Test 9: POST /api/forma19/template/reset (CRITICAL - restore defaults)"""
    print("\n=== TEST 9: POST /api/forma19/template/reset (CRITICAL) ===")
    
    r = requests.post(f"{BACKEND_URL}/forma19/template/reset")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "reset" in data, "Missing 'reset' key"
    assert data["reset"] == True, f"reset should be True, got {data['reset']}"
    print(f"✅ PASS: reset={data['reset']}")
    
    # Verify is_custom is now False
    r = requests.get(f"{BACKEND_URL}/forma19/template")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["is_custom"] == False, f"is_custom should be False after reset, got {data['is_custom']}"
    print(f"✅ PASS: is_custom={data['is_custom']} (default restored)")


def test_forma24_template_reset():
    """Test 9b: POST /api/forma24/template/reset (CRITICAL - restore defaults)"""
    print("\n=== TEST 9b: POST /api/forma24/template/reset (CRITICAL) ===")
    
    r = requests.post(f"{BACKEND_URL}/forma24/template/reset")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    
    assert "reset" in data, "Missing 'reset' key"
    assert data["reset"] == True, f"reset should be True, got {data['reset']}"
    print(f"✅ PASS: reset={data['reset']}")
    
    # Verify is_custom is now False
    r = requests.get(f"{BACKEND_URL}/forma24/template")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    data = r.json()
    assert data["is_custom"] == False, f"is_custom should be False after reset, got {data['is_custom']}"
    print(f"✅ PASS: is_custom={data['is_custom']} (default restored)")


def main():
    """Run all tests"""
    print("=" * 80)
    print("BACKEND TESTING: Editable Templates for Forms 19/24")
    print("=" * 80)
    
    tests = [
        ("GET /api/forma19/template", test_forma19_template_get),
        ("GET /api/forma24/template", test_forma24_template_get),
        ("POST /api/forma19/template (save custom)", test_forma19_template_save),
        ("POST /api/forma19/preview", test_forma19_preview),
        ("POST /api/forma24/preview", test_forma24_preview),
        ("POST /api/forma19/preview-png", test_forma19_preview_png),
        ("POST /api/package", test_package),
        ("POST /api/forma24/template (save default)", test_forma24_template_save),
        ("REGRESSION: fields", test_regression_fields),
        ("REGRESSION: prefill", test_regression_prefill),
        ("POST /api/forma19/template/reset (CRITICAL)", test_forma19_template_reset),
        ("POST /api/forma24/template/reset (CRITICAL)", test_forma24_template_reset),
    ]
    
    passed = 0
    failed = 0
    original_template = None
    
    for name, test_func in tests:
        try:
            if test_func == test_forma19_template_save:
                # Pass original template to this test
                result = test_func(original_template)
            elif test_func == test_forma19_template_get:
                # Save original template for later use
                original_template = test_func()
            else:
                test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {name}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {name}")
            print(f"   Exception: {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed out of {passed + failed} tests")
    print("=" * 80)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
