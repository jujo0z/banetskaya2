#!/usr/bin/env python3
"""
Backend testing for Zayavlenie endpoints after redesign.
Tests the NEW A4-PORTRAIT design with 2 pages per person.
"""
import requests
import pymupdf
import io
import hashlib
import os
from openpyxl import load_workbook
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://form-portal-15.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_1_layout_get():
    """Test 1: GET /api/zayavlenie/layout → 200, check structure"""
    print("\n=== TEST 1: GET /api/zayavlenie/layout ===")
    
    resp = requests.get(f"{API_BASE}/zayavlenie/layout")
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check required keys
    assert "layout" in data, "Missing 'layout' key"
    assert "slots" in data, "Missing 'slots' key"
    assert "page_count" in data, "Missing 'page_count' key"
    
    layout = data["layout"]
    slots = data["slots"]
    page_count = data["page_count"]
    
    print(f"Page count: {page_count}")
    assert page_count == 2, f"Expected page_count=2, got {page_count}"
    
    # Check layout['1'] has ≥19 slots
    assert "1" in layout, "Missing layout['1']"
    page1_slots = layout["1"]
    print(f"Page 1 slots count: {len(page1_slots)}")
    assert len(page1_slots) >= 19, f"Expected ≥19 slots in page 1, got {len(page1_slots)}"
    
    # Check required slots in page 1
    required_page1 = ["applicant", "passport_series", "passport_number", "res_street", "basis", "sign_day"]
    for slot in required_page1:
        assert slot in page1_slots, f"Missing required slot '{slot}' in page 1"
    print(f"✓ Page 1 contains all required slots: {required_page1}")
    
    # Check layout['2'] has required slots
    assert "2" in layout, "Missing layout['2']"
    page2_slots = layout["2"]
    print(f"Page 2 slots count: {len(page2_slots)}")
    
    required_page2 = ["area", "occupancy_count", "minors_count"]
    for slot in required_page2:
        assert slot in page2_slots, f"Missing required slot '{slot}' in page 2"
    print(f"✓ Page 2 contains all required slots: {required_page2}")
    
    # Check slots array structure
    assert isinstance(slots, list), "slots should be an array"
    print(f"Slots array length: {len(slots)}")
    
    for s in slots:
        assert "slot" in s, f"Slot missing 'slot' key: {s}"
        assert "page" in s, f"Slot missing 'page' key: {s}"
        assert "label" in s, f"Slot missing 'label' key: {s}"
    
    print("✅ TEST 1 PASSED")
    return layout

