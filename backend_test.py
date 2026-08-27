#!/usr/bin/env python3
"""
Backend testing for /api/zayavlenie/* endpoints after template conversion to EDITABLE TEMPLATE.
Tests the new template structure with elements (text/line/field).
"""
import requests
import pymupdf
import io
import sys
from openpyxl import load_workbook
from datetime import datetime

# Backend URL from frontend/.env
BASE_URL = "https://form-portal-15.preview.emergentagent.com/api"

def test_1_get_template():
    """
    TEST 1: GET /api/zayavlenie/template → 200
    - template is array of ~149 elements
    - types include 'text', 'line', 'field'
    - among field elements: field=='applicant', field=='passport_series', field=='area'
    - slots is array of objects with keys slot/page/label
    - is_custom == false (on clean DB)
    - page_count == 2
    """
    print("\n=== TEST 1: GET /api/zayavlenie/template ===")
    resp = requests.get(f"{BASE_URL}/zayavlenie/template")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check required keys
    if "template" not in data:
        print("❌ FAIL: Missing 'template' key")
        return False
    
    template = data["template"]
    if not isinstance(template, list):
        print(f"❌ FAIL: template is not a list, got {type(template)}")
        return False
    
    elem_count = len(template)
    print(f"Template elements count: {elem_count}")
    
    if elem_count < 140 or elem_count > 160:
        print(f"❌ FAIL: Expected ~149 elements, got {elem_count}")
        return False
    
    # Check types
    types_found = set()
    field_names = []
    for elem in template:
        if "type" in elem:
            types_found.add(elem["type"])
        if elem.get("type") == "field" and "field" in elem:
            field_names.append(elem["field"])
    
    print(f"Types found: {types_found}")
    print(f"Field elements count: {len(field_names)}")
    print(f"Field names: {field_names}")
    
    required_types = {"text", "line", "field"}
    if not required_types.issubset(types_found):
        print(f"❌ FAIL: Missing required types. Expected {required_types}, found {types_found}")
        return False
    
    # Check required field elements
    required_fields = {"applicant", "passport_series", "area"}
    fields_set = set(field_names)
    if not required_fields.issubset(fields_set):
        print(f"❌ FAIL: Missing required field elements. Expected {required_fields}, found {fields_set}")
        return False
    
    # Check slots
    if "slots" not in data:
        print("❌ FAIL: Missing 'slots' key")
        return False
    
    slots = data["slots"]
    if not isinstance(slots, list) or len(slots) == 0:
        print(f"❌ FAIL: slots should be non-empty array, got {type(slots)} with {len(slots) if isinstance(slots, list) else 0} items")
        return False
    
    # Check slot structure
    first_slot = slots[0]
    required_slot_keys = {"slot", "page", "label"}
    if not required_slot_keys.issubset(set(first_slot.keys())):
        print(f"❌ FAIL: Slot missing required keys. Expected {required_slot_keys}, found {set(first_slot.keys())}")
        return False
    
    print(f"Slots count: {len(slots)}")
    print(f"First slot: {first_slot}")
    
    # Check is_custom
    if "is_custom" not in data:
        print("❌ FAIL: Missing 'is_custom' key")
        return False
    
    is_custom = data["is_custom"]
    print(f"is_custom: {is_custom}")
    
    # Note: is_custom might be true if previous tests ran, so we'll just check it exists
    
    # Check page_count
    if "page_count" not in data:
        print("❌ FAIL: Missing 'page_count' key")
        return False
    
    page_count = data["page_count"]
    print(f"page_count: {page_count}")
    
    if page_count != 2:
        print(f"❌ FAIL: Expected page_count=2, got {page_count}")
        return False
    
    print("✅ PASS: GET /api/zayavlenie/template")
    return True


