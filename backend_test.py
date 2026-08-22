#!/usr/bin/env python3
"""
Backend testing for overlay printing with exact page size verification.
Tests the 147×103 mm (card) page size and Linux degradation for silent printing.
"""
import io
import sys
import requests

# Use pymupdf as specified in the review request
import pymupdf

# Backend URL from environment
BACKEND_URL = "https://1a44cbd3-e499-4c2e-b9f8-dd81fc5e4c75.preview.emergentagent.com/api"

# Page size constants (in points)
# 147 mm = 416.69 pt, 103 mm = 291.97 pt
CARD_WIDTH_PT = 416.69
CARD_HEIGHT_PT = 291.97
TOLERANCE_PT = 1.5

# A4 size in points
A4_WIDTH_PT = 595.0
A4_HEIGHT_PT = 842.0

def test_overlay_generate_card_without_form():
    """Test 1: POST /api/overlay/generate with page_size='card', with_form=false
    Should return 200, Content-Type application/pdf, valid PDF, page size ~416.69 × 291.97 pt"""
    print("\n=== TEST 1: POST /api/overlay/generate (page_size='card', with_form=false) ===")
    
    payload = {
        "records": [{"fio": "Тест Тестович"}],
        "page_size": "card",
        "with_form": False
    }
    
    response = requests.post(f"{BACKEND_URL}/overlay/generate", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/pdf" in response.headers.get('Content-Type', ''), "Expected Content-Type application/pdf"
    
    # Check PDF validity
    pdf_bytes = response.content
    assert pdf_bytes.startswith(b'%PDF'), "PDF should start with %PDF signature"
    print(f"✓ Valid PDF signature: {pdf_bytes[:8]}")
    
    # Check page size using pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    page = doc[0]
    rect = page.rect
    width_pt = rect.width
    height_pt = rect.height
    doc.close()
    
    print(f"Page size: {width_pt:.2f} × {height_pt:.2f} pt")
    print(f"Expected: {CARD_WIDTH_PT:.2f} × {CARD_HEIGHT_PT:.2f} pt (tolerance ±{TOLERANCE_PT} pt)")
    
    width_diff = abs(width_pt - CARD_WIDTH_PT)
    height_diff = abs(height_pt - CARD_HEIGHT_PT)
    
    assert width_diff <= TOLERANCE_PT, f"Width {width_pt:.2f} pt differs from expected {CARD_WIDTH_PT:.2f} pt by {width_diff:.2f} pt (tolerance {TOLERANCE_PT} pt)"
    assert height_diff <= TOLERANCE_PT, f"Height {height_pt:.2f} pt differs from expected {CARD_HEIGHT_PT:.2f} pt by {height_diff:.2f} pt (tolerance {TOLERANCE_PT} pt)"
    
    print(f"✓ Page size is correct: {width_pt:.2f} × {height_pt:.2f} pt (147×103 mm)")
    print("✅ TEST 1 PASSED\n")
    return True


def test_overlay_generate_card_with_form():
    """Test 2: POST /api/overlay/generate with page_size='card', with_form=true
    Should return 200, page size ~416.69 × 291.97 pt (147×103 mm)"""
    print("\n=== TEST 2: POST /api/overlay/generate (page_size='card', with_form=true) ===")
    
    payload = {
        "records": [{"fio": "Тест"}],
        "page_size": "card",
        "with_form": True
    }
    
    response = requests.post(f"{BACKEND_URL}/overlay/generate", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/pdf" in response.headers.get('Content-Type', ''), "Expected Content-Type application/pdf"
    
    # Check PDF validity
    pdf_bytes = response.content
    assert pdf_bytes.startswith(b'%PDF'), "PDF should start with %PDF signature"
    print(f"✓ Valid PDF signature: {pdf_bytes[:8]}")
    
    # Check page size using pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    page = doc[0]
    rect = page.rect
    width_pt = rect.width
    height_pt = rect.height
    doc.close()
    
    print(f"Page size: {width_pt:.2f} × {height_pt:.2f} pt")
    print(f"Expected: {CARD_WIDTH_PT:.2f} × {CARD_HEIGHT_PT:.2f} pt (tolerance ±{TOLERANCE_PT} pt)")
    
    width_diff = abs(width_pt - CARD_WIDTH_PT)
    height_diff = abs(height_pt - CARD_HEIGHT_PT)
    
    assert width_diff <= TOLERANCE_PT, f"Width {width_pt:.2f} pt differs from expected {CARD_WIDTH_PT:.2f} pt by {width_diff:.2f} pt (tolerance {TOLERANCE_PT} pt)"
    assert height_diff <= TOLERANCE_PT, f"Height {height_pt:.2f} pt differs from expected {CARD_HEIGHT_PT:.2f} pt by {height_diff:.2f} pt (tolerance {TOLERANCE_PT} pt)"
    
    print(f"✓ Page size is correct: {width_pt:.2f} × {height_pt:.2f} pt (147×103 mm)")
    print("✅ TEST 2 PASSED\n")
    return True


def test_overlay_generate_a4():
    """Test 3: POST /api/overlay/generate with page_size='a4', with_form=true
    Should return 200, page size ~595 × 842 pt (A4), NOT 147×103"""
    print("\n=== TEST 3: POST /api/overlay/generate (page_size='a4') ===")
    
    payload = {
        "records": [{"fio": "Тест"}],
        "page_size": "a4",
        "with_form": True
    }
    
    response = requests.post(f"{BACKEND_URL}/overlay/generate", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/pdf" in response.headers.get('Content-Type', ''), "Expected Content-Type application/pdf"
    
    # Check PDF validity
    pdf_bytes = response.content
    assert pdf_bytes.startswith(b'%PDF'), "PDF should start with %PDF signature"
    print(f"✓ Valid PDF signature: {pdf_bytes[:8]}")
    
    # Check page size using pymupdf
    doc = pymupdf.open(stream=pdf_bytes, filetype='pdf')
    page = doc[0]
    rect = page.rect
    width_pt = rect.width
    height_pt = rect.height
    doc.close()
    
    print(f"Page size: {width_pt:.2f} × {height_pt:.2f} pt")
    print(f"Expected: ~{A4_WIDTH_PT:.2f} × {A4_HEIGHT_PT:.2f} pt (A4)")
    
    # A4 should be significantly different from card size
    assert abs(width_pt - A4_WIDTH_PT) < 5, f"Width should be ~{A4_WIDTH_PT} pt (A4), got {width_pt:.2f} pt"
    assert abs(height_pt - A4_HEIGHT_PT) < 5, f"Height should be ~{A4_HEIGHT_PT} pt (A4), got {height_pt:.2f} pt"
    
    # Verify it's NOT card size
    assert abs(width_pt - CARD_WIDTH_PT) > 100, f"Page should NOT be card size (147×103 mm)"
    
    print(f"✓ Page size is A4: {width_pt:.2f} × {height_pt:.2f} pt, NOT 147×103 mm")
    print("✅ TEST 3 PASSED\n")
    return True


def test_overlay_print_silent_degradation():
    """Test 4: POST /api/overlay/print-silent with page_size='card'
    Should return 400 (Bad Request) on Linux with message about Windows app"""
    print("\n=== TEST 4: POST /api/overlay/print-silent (Linux degradation) ===")
    
    payload = {
        "records": [{"fio": "Тест"}],
        "page_size": "card"
    }
    
    response = requests.post(f"{BACKEND_URL}/overlay/print-silent", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    assert response.status_code == 400, f"Expected 400 (Bad Request) on Linux, got {response.status_code}"
    
    # Check response is JSON
    assert "application/json" in response.headers.get('Content-Type', ''), "Expected Content-Type application/json"
    
    # Check error message mentions Windows
    response_json = response.json()
    print(f"Response: {response_json}")
    
    detail = response_json.get('detail', '')
    assert 'Windows' in detail or 'установленном' in detail, f"Error message should mention Windows app: {detail}"
    
    print(f"✓ Correct error message: {detail}")
    print("✅ TEST 4 PASSED (graceful degradation on Linux)\n")
    return True


def test_printers_endpoint():
    """Test 5: GET /api/printers
    Should return 200 JSON {"supported": false, "printers": []} on Linux"""
    print("\n=== TEST 5: GET /api/printers (Linux) ===")
    
    response = requests.get(f"{BACKEND_URL}/printers")
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/json" in response.headers.get('Content-Type', ''), "Expected Content-Type application/json"
    
    data = response.json()
    print(f"Response: {data}")
    
    assert "supported" in data, "Response should contain 'supported' key"
    assert "printers" in data, "Response should contain 'printers' key"
    
    assert data["supported"] == False, f"On Linux, supported should be false, got {data['supported']}"
    assert isinstance(data["printers"], list), "printers should be a list"
    assert len(data["printers"]) == 0, f"On Linux, printers list should be empty, got {len(data['printers'])} items"
    
    print("✓ Correct response: supported=false, printers=[]")
    print("✅ TEST 5 PASSED\n")
    return True


def test_regression_form_background():
    """Test 6 (REGRESSION): GET /api/overlay/form-background
    Should return 200 image/png (valid PNG \\x89PNG)"""
    print("\n=== TEST 6 (REGRESSION): GET /api/overlay/form-background ===")
    
    response = requests.get(f"{BACKEND_URL}/overlay/form-background")
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "image/png" in response.headers.get('Content-Type', ''), "Expected Content-Type image/png"
    
    # Check PNG signature
    png_bytes = response.content
    assert png_bytes.startswith(b'\x89PNG'), "PNG should start with \\x89PNG signature"
    
    print(f"✓ Valid PNG signature: {png_bytes[:8]}")
    print(f"✓ PNG size: {len(png_bytes)} bytes")
    print("✅ TEST 6 PASSED\n")
    return True


def test_regression_overlay_layout():
    """Test 7 (REGRESSION): GET /api/overlay/layout
    Should return 200 JSON"""
    print("\n=== TEST 7 (REGRESSION): GET /api/overlay/layout ===")
    
    response = requests.get(f"{BACKEND_URL}/overlay/layout")
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/json" in response.headers.get('Content-Type', ''), "Expected Content-Type application/json"
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    assert "layout" in data, "Response should contain 'layout' key"
    assert "dx_mm" in data, "Response should contain 'dx_mm' key"
    assert "dy_mm" in data, "Response should contain 'dy_mm' key"
    assert "page_mm" in data, "Response should contain 'page_mm' key"
    
    print(f"✓ Layout contains {len(data['layout'])} fields")
    print(f"✓ page_mm: {data['page_mm']}")
    print("✅ TEST 7 PASSED\n")
    return True


def test_regression_stats():
    """Test 8 (REGRESSION): GET /api/stats
    Should return 200 JSON"""
    print("\n=== TEST 8 (REGRESSION): GET /api/stats ===")
    
    response = requests.get(f"{BACKEND_URL}/stats")
    
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "application/json" in response.headers.get('Content-Type', ''), "Expected Content-Type application/json"
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    assert "total" in data, "Response should contain 'total' key"
    assert "drafts" in data, "Response should contain 'drafts' key"
    assert "this_month" in data, "Response should contain 'this_month' key"
    assert "datasets" in data, "Response should contain 'datasets' key"
    assert "recent" in data, "Response should contain 'recent' key"
    
    print(f"✓ Stats: total={data['total']}, drafts={data['drafts']}, this_month={data['this_month']}")
    print("✅ TEST 8 PASSED\n")
    return True


def main():
    """Run all tests"""
    print("=" * 80)
    print("BACKEND TESTING: Overlay Printing with Exact Page Size Verification")
    print("Testing 147×103 mm (card) page size and Linux degradation")
    print("=" * 80)
    
    tests = [
        ("Test 1: overlay/generate card without form", test_overlay_generate_card_without_form),
        ("Test 2: overlay/generate card with form", test_overlay_generate_card_with_form),
        ("Test 3: overlay/generate A4", test_overlay_generate_a4),
        ("Test 4: overlay/print-silent degradation", test_overlay_print_silent_degradation),
        ("Test 5: printers endpoint", test_printers_endpoint),
        ("Test 6 (REGRESSION): form-background", test_regression_form_background),
        ("Test 7 (REGRESSION): overlay/layout", test_regression_overlay_layout),
        ("Test 8 (REGRESSION): stats", test_regression_stats),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            error_msg = f"❌ {test_name} FAILED: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
        except Exception as e:
            failed += 1
            error_msg = f"❌ {test_name} ERROR: {str(e)}"
            print(error_msg)
            errors.append(error_msg)
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    if errors:
        print("\nFAILURES:")
        for error in errors:
            print(f"  {error}")
    
    print("=" * 80)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"⚠️  {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
