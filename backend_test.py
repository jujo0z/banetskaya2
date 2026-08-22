#!/usr/bin/env python3
"""Backend API testing for overlay printing with rotate, mode=full, and preview-png."""
import sys
import requests
import pymupdf  # fitz
from io import BytesIO

# Base URL from frontend/.env
BASE_URL = "https://df5d1aab-d151-43c7-81f6-15cafa62422e.preview.emergentagent.com/api"

# Tolerance for page size checks (±1.5 pt)
TOLERANCE = 1.5

def check_page_size(pdf_bytes, expected_width, expected_height, page_index=0):
    """Check if a PDF page has the expected dimensions within tolerance."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    if len(doc) <= page_index:
        doc.close()
        return False, f"PDF has only {len(doc)} pages, cannot check page {page_index}"
    
    page = doc[page_index]
    rect = page.rect
    actual_w = rect.width
    actual_h = rect.height
    doc.close()
    
    w_ok = abs(actual_w - expected_width) <= TOLERANCE
    h_ok = abs(actual_h - expected_height) <= TOLERANCE
    
    if w_ok and h_ok:
        return True, f"Page size OK: {actual_w:.2f}×{actual_h:.2f} pt (expected {expected_width}×{expected_height})"
    else:
        return False, f"Page size MISMATCH: {actual_w:.2f}×{actual_h:.2f} pt (expected {expected_width}×{expected_height}, tolerance ±{TOLERANCE})"

def count_pages(pdf_bytes):
    """Count the number of pages in a PDF."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    count = len(doc)
    doc.close()
    return count

def test_rotate_90():
    """Test 1: POST /api/overlay/generate with rotate=90 -> page size 291.97×416.69 pt (103×147 mm portrait)."""
    print("\n=== Test 1: rotate=90 (103×147 mm portrait) ===")
    payload = {
        "records": [{"fio": "Тест Поворот 90"}],
        "page_size": "card",
        "rotate": 90
    }
    resp = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        return False
    
    if resp.headers.get("Content-Type") != "application/pdf":
        print(f"❌ FAIL: Expected application/pdf, got {resp.headers.get('Content-Type')}")
        return False
    
    pdf_bytes = resp.content
    if not pdf_bytes.startswith(b"%PDF"):
        print(f"❌ FAIL: Response does not start with %PDF")
        return False
    
    # rotate=90 should swap dimensions: 103×147 mm = 291.97×416.69 pt
    ok, msg = check_page_size(pdf_bytes, 291.97, 416.69)
    if ok:
        print(f"✅ PASS: {msg}")
        return True
    else:
        print(f"❌ FAIL: {msg}")
        return False

def test_rotate_0():
    """Test 1b: rotate=0 -> 416.69×291.97 pt (147×103 mm landscape)."""
    print("\n=== Test 1b: rotate=0 (147×103 mm landscape) ===")
    payload = {
        "records": [{"fio": "Тест Поворот 0"}],
        "page_size": "card",
        "rotate": 0
    }
    resp = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    pdf_bytes = resp.content
    ok, msg = check_page_size(pdf_bytes, 416.69, 291.97)
    if ok:
        print(f"✅ PASS: {msg}")
        return True
    else:
        print(f"❌ FAIL: {msg}")
        return False

def test_rotate_270():
    """Test 1c: rotate=270 -> 291.97×416.69 pt (103×147 mm portrait)."""
    print("\n=== Test 1c: rotate=270 (103×147 mm portrait) ===")
    payload = {
        "records": [{"fio": "Тест Поворот 270"}],
        "page_size": "card",
        "rotate": 270
    }
    resp = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    pdf_bytes = resp.content
    ok, msg = check_page_size(pdf_bytes, 291.97, 416.69)
    if ok:
        print(f"✅ PASS: {msg}")
        return True
    else:
        print(f"❌ FAIL: {msg}")
        return False

def test_rotate_180():
    """Test 1d: rotate=180 -> 416.69×291.97 pt (147×103 mm landscape)."""
    print("\n=== Test 1d: rotate=180 (147×103 mm landscape) ===")
    payload = {
        "records": [{"fio": "Тест Поворот 180"}],
        "page_size": "card",
        "rotate": 180
    }
    resp = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    pdf_bytes = resp.content
    ok, msg = check_page_size(pdf_bytes, 416.69, 291.97)
    if ok:
        print(f"✅ PASS: {msg}")
        return True
    else:
        print(f"❌ FAIL: {msg}")
        return False

