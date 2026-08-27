#!/usr/bin/env python3
"""
Backend testing for NEW /api/zayavlenie/* features:
1. Saving list of records (persist)
2. Underline in PDF doesn't break generation
3. Regression tests

Based on review_request in Russian.
"""
import requests
import pymupdf
import io
import sys

# Backend URL from frontend/.env
BASE_URL = "https://form-portal-15.preview.emergentagent.com/api"

def test_1_save_records_persist():
    """
    TEST 1: Saving list of records (persist)
    a. POST /api/zayavlenie/records {"records":[{"fio":"A","__print":true},{"fio":"B","__print":false}]}
       → 200, saved==true, count==2
    b. GET /api/zayavlenie/records → {"records":[...]} exactly 2 records, __print field preserved (true and false)
    c. POST /api/zayavlenie/records {"records":[]} → 200, count==0
       GET → records == [] (empty)
    """
    print("\n=== TEST 1: Saving list of records (persist) ===")
    
    # Step a: POST records with 2 items
    print("\nStep 1a: POST /api/zayavlenie/records (2 records)")
    payload = {
        "records": [
            {"fio": "A", "__print": True},
            {"fio": "B", "__print": False}
        ]
    }
    
    resp = requests.post(f"{BASE_URL}/zayavlenie/records", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    if not data.get("saved"):
        print(f"❌ FAIL: saved should be true, got {data.get('saved')}")
        return False
    
    if data.get("count") != 2:
        print(f"❌ FAIL: count should be 2, got {data.get('count')}")
        return False
    
    print("✅ Step 1a PASS")
    
    # Step b: GET records (should return 2 records with __print preserved)
    print("\nStep 1b: GET /api/zayavlenie/records (verify persist)")
    resp = requests.get(f"{BASE_URL}/zayavlenie/records")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    if "records" not in data:
        print(f"❌ FAIL: Missing 'records' key")
        return False
    
    records = data["records"]
    if not isinstance(records, list):
        print(f"❌ FAIL: records should be a list, got {type(records)}")
        return False
    
    if len(records) != 2:
        print(f"❌ FAIL: Expected exactly 2 records, got {len(records)}")
        return False
    
    # Check __print field is preserved
    print(f"Record 0: {records[0]}")
    print(f"Record 1: {records[1]}")
    
    # Find records by fio
    record_a = next((r for r in records if r.get("fio") == "A"), None)
    record_b = next((r for r in records if r.get("fio") == "B"), None)
    
    if not record_a:
        print(f"❌ FAIL: Could not find record with fio='A'")
        return False
    
    if not record_b:
        print(f"❌ FAIL: Could not find record with fio='B'")
        return False
    
    if record_a.get("__print") != True:
        print(f"❌ FAIL: Record A __print should be true, got {record_a.get('__print')}")
        return False
    
    if record_b.get("__print") != False:
        print(f"❌ FAIL: Record B __print should be false, got {record_b.get('__print')}")
        return False
    
    print("✅ Step 1b PASS: __print field preserved correctly (true and false)")
    
    # Step c: POST empty records
    print("\nStep 1c: POST /api/zayavlenie/records (empty)")
    payload = {"records": []}
    
    resp = requests.post(f"{BASE_URL}/zayavlenie/records", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    if data.get("count") != 0:
        print(f"❌ FAIL: count should be 0, got {data.get('count')}")
        return False
    
    # GET records (should be empty)
    print("\nStep 1c: GET /api/zayavlenie/records (verify empty)")
    resp = requests.get(f"{BASE_URL}/zayavlenie/records")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    records = data.get("records", None)
    if records is None:
        print(f"❌ FAIL: Missing 'records' key")
        return False
    
    if not isinstance(records, list):
        print(f"❌ FAIL: records should be a list, got {type(records)}")
        return False
    
    if len(records) != 0:
        print(f"❌ FAIL: records should be empty, got {len(records)} items")
        return False
    
    print("✅ Step 1c PASS: Empty records saved and retrieved")
    
    print("✅ PASS: TEST 1 - Saving list of records (persist)")
    return True


def test_2_underline_pdf():
    """
    TEST 2: Underline in PDF doesn't break generation
    a. POST /api/zayavlenie/template {"template":[{"id":"u1","type":"text","page":1,"x":20,"y":20,
       "align":"left","text":"Подчёркнутый","size":12,"underline":true}]} → 200 saved==true
    b. POST /api/zayavlenie/preview {"records":[{"fio":"Тест"}]} → 200 application/pdf,
       via pymupdf exactly 2 pages (doesn't crash)
    c. MANDATORY at end: POST /api/zayavlenie/template/reset → 200 reset==true
       (restore default template, otherwise preview will be almost empty)
    """
    print("\n=== TEST 2: Underline in PDF doesn't break generation ===")
    
    # Step a: POST template with underline
    print("\nStep 2a: POST /api/zayavlenie/template (with underline)")
    template = [{
        "id": "u1",
        "type": "text",
        "page": 1,
        "x": 20,
        "y": 20,
        "align": "left",
        "text": "Подчёркнутый",
        "size": 12,
        "underline": True
    }]
    
    payload = {"template": template}
    resp = requests.post(f"{BASE_URL}/zayavlenie/template", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    if not data.get("saved"):
        print(f"❌ FAIL: saved should be true, got {data.get('saved')}")
        return False
    
    print("✅ Step 2a PASS")
    
    # Step b: POST preview (should not crash with underline)
    print("\nStep 2b: POST /api/zayavlenie/preview (with underline template)")
    payload = {"records": [{"fio": "Тест"}]}
    
    resp = requests.post(f"{BASE_URL}/zayavlenie/preview", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    content_type = resp.headers.get("Content-Type", "")
    print(f"Content-Type: {content_type}")
    
    if "application/pdf" not in content_type:
        print(f"❌ FAIL: Expected application/pdf, got {content_type}")
        return False
    
    pdf_data = resp.content
    print(f"PDF size: {len(pdf_data)} bytes")
    
    if not pdf_data.startswith(b"%PDF"):
        print(f"❌ FAIL: PDF should start with %PDF, got {pdf_data[:10]}")
        return False
    
    # Check with pymupdf (should not crash)
    try:
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page_count = len(doc)
        print(f"Page count: {page_count}")
        
        if page_count != 2:
            print(f"❌ FAIL: Expected exactly 2 pages, got {page_count}")
            doc.close()
            return False
        
        doc.close()
        print("✅ Step 2b PASS: PDF generated successfully with underline (2 pages)")
        
    except Exception as e:
        print(f"❌ FAIL: Error processing PDF with underline: {e}")
        return False
    
    # Step c: MANDATORY reset template
    print("\nStep 2c: POST /api/zayavlenie/template/reset (MANDATORY)")
    resp = requests.post(f"{BASE_URL}/zayavlenie/template/reset")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    if not data.get("reset"):
        print(f"❌ FAIL: reset should be true, got {data.get('reset')}")
        return False
    
    print("✅ Step 2c PASS: Template reset to default")
    
    print("✅ PASS: TEST 2 - Underline in PDF doesn't break generation")
    return True


def test_3_regression_preview():
    """
    TEST 3: REGRESSION - POST /api/zayavlenie/preview with real data
    - 200 application/pdf
    - Via pymupdf: 2 pages A4-portrait (rect≈595.28×841.89)
    - Page 0 contains: 'ЗАЯВЛЕНИЕ', 'по месту пребывания', 'Иванов Иван Иванович', 'пр-т Дзержинского'
    - Page 1 contains: 'Общая площадь' and '5467,9'
    """
    print("\n=== TEST 3: REGRESSION - POST /api/zayavlenie/preview ===")
    
    record = {
        "fio": "Иванов Иван Иванович",
        "birth_year": "2006",
        "area": "5467,9",
        "res_street": "пр-т Дзержинского"
    }
    
    payload = {"records": [record]}
    
    resp = requests.post(f"{BASE_URL}/zayavlenie/preview", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    content_type = resp.headers.get("Content-Type", "")
    print(f"Content-Type: {content_type}")
    
    if "application/pdf" not in content_type:
        print(f"❌ FAIL: Expected application/pdf, got {content_type}")
        return False
    
    pdf_data = resp.content
    print(f"PDF size: {len(pdf_data)} bytes")
    
    if not pdf_data.startswith(b"%PDF"):
        print(f"❌ FAIL: PDF should start with %PDF")
        return False
    
    # Check with pymupdf
    try:
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page_count = len(doc)
        print(f"Page count: {page_count}")
        
        if page_count != 2:
            print(f"❌ FAIL: Expected 2 pages, got {page_count}")
            doc.close()
            return False
        
        # Check page sizes (A4 portrait: 595.28 x 841.89 pt)
        for i in range(2):
            page = doc[i]
            rect = page.rect
            width = rect.width
            height = rect.height
            print(f"Page {i} size: {width:.2f} x {height:.2f} pt")
            
            # Allow tolerance of ±2 pt
            if not (593 <= width <= 598):
                print(f"❌ FAIL: Page {i} width should be ~595.28 pt, got {width:.2f}")
                doc.close()
                return False
            
            if not (839 <= height <= 844):
                print(f"❌ FAIL: Page {i} height should be ~841.89 pt, got {height:.2f}")
                doc.close()
                return False
        
        # Check text content page 0
        page0_text = doc[0].get_text()
        print(f"\nPage 0 text sample (first 300 chars):\n{page0_text[:300]}")
        
        required_page0 = ["ЗАЯВЛЕНИЕ", "по месту пребывания", "Иванов Иван Иванович", "пр-т Дзержинского"]
        for text in required_page0:
            if text not in page0_text:
                print(f"❌ FAIL: Page 0 should contain '{text}'")
                doc.close()
                return False
            print(f"✓ Found '{text}' in page 0")
        
        # Check text content page 1
        page1_text = doc[1].get_text()
        print(f"\nPage 1 text sample (first 300 chars):\n{page1_text[:300]}")
        
        required_page1 = ["Общая площадь", "5467,9"]
        for text in required_page1:
            if text not in page1_text:
                print(f"❌ FAIL: Page 1 should contain '{text}'")
                doc.close()
                return False
            print(f"✓ Found '{text}' in page 1")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ FAIL: Error processing PDF: {e}")
        return False
    
    print("✅ PASS: TEST 3 - REGRESSION preview")
    return True


def test_4_regression_template():
    """
    TEST 4: REGRESSION - GET /api/zayavlenie/template
    - 200, template ~149 elements, is_custom==false
    """
    print("\n=== TEST 4: REGRESSION - GET /api/zayavlenie/template ===")
    
    resp = requests.get(f"{BASE_URL}/zayavlenie/template")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    
    if "template" not in data:
        print(f"❌ FAIL: Missing 'template' key")
        return False
    
    template = data["template"]
    elem_count = len(template)
    print(f"Template elements count: {elem_count}")
    
    if elem_count < 140 or elem_count > 160:
        print(f"❌ FAIL: Expected ~149 elements, got {elem_count}")
        return False
    
    is_custom = data.get("is_custom")
    print(f"is_custom: {is_custom}")
    
    if is_custom != False:
        print(f"❌ FAIL: is_custom should be false, got {is_custom}")
        return False
    
    print("✅ PASS: TEST 4 - REGRESSION template")
    return True


def test_5_regression_preview_png():
    """
    TEST 5: REGRESSION - POST /api/zayavlenie/preview-png
    - side='front' → 200 image/png
    - side='back' → 200 image/png
    """
    print("\n=== TEST 5: REGRESSION - POST /api/zayavlenie/preview-png ===")
    
    record = {"fio": "Иванов"}
    
    # Test front
    print("\nTesting side='front'")
    payload = {"records": [record], "side": "front"}
    resp = requests.post(f"{BASE_URL}/zayavlenie/preview-png", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    content_type = resp.headers.get("Content-Type", "")
    print(f"Content-Type: {content_type}")
    
    if "image/png" not in content_type:
        print(f"❌ FAIL: Expected image/png, got {content_type}")
        return False
    
    front_data = resp.content
    print(f"Front PNG size: {len(front_data)} bytes")
    
    if not front_data.startswith(b"\x89PNG"):
        print(f"❌ FAIL: PNG should start with \\x89PNG")
        return False
    
    # Test back
    print("\nTesting side='back'")
    payload = {"records": [record], "side": "back"}
    resp = requests.post(f"{BASE_URL}/zayavlenie/preview-png", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    content_type = resp.headers.get("Content-Type", "")
    print(f"Content-Type: {content_type}")
    
    if "image/png" not in content_type:
        print(f"❌ FAIL: Expected image/png, got {content_type}")
        return False
    
    back_data = resp.content
    print(f"Back PNG size: {len(back_data)} bytes")
    
    if not back_data.startswith(b"\x89PNG"):
        print(f"❌ FAIL: PNG should start with \\x89PNG")
        return False
    
    print("✅ PASS: TEST 5 - REGRESSION preview-png")
    return True


def test_6_regression_ping_stats():
    """
    TEST 6: REGRESSION - GET /api/_ping and GET /api/stats
    """
    print("\n=== TEST 6: REGRESSION - GET /api/_ping and /api/stats ===")
    
    # Test _ping
    print("\nTesting GET /api/_ping")
    resp = requests.get(f"{BASE_URL}/_ping")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    # Test stats
    print("\nTesting GET /api/stats")
    resp = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    
    print("✅ PASS: TEST 6 - REGRESSION _ping and stats")
    return True


def cleanup_state():
    """
    MANDATORY CLEANUP at end:
    - POST /api/zayavlenie/records {"records":[]} to clear
    - Verify template is reset (GET template is_custom==false)
    """
    print("\n=== MANDATORY CLEANUP ===")
    
    # Clear records
    print("\nClearing records: POST /api/zayavlenie/records (empty)")
    payload = {"records": []}
    resp = requests.post(f"{BASE_URL}/zayavlenie/records", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        print("✓ Records cleared")
    else:
        print(f"⚠ Warning: Could not clear records, status {resp.status_code}")
    
    # Verify template is reset
    print("\nVerifying template is reset: GET /api/zayavlenie/template")
    resp = requests.get(f"{BASE_URL}/zayavlenie/template")
    
    if resp.status_code == 200:
        data = resp.json()
        is_custom = data.get("is_custom")
        print(f"is_custom: {is_custom}")
        
        if is_custom == False:
            print("✓ Template is reset (is_custom==false)")
        else:
            print("⚠ Warning: Template is custom, resetting...")
            reset_resp = requests.post(f"{BASE_URL}/zayavlenie/template/reset")
            if reset_resp.status_code == 200:
                print("✓ Template reset successfully")
            else:
                print(f"⚠ Warning: Could not reset template, status {reset_resp.status_code}")
    else:
        print(f"⚠ Warning: Could not verify template, status {resp.status_code}")


def main():
    print("=" * 80)
    print("BACKEND TESTING: NEW /api/zayavlenie/* features")
    print("1. Saving list of records (persist)")
    print("2. Underline in PDF doesn't break generation")
    print("3. Regression tests")
    print("=" * 80)
    
    tests = [
        ("TEST 1: Save records (persist)", test_1_save_records_persist),
        ("TEST 2: Underline in PDF", test_2_underline_pdf),
        ("TEST 3: REGRESSION - preview", test_3_regression_preview),
        ("TEST 4: REGRESSION - template", test_4_regression_template),
        ("TEST 5: REGRESSION - preview-png", test_5_regression_preview_png),
        ("TEST 6: REGRESSION - _ping/stats", test_6_regression_ping_stats),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Mandatory cleanup
    cleanup_state()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