def test_2_layout_save_and_merge(original_layout):
    """Test 2: POST /api/zayavlenie/layout with partial update, verify merge"""
    print("\n=== TEST 2: POST /api/zayavlenie/layout (save & merge) ===")
    
    # Save a partial layout update
    payload = {
        "layout": {
            "1": {
                "applicant": {
                    "x": 31.0,
                    "y": 11.0,
                    "w": 65,
                    "align": "center",
                    "size": 10,
                    "bold": False
                }
            }
        }
    }
    
    resp = requests.post(f"{API_BASE}/zayavlenie/layout", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    data = resp.json()
    assert data.get("saved") == True, "Expected saved=true"
    print("✓ Layout saved successfully")
    
    # Verify the change persisted
    resp2 = requests.get(f"{API_BASE}/zayavlenie/layout")
    assert resp2.status_code == 200
    data2 = resp2.json()
    
    applicant_cfg = data2["layout"]["1"]["applicant"]
    print(f"Applicant config after save: {applicant_cfg}")
    
    assert applicant_cfg["x"] == 31.0, f"Expected x=31.0, got {applicant_cfg['x']}"
    print("✓ Custom applicant.x=31.0 persisted")
    
    # Verify other slots are still present (merge, not overwrite)
    page1_slots = data2["layout"]["1"]
    assert "passport_series" in page1_slots, "passport_series should still be present after merge"
    assert "basis" in page1_slots, "basis should still be present after merge"
    print(f"✓ Other slots still present (count: {len(page1_slots)})")
    
    # IMPORTANT: Restore to defaults
    print("\n--- Restoring layout to defaults ---")
    restore_payload = {"layout": {}}
    resp3 = requests.post(f"{API_BASE}/zayavlenie/layout", json=restore_payload)
    assert resp3.status_code == 200
    print("✓ Layout restored to defaults")
    
    print("✅ TEST 2 PASSED")

def test_3_background_images():
    """Test 3: GET /api/zayavlenie/background?page=1 and page=2"""
    print("\n=== TEST 3: GET /api/zayavlenie/background ===")
    
    # Page 1
    resp1 = requests.get(f"{API_BASE}/zayavlenie/background?page=1")
    print(f"Page 1 status: {resp1.status_code}")
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"
    assert resp1.headers.get("Content-Type") == "image/png", f"Expected image/png, got {resp1.headers.get('Content-Type')}"
    
    png1 = resp1.content
    assert png1[:4] == b'\x89PNG', "Page 1 should start with PNG signature"
    assert len(png1) > 5000, f"Page 1 size should be > 5000 bytes, got {len(png1)}"
    print(f"✓ Page 1: valid PNG, size={len(png1)} bytes")
    
    # Page 2
    resp2 = requests.get(f"{API_BASE}/zayavlenie/background?page=2")
    print(f"Page 2 status: {resp2.status_code}")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
    assert resp2.headers.get("Content-Type") == "image/png", f"Expected image/png, got {resp2.headers.get('Content-Type')}"
    
    png2 = resp2.content
    assert png2[:4] == b'\x89PNG', "Page 2 should start with PNG signature"
    assert len(png2) > 5000, f"Page 2 size should be > 5000 bytes, got {len(png2)}"
    print(f"✓ Page 2: valid PNG, size={len(png2)} bytes")
    
    # Verify they are different images
    hash1 = hashlib.md5(png1).hexdigest()
    hash2 = hashlib.md5(png2).hexdigest()
    assert hash1 != hash2, "Page 1 and Page 2 should be different images"
    print(f"✓ Page 1 and Page 2 are different images (hash1={hash1[:8]}, hash2={hash2[:8]})")
    
    print("✅ TEST 3 PASSED")

def test_4_preview_pdf():
    """Test 4: POST /api/zayavlenie/preview with 1 record"""
    print("\n=== TEST 4: POST /api/zayavlenie/preview (PDF) ===")
    
    payload = {
        "records": [{
            "fio": "Иванов Иван Иванович",
            "birth_year": "2006",
            "passport_series": "MP",
            "passport_number": "1234567",
            "res_street": "пр-т Дзержинского",
            "res_house": "85",
            "from_place": "г. Гомель",
            "basis": "договор найма № 12 от 01.09.2024",
            "sign_date": "01.09.2024",
            "area": "5467,9",
            "occupancy_count": "250",
            "minors_count": "3"
        }]
    }
    
    resp = requests.post(f"{API_BASE}/zayavlenie/preview", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers.get("Content-Type") == "application/pdf", f"Expected application/pdf, got {resp.headers.get('Content-Type')}"
    
    pdf_data = resp.content
    assert pdf_data[:4] == b'%PDF', "PDF should start with %PDF"
    print(f"✓ Valid PDF, size={len(pdf_data)} bytes")
    
    # Check with pymupdf
    doc = pymupdf.open(stream=pdf_data, filetype="pdf")
    page_count = len(doc)
    print(f"Page count: {page_count}")
    assert page_count == 2, f"Expected EXACTLY 2 pages, got {page_count}"
    
    # Check page 0 (front) dimensions - A4 PORTRAIT
    page0 = doc[0]
    rect0 = page0.rect
    width0 = rect0.width
    height0 = rect0.height
    print(f"Page 0 dimensions: {width0:.2f} × {height0:.2f} pt")
    
    # A4 portrait: 595.28 × 841.89 pt (allow ±2pt tolerance)
    assert abs(width0 - 595.28) <= 2, f"Page 0 width should be ≈595.28pt, got {width0:.2f}"
    assert abs(height0 - 841.89) <= 2, f"Page 0 height should be ≈841.89pt, got {height0:.2f}"
    print("✓ Page 0 is A4-PORTRAIT (595.28×841.89 pt)")
    
    # Check page 1 (back) dimensions
    page1 = doc[1]
    rect1 = page1.rect
    width1 = rect1.width
    height1 = rect1.height
    print(f"Page 1 dimensions: {width1:.2f} × {height1:.2f} pt")
    assert abs(width1 - 595.28) <= 2, f"Page 1 width should be ≈595.28pt, got {width1:.2f}"
    assert abs(height1 - 841.89) <= 2, f"Page 1 height should be ≈841.89pt, got {height1:.2f}"
    print("✓ Page 1 is A4-PORTRAIT (595.28×841.89 pt)")
    
    # Extract text from page 0 and check for required substrings
    text0 = page0.get_text()
    print(f"\n--- Page 0 text excerpt (first 500 chars) ---")
    print(text0[:500])
    
    required_page0 = [
        'ЗАЯВЛЕНИЕ',
        'по месту пребывания',  # NOT "жительства"
        'Иванов Иван Иванович',
        'пр-т Дзержинского'
    ]
    
    for substring in required_page0:
        assert substring in text0, f"Page 0 should contain '{substring}'"
        print(f"✓ Found '{substring}' in page 0")
    
    # Extract text from page 1 and check for required substrings
    text1 = page1.get_text()
    print(f"\n--- Page 1 text excerpt (first 500 chars) ---")
    print(text1[:500])
    
    required_page1 = [
        'Общая площадь',
        '5467,9'
    ]
    
    for substring in required_page1:
        assert substring in text1, f"Page 1 should contain '{substring}'"
        print(f"✓ Found '{substring}' in page 1")
    
    doc.close()
    print("✅ TEST 4 PASSED")

def test_5_preview_png():
    """Test 5: POST /api/zayavlenie/preview-png with side=front and side=back"""
    print("\n=== TEST 5: POST /api/zayavlenie/preview-png ===")
    
    payload = {
        "records": [{
            "fio": "Иванов Иван Иванович",
            "birth_year": "2006",
            "passport_series": "MP",
            "passport_number": "1234567",
            "res_street": "пр-т Дзержинского",
            "res_house": "85",
            "from_place": "г. Гомель",
            "basis": "договор найма № 12 от 01.09.2024",
            "sign_date": "01.09.2024",
            "area": "5467,9",
            "occupancy_count": "250",
            "minors_count": "3"
        }],
        "side": "front"
    }
    
    # Test front
    resp_front = requests.post(f"{API_BASE}/zayavlenie/preview-png", json=payload)
    print(f"Front status: {resp_front.status_code}")
    assert resp_front.status_code == 200, f"Expected 200, got {resp_front.status_code}"
    assert resp_front.headers.get("Content-Type") == "image/png"
    
    png_front = resp_front.content
    assert png_front[:4] == b'\x89PNG', "Front should be valid PNG"
    print(f"✓ Front: valid PNG, size={len(png_front)} bytes")
    
    # Test back
    payload["side"] = "back"
    resp_back = requests.post(f"{API_BASE}/zayavlenie/preview-png", json=payload)
    print(f"Back status: {resp_back.status_code}")
    assert resp_back.status_code == 200, f"Expected 200, got {resp_back.status_code}"
    assert resp_back.headers.get("Content-Type") == "image/png"
    
    png_back = resp_back.content
    assert png_back[:4] == b'\x89PNG', "Back should be valid PNG"
    print(f"✓ Back: valid PNG, size={len(png_back)} bytes")
    
    # Verify they are different
    assert png_front != png_back, "Front and back should be different images"
    print(f"✓ Front and back are different images")
    
    print("✅ TEST 5 PASSED")

def test_6_prefill():
    """Test 6: POST /api/zayavlenie/prefill"""
    print("\n=== TEST 6: POST /api/zayavlenie/prefill ===")
    
    payload = {
        "students": [{
            "full_name": "Иванов Иван Иванович",
            "birth_date": "01.09.2007",
            "citizenship": "РБ",
            "passport_number": "MP1234567"
        }]
    }
    
    resp = requests.post(f"{API_BASE}/zayavlenie/prefill", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    data = resp.json()
    assert "records" in data, "Response should contain 'records'"
    records = data["records"]
    assert isinstance(records, list), "records should be an array"
    assert len(records) > 0, "records should not be empty"
    
    print(f"✓ Returned {len(records)} record(s)")
    print(f"First record: {records[0]}")
    
    print("✅ TEST 6 PASSED")

def test_7_regression_package():
    """Test 7: Regression - master-template, master-upload, package"""
    print("\n=== TEST 7: REGRESSION - Package flow ===")
    
    # Get master template
    print("\n--- Step 1: GET /api/master-template ---")
    resp = requests.get(f"{API_BASE}/master-template")
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in resp.headers.get("Content-Type", "")
    
    xlsx_data = resp.content
    print(f"✓ Downloaded template, size={len(xlsx_data)} bytes")
    
    # Fill the template
    print("\n--- Step 2: Fill template with openpyxl ---")
    wb = load_workbook(io.BytesIO(xlsx_data))
    ws = wb.active
    
    # Find header row (usually row 2)
    headers = {}
    for col_idx, cell in enumerate(ws[2], start=1):
        if cell.value:
            headers[cell.value] = col_idx
    
    print(f"Found {len(headers)} headers")
    
    # Fill row 3 with test data
    row_idx = 3
    test_data = {
        "ФИО": "Иванов Иван Иванович",
        "Дата рождения": datetime(2006, 8, 3),
        "Гражданство": "Республика Беларусь",
        "Номер паспорта": "MP1234567",
        "Дата выдачи": datetime(2020, 1, 10),
        "Срок действия": datetime(2030, 1, 10),
        "Кем выдан": "РОВД Минска",
        "Номер договора": "TEST-001",
        "Дата подписания": datetime(2024, 9, 1),
        "Номер комнаты": "101",
        "Адрес регистрации": "г. Минск, ул. Тестовая, д. 1",
        "Телефон": "+375291234567"
    }
    
    for header, value in test_data.items():
        if header in headers:
            col_idx = headers[header]
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Save to bytes
    filled_xlsx = io.BytesIO()
    wb.save(filled_xlsx)
    filled_xlsx.seek(0)
    print("✓ Template filled with test data")
    
    # Upload
    print("\n--- Step 3: POST /api/master-upload ---")
    files = {"file": ("test_data.xlsx", filled_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    resp2 = requests.post(f"{API_BASE}/master-upload", files=files)
    print(f"Status: {resp2.status_code}")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
    
    upload_data = resp2.json()
    print(f"Upload response keys: {list(upload_data.keys())}")
    
    assert "zayavlenie" in upload_data, "Response should contain 'zayavlenie' key"
    zayavlenie_records = upload_data["zayavlenie"]
    assert isinstance(zayavlenie_records, list), "zayavlenie should be an array"
    assert len(zayavlenie_records) > 0, "zayavlenie should not be empty"
    print(f"✓ zayavlenie key present with {len(zayavlenie_records)} record(s)")
    
    # Get master data for package
    masters = upload_data.get("masters", [])
    if not masters:
        print("⚠ No masters in response, using upload_data directly")
        masters = [upload_data]
    
    # Test package
    print("\n--- Step 4: POST /api/package ---")
    package_payload = {
        "people": [masters[0]],
        "include": {
            "zayavlenie": True
        }
    }
    
    resp3 = requests.post(f"{API_BASE}/package", json=package_payload)
    print(f"Status: {resp3.status_code}")
    assert resp3.status_code == 200, f"Expected 200, got {resp3.status_code}"
    assert resp3.headers.get("Content-Type") == "application/pdf"
    
    package_pdf = resp3.content
    assert package_pdf[:4] == b'%PDF', "Package should be valid PDF"
    print(f"✓ Package PDF generated, size={len(package_pdf)} bytes")
    
    # Check page count
    doc = pymupdf.open(stream=package_pdf, filetype="pdf")
    page_count = len(doc)
    print(f"Package page count: {page_count}")
    assert page_count > 0, "Package should have at least 1 page"
    doc.close()
    
    print("✅ TEST 7 PASSED")

def test_8_health_regression():
    """Test 8: Health regression - _ping and stats"""
    print("\n=== TEST 8: HEALTH REGRESSION ===")
    
    # Test _ping
    print("\n--- GET /api/_ping ---")
    resp1 = requests.get(f"{API_BASE}/_ping")
    print(f"Status: {resp1.status_code}")
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"
    
    data1 = resp1.json()
    assert data1.get("ok") == True, f"Expected ok=true, got {data1}"
    print("✓ _ping returned ok=true")
    
    # Test stats
    print("\n--- GET /api/stats ---")
    resp2 = requests.get(f"{API_BASE}/stats")
    print(f"Status: {resp2.status_code}")
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
    
    data2 = resp2.json()
    print(f"Stats keys: {list(data2.keys())}")
    assert "total" in data2, "Stats should contain 'total'"
    assert "drafts" in data2, "Stats should contain 'drafts'"
    print("✓ Stats endpoint working")
    
    print("✅ TEST 8 PASSED")

def main():
    """Run all tests"""
    print("=" * 80)
    print("BACKEND TESTING: Zayavlenie Endpoints (Redesigned A4-PORTRAIT)")
    print("=" * 80)
    print(f"Backend URL: {API_BASE}")
    
    try:
        # Test 1: GET layout
        original_layout = test_1_layout_get()
        
        # Test 2: POST layout (save & merge)
        test_2_layout_save_and_merge(original_layout)
        
        # Test 3: Background images
        test_3_background_images()
        
        # Test 4: Preview PDF
        test_4_preview_pdf()
        
        # Test 5: Preview PNG
        test_5_preview_png()
        
        # Test 6: Prefill
        test_6_prefill()
        
        # Test 7: Regression - package
        test_7_regression_package()
        
        # Test 8: Health regression
        test_8_health_regression()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED (8/8)")
        print("=" * 80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