def test_mode_full_landscape():
    """Test 2: mode='full', orientation='landscape' -> A4 landscape 841.89×595.28 pt, ceil(3/4)=1 sheet."""
    print("\n=== Test 2: mode='full', orientation='landscape' (3 records) ===")
    payload = {
        "records": [
            {"fio": "Запись A"},
            {"fio": "Запись B"},
            {"fio": "Запись C"}
        ],
        "mode": "full",
        "orientation": "landscape"
    }
    resp = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        return False
    
    if resp.headers.get("Content-Type") != "application/pdf":
        print(f"❌ FAIL: Expected application/pdf, got {resp.headers.get('Content-Type')}")
        return False
    
    pdf_bytes = resp.content
    
    # Check page size: A4 landscape = 841.89×595.28 pt
    ok, msg = check_page_size(pdf_bytes, 841.89, 595.28)
    if not ok:
        print(f"❌ FAIL: {msg}")
        return False
    
    # Check page count: 3 records, landscape = 4 per sheet, so ceil(3/4) = 1 sheet
    page_count = count_pages(pdf_bytes)
    if page_count != 1:
        print(f"❌ FAIL: Expected 1 sheet, got {page_count}")
        return False
    
    print(f"✅ PASS: A4 landscape, 1 sheet for 3 records")
    return True

def test_mode_full_portrait():
    """Test 3: mode='full', orientation='portrait' -> A4 portrait 595.28×841.89 pt, ceil(3/2)=2 sheets."""
    print("\n=== Test 3: mode='full', orientation='portrait' (3 records) ===")
    payload = {
        "records": [
            {"fio": "Запись A"},
            {"fio": "Запись B"},
            {"fio": "Запись C"}
        ],
        "mode": "full",
        "orientation": "portrait"
    }
    resp = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    pdf_bytes = resp.content
    
    # Check page size: A4 portrait = 595.28×841.89 pt
    ok, msg = check_page_size(pdf_bytes, 595.28, 841.89)
    if not ok:
        print(f"❌ FAIL: {msg}")
        return False
    
    # Check page count: 3 records, portrait = 2 per sheet, so ceil(3/2) = 2 sheets
    page_count = count_pages(pdf_bytes)
    if page_count != 2:
        print(f"❌ FAIL: Expected 2 sheets, got {page_count}")
        return False
    
    print(f"✅ PASS: A4 portrait, 2 sheets for 3 records")
    return True

def test_mode_full_per_sheet():
    """Test 4: mode='full', per_sheet=2, orientation='landscape', 5 records -> ceil(5/2)=3 sheets."""
    print("\n=== Test 4: mode='full', per_sheet=2, orientation='landscape' (5 records) ===")
    payload = {
        "records": [
            {"fio": "Запись 1"},
            {"fio": "Запись 2"},
            {"fio": "Запись 3"},
            {"fio": "Запись 4"},
            {"fio": "Запись 5"}
        ],
        "mode": "full",
        "orientation": "landscape",
        "per_sheet": 2
    }
    resp = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    pdf_bytes = resp.content
    
    # Check page count: 5 records, per_sheet=2, so ceil(5/2) = 3 sheets
    page_count = count_pages(pdf_bytes)
    if page_count != 3:
        print(f"❌ FAIL: Expected 3 sheets, got {page_count}")
        return False
    
    print(f"✅ PASS: 3 sheets for 5 records with per_sheet=2")
    return True