def test_2_save_and_reset_template():
    """
    TEST 2: SAVE+RESET template (IMPORTANT about order!)
    a. POST /api/zayavlenie/template with custom template → 200, saved==true, count==1
    b. GET /api/zayavlenie/template → template contains exactly 1 element, is_custom==true
    c. POST /api/zayavlenie/template/reset (no body) → 200, reset==true, response contains ~149 elements
    d. GET /api/zayavlenie/template → is_custom==false, template again ~149 elements
    """
    print("\n=== TEST 2: SAVE+RESET template ===")
    
    # Step a: POST custom template
    print("\nStep 2a: POST /api/zayavlenie/template (save custom)")
    custom_template = [{
        "id": "t1",
        "type": "text",
        "page": 1,
        "x": 10,
        "y": 10,
        "align": "left",
        "text": "ТЕСТ ШАПКА",
        "size": 10,
        "bold": True
    }]
    
    resp = requests.post(f"{BASE_URL}/zayavlenie/template", json={"template": custom_template})
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    if not data.get("saved"):
        print(f"❌ FAIL: saved should be true, got {data.get('saved')}")
        return False
    
    if data.get("count") != 1:
        print(f"❌ FAIL: count should be 1, got {data.get('count')}")
        return False
    
    print("✅ Step 2a PASS")
    
    # Step b: GET template (should be custom)
    print("\nStep 2b: GET /api/zayavlenie/template (verify custom)")
    resp = requests.get(f"{BASE_URL}/zayavlenie/template")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    template = data.get("template", [])
    is_custom = data.get("is_custom")
    
    print(f"Template elements count: {len(template)}")
    print(f"is_custom: {is_custom}")
    
    if len(template) != 1:
        print(f"❌ FAIL: Expected 1 element, got {len(template)}")
        return False
    
    if not is_custom:
        print(f"❌ FAIL: is_custom should be true, got {is_custom}")
        return False
    
    print("✅ Step 2b PASS")
    
    # Step c: POST reset
    print("\nStep 2c: POST /api/zayavlenie/template/reset")
    resp = requests.post(f"{BASE_URL}/zayavlenie/template/reset")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    
    if not data.get("reset"):
        print(f"❌ FAIL: reset should be true, got {data.get('reset')}")
        return False
    
    if "template" in data:
        reset_template = data["template"]
        print(f"Reset template elements count: {len(reset_template)}")
        if len(reset_template) < 140 or len(reset_template) > 160:
            print(f"❌ FAIL: Expected ~149 elements in reset response, got {len(reset_template)}")
            return False
    
    print("✅ Step 2c PASS")
    
    # Step d: GET template (should be default again)
    print("\nStep 2d: GET /api/zayavlenie/template (verify reset)")
    resp = requests.get(f"{BASE_URL}/zayavlenie/template")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    template = data.get("template", [])
    is_custom = data.get("is_custom")
    
    print(f"Template elements count: {len(template)}")
    print(f"is_custom: {is_custom}")
    
    if len(template) < 140 or len(template) > 160:
        print(f"❌ FAIL: Expected ~149 elements, got {len(template)}")
        return False
    
    if is_custom:
        print(f"❌ FAIL: is_custom should be false after reset, got {is_custom}")
        return False
    
    print("✅ Step 2d PASS")
    print("✅ PASS: SAVE+RESET template")
    return True