def test_preview_png():
    """Test 5: POST /api/overlay/preview-png -> 200, image/png, starts with \\x89PNG."""
    print("\n=== Test 5: POST /api/overlay/preview-png ===")
    payload = {
        "records": [
            {"fio": "Запись A"},
            {"fio": "Запись B"}
        ],
        "mode": "full",
        "orientation": "landscape"
    }
    resp = requests.post(f"{BASE_URL}/overlay/preview-png", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        return False
    
    if resp.headers.get("Content-Type") != "image/png":
        print(f"❌ FAIL: Expected image/png, got {resp.headers.get('Content-Type')}")
        return False
    
    png_bytes = resp.content
    if not png_bytes.startswith(b"\x89PNG"):
        print(f"❌ FAIL: Response does not start with \\x89PNG")
        return False
    
    if len(png_bytes) < 1000:
        print(f"❌ FAIL: PNG size too small: {len(png_bytes)} bytes")
        return False
    
    print(f"✅ PASS: Valid PNG, size {len(png_bytes)} bytes")
    return True

def test_test_sheet_rotate():
    """Test 6: GET /api/overlay/test-sheet?rotate=90 -> 200, page size 291.97×416.69 pt."""
    print("\n=== Test 6: GET /api/overlay/test-sheet?rotate=90 ===")
    resp = requests.get(f"{BASE_URL}/overlay/test-sheet?rotate=90", timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    if resp.headers.get("Content-Type") != "application/pdf":
        print(f"❌ FAIL: Expected application/pdf, got {resp.headers.get('Content-Type')}")
        return False
    
    pdf_bytes = resp.content
    ok, msg = check_page_size(pdf_bytes, 291.97, 416.69)
    if ok:
        print(f"✅ PASS: {msg}")
        return True
    else:
        print(f"❌ FAIL: {msg}")
        return False

def test_layout_rotate_save():
    """Test 7: POST /api/overlay/layout with rotate=90, then GET to verify it's saved."""
    print("\n=== Test 7: POST /api/overlay/layout with rotate=90 ===")
    
    # First, get the current layout to use as a base
    resp = requests.get(f"{BASE_URL}/overlay/layout", timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Could not get current layout: {resp.status_code}")
        return False
    
    current = resp.json()
    layout = current.get("layout", [])
    
    # Save with rotate=90
    payload = {
        "layout": layout,
        "dx_mm": 1.0,
        "dy_mm": 2.0,
        "rotate": 90
    }
    resp = requests.post(f"{BASE_URL}/overlay/layout", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: POST failed with {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        return False
    
    data = resp.json()
    if not data.get("saved"):
        print(f"❌ FAIL: Response does not indicate saved=true")
        return False
    
    if data.get("rotate") != 90:
        print(f"❌ FAIL: Response rotate={data.get('rotate')}, expected 90")
        return False
    
    # Now GET to verify persistence
    resp = requests.get(f"{BASE_URL}/overlay/layout", timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: GET after POST failed with {resp.status_code}")
        return False
    
    data = resp.json()
    if data.get("rotate") != 90:
        print(f"❌ FAIL: GET returned rotate={data.get('rotate')}, expected 90")
        return False
    
    print(f"✅ PASS: rotate=90 saved and retrieved correctly")
    return True

def test_regression_card_no_rotate():
    """Test 8a: Regression - POST /api/overlay/generate page_size='card' without rotate -> 416.69×291.97 pt."""
    print("\n=== Test 8a: Regression - card without rotate ===")
    payload = {
        "records": [{"fio": "Тест Регрессия"}],
        "page_size": "card"
    }
    resp = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    pdf_bytes = resp.content
    ok, msg = check_page_size(pdf_bytes, 416.69, 291.97)
    if ok:
        print(f"✅ PASS: {msg}")
        return True
    else:
        print(f"❌ FAIL: {msg}")
        return False

def test_regression_print_silent():
    """Test 8b: Regression - POST /api/overlay/print-silent on Linux -> 400."""
    print("\n=== Test 8b: Regression - print-silent on Linux ===")
    payload = {
        "records": [{"fio": "Тест"}],
        "page_size": "card"
    }
    resp = requests.post(f"{BASE_URL}/overlay/print-silent", json=payload, timeout=30)
    if resp.status_code != 400:
        print(f"❌ FAIL: Expected 400 (graceful degradation on Linux), got {resp.status_code}")
        return False
    
    print(f"✅ PASS: print-silent returns 400 on Linux (expected)")
    return True

def main():
    print("=" * 70)
    print("BACKEND TESTING: Overlay Printing with Rotate, Mode=Full, Preview-PNG")
    print("=" * 70)
    
    tests = [
        ("Test 1: rotate=90", test_rotate_90),
        ("Test 1b: rotate=0", test_rotate_0),
        ("Test 1c: rotate=270", test_rotate_270),
        ("Test 1d: rotate=180", test_rotate_180),
        ("Test 2: mode=full landscape", test_mode_full_landscape),
        ("Test 3: mode=full portrait", test_mode_full_portrait),
        ("Test 4: mode=full per_sheet", test_mode_full_per_sheet),
        ("Test 5: preview-png", test_preview_png),
        ("Test 6: test-sheet rotate", test_test_sheet_rotate),
        ("Test 7: layout rotate save", test_layout_rotate_save),
        ("Test 8a: regression card", test_regression_card_no_rotate),
        ("Test 8b: regression print-silent", test_regression_print_silent),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({100*passed//total}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