def test_3_preview_pdf():
    """
    TEST 3: POST /api/zayavlenie/preview (after reset!)
    - 200, Content-Type application/pdf, body starts with %PDF
    - Via pymupdf: EXACTLY 2 pages, each A4-portrait (rect width≈595.28, height≈841.89 pt)
    - Text page 0 contains: 'ЗАЯВЛЕНИЕ', 'по месту пребывания', 'Иванов Иван Иванович', 'пр-т Дзержинского'
    - Text page 1 contains: 'Общая площадь' and '5467,9'
    """
    print("\n=== TEST 3: POST /api/zayavlenie/preview ===")
    
    record = {
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
        print(f"❌ FAIL: PDF should start with %PDF, got {pdf_data[:10]}")
        return False
    
    # Check with pymupdf
    try:
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page_count = len(doc)
        print(f"Page count: {page_count}")
        
        if page_count != 2:
            print(f"❌ FAIL: Expected EXACTLY 2 pages, got {page_count}")
            doc.close()
            return False
        
        # Check page sizes (A4 portrait: 595.28 x 841.89 pt)
        for i in range(page_count):
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
        print(f"\nPage 0 text sample (first 500 chars):\n{page0_text[:500]}")
        
        required_page0 = ["ЗАЯВЛЕНИЕ", "по месту пребывания", "Иванов Иван Иванович", "пр-т Дзержинского"]
        for text in required_page0:
            if text not in page0_text:
                print(f"❌ FAIL: Page 0 should contain '{text}'")
                doc.close()
                return False
            print(f"✓ Found '{text}' in page 0")
        
        # Check text content page 1
        page1_text = doc[1].get_text()
        print(f"\nPage 1 text sample (first 500 chars):\n{page1_text[:500]}")
        
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
    
    print("✅ PASS: POST /api/zayavlenie/preview")
    return True


def test_4_background_images():
    """
    TEST 4: GET /api/zayavlenie/background?page=1 → 200 image/png
           GET /api/zayavlenie/background?page=2 → 200 image/png
    """
    print("\n=== TEST 4: GET /api/zayavlenie/background ===")
    
    for page in [1, 2]:
        print(f"\nTesting page={page}")
        resp = requests.get(f"{BASE_URL}/zayavlenie/background?page={page}")
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {resp.status_code}")
            return False
        
        content_type = resp.headers.get("Content-Type", "")
        print(f"Content-Type: {content_type}")
        
        if "image/png" not in content_type:
            print(f"❌ FAIL: Expected image/png, got {content_type}")
            return False
        
        png_data = resp.content
        print(f"PNG size: {len(png_data)} bytes")
        
        if not png_data.startswith(b"\x89PNG"):
            print(f"❌ FAIL: PNG should start with \\x89PNG, got {png_data[:10]}")
            return False
        
        print(f"✓ Page {page} background OK")
    
    print("✅ PASS: GET /api/zayavlenie/background")
    return True


def test_5_preview_png():
    """
    TEST 5: POST /api/zayavlenie/preview-png
    - with "side":"front" → 200 image/png
    - with "side":"back" → 200 image/png (different image)
    """
    print("\n=== TEST 5: POST /api/zayavlenie/preview-png ===")
    
    record = {
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
    }
    
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
    
    # Verify they are different
    if front_data == back_data:
        print(f"❌ FAIL: Front and back images should be different")
        return False
    
    size_diff = abs(len(front_data) - len(back_data))
    print(f"Size difference: {size_diff} bytes ({size_diff/len(front_data)*100:.1f}%)")
    print("✓ Front and back are different images")
    
    print("✅ PASS: POST /api/zayavlenie/preview-png")
    return True


def test_6_prefill():
    """
    TEST 6: POST /api/zayavlenie/prefill
    - with students array → 200, returns records array (regression not broken)
    """
    print("\n=== TEST 6: POST /api/zayavlenie/prefill ===")
    
    payload = {
        "students": [{
            "full_name": "Иванов Иван Иванович",
            "birth_date": "01.09.2007",
            "citizenship": "РБ",
            "passport_number": "MP1234567"
        }]
    }
    
    resp = requests.post(f"{BASE_URL}/zayavlenie/prefill", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    
    if "records" not in data:
        print(f"❌ FAIL: Missing 'records' key")
        return False
    
    records = data["records"]
    if not isinstance(records, list):
        print(f"❌ FAIL: records should be a list, got {type(records)}")
        return False
    
    if len(records) != 1:
        print(f"❌ FAIL: Expected 1 record, got {len(records)}")
        return False
    
    print(f"Record: {records[0]}")
    
    print("✅ PASS: POST /api/zayavlenie/prefill")
    return True


def test_7_package_regression():
    """
    TEST 7: REGRESSION of package
    - GET /api/master-template → 200 (xlsx)
    - Fill one row via openpyxl
    - POST /api/master-upload → 200, has 'zayavlenie' key
    - POST /api/package with include.zayavlenie → 200, PDF with pages > 0
    """
    print("\n=== TEST 7: Package regression ===")
    
    # Step 1: Get master template
    print("\nStep 7.1: GET /api/master-template")
    resp = requests.get(f"{BASE_URL}/master-template")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    content_type = resp.headers.get("Content-Type", "")
    print(f"Content-Type: {content_type}")
    
    if "spreadsheet" not in content_type and "excel" not in content_type:
        print(f"⚠ Warning: Unexpected content type {content_type}, but continuing...")
    
    xlsx_data = resp.content
    print(f"XLSX size: {len(xlsx_data)} bytes")
    
    # Step 2: Fill one row
    print("\nStep 7.2: Fill template with test data")
    try:
        wb = load_workbook(io.BytesIO(xlsx_data))
        ws = wb["Данные"]
        
        # Fill row 3 with test data (row 2 is headers)
        test_data = {
            "ФИО": "Иванов Иван Иванович",
            "Дата рождения": datetime(2006, 8, 3),
            "Гражданство": "Республика Беларусь",
            "Номер паспорта": "MP 1234567",
            "Дата выдачи": datetime(2020, 1, 10),
            "Срок действия": datetime(2030, 1, 10),
            "Кем выдан": "МВД РБ",
            "ИИН": "1234567A001PB5",
            "Номер договора": "TEST-001",
            "Дата подписания": datetime(2025, 7, 21),
            "Номер приказа": "123",
            "Дата приказа": datetime(2025, 7, 21),
            "Номер комнаты": "101",
            "Срок договора до": datetime(2028, 6, 30),
            "Адрес регистрации": "г. Минск, ул. Тестовая, д. 1",
            "Телефон": "+375291234567",
            "Дата прибытия": datetime(2024, 9, 1),
            "Проживает с": datetime(2010, 1, 1),
            "Дата регистрации": datetime(2024, 9, 1),
            "Регистрация с": datetime(2024, 9, 1),
            "Регистрация по": datetime(2028, 6, 30),
            "Срок пребывания": datetime(2028, 6, 30),
        }
        
        # Get headers from row 2
        headers = []
        for cell in ws[2]:
            if cell.value:
                headers.append(cell.value)
        
        print(f"Found {len(headers)} headers")
        
        # Fill row 3
        for col_idx, header in enumerate(headers, start=1):
            if header in test_data:
                ws.cell(row=3, column=col_idx, value=test_data[header])
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        filled_xlsx = output.getvalue()
        print(f"Filled XLSX size: {len(filled_xlsx)} bytes")
        
    except Exception as e:
        print(f"❌ FAIL: Error filling template: {e}")
        return False
    
    # Step 3: Upload master
    print("\nStep 7.3: POST /api/master-upload")
    files = {"file": ("test_master.xlsx", filled_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    resp = requests.post(f"{BASE_URL}/master-upload", files=files)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
        return False
    
    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    
    if "zayavlenie" not in data:
        print(f"❌ FAIL: Missing 'zayavlenie' key in response")
        return False
    
    zayavlenie_data = data["zayavlenie"]
    print(f"Zayavlenie records count: {len(zayavlenie_data) if isinstance(zayavlenie_data, list) else 'N/A'}")
    
    if not isinstance(zayavlenie_data, list) or len(zayavlenie_data) == 0:
        print(f"❌ FAIL: zayavlenie should be non-empty list")
        return False
    
    # Get master data for package
    master_data = data.get("master", [])
    if not master_data:
        print(f"❌ FAIL: No master data in response")
        return False
    
    print(f"Master records count: {len(master_data)}")
    
    # Step 4: Generate package
    print("\nStep 7.4: POST /api/package")
    package_payload = {
        "people": [master_data[0]],
        "include": {"zayavlenie": True}
    }
    
    resp = requests.post(f"{BASE_URL}/package", json=package_payload)
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
    print(f"Package PDF size: {len(pdf_data)} bytes")
    
    if not pdf_data.startswith(b"%PDF"):
        print(f"❌ FAIL: PDF should start with %PDF")
        return False
    
    # Check page count
    try:
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page_count = len(doc)
        print(f"Package page count: {page_count}")
        doc.close()
        
        if page_count == 0:
            print(f"❌ FAIL: Package should have pages > 0")
            return False
        
    except Exception as e:
        print(f"❌ FAIL: Error processing package PDF: {e}")
        return False
    
    print("✅ PASS: Package regression")
    return True


def test_8_health_regression():
    """
    TEST 8: Health regression
    - GET /api/_ping → 200 {ok:true}
    - GET /api/stats → 200
    """
    print("\n=== TEST 8: Health regression ===")
    
    # Test _ping
    print("\nTesting GET /api/_ping")
    resp = requests.get(f"{BASE_URL}/_ping")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response: {data}")
    
    if not data.get("ok"):
        print(f"❌ FAIL: Expected ok=true, got {data.get('ok')}")
        return False
    
    # Test stats
    print("\nTesting GET /api/stats")
    resp = requests.get(f"{BASE_URL}/stats")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response keys: {list(data.keys())}")
    
    print("✅ PASS: Health regression")
    return True


def verify_template_reset():
    """
    Final verification: Ensure custom template is reset (is_custom==false)
    """
    print("\n=== FINAL VERIFICATION: Template reset ===")
    resp = requests.get(f"{BASE_URL}/zayavlenie/template")
    
    if resp.status_code != 200:
        print(f"⚠ Warning: Could not verify template reset, status {resp.status_code}")
        return
    
    data = resp.json()
    is_custom = data.get("is_custom")
    
    print(f"is_custom: {is_custom}")
    
    if is_custom:
        print("⚠ Warning: Template is still custom, resetting...")
        reset_resp = requests.post(f"{BASE_URL}/zayavlenie/template/reset")
        if reset_resp.status_code == 200:
            print("✓ Template reset successfully")
        else:
            print(f"⚠ Warning: Could not reset template, status {reset_resp.status_code}")
    else:
        print("✓ Template is already reset (is_custom=false)")


def main():
    print("=" * 80)
    print("BACKEND TESTING: /api/zayavlenie/* endpoints")
    print("Testing EDITABLE TEMPLATE structure (text/line/field elements)")
    print("=" * 80)
    
    tests = [
        ("TEST 1: GET template", test_1_get_template),
        ("TEST 2: SAVE+RESET template", test_2_save_and_reset_template),
        ("TEST 3: POST preview (PDF)", test_3_preview_pdf),
        ("TEST 4: GET background images", test_4_background_images),
        ("TEST 5: POST preview-png", test_5_preview_png),
        ("TEST 6: POST prefill", test_6_prefill),
        ("TEST 7: Package regression", test_7_package_regression),
        ("TEST 8: Health regression", test_8_health_regression),
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
    
    # Final verification
    verify_template_reset()
    
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
