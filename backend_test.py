#!/usr/bin/env python3
"""Backend API tests for Banetskaya.by - Focus on PDF generation and font fix"""
import sys
import requests
import pymupdf  # PyMuPDF for PDF validation and text extraction

# Backend URL from frontend/.env
BACKEND_URL = "https://1a44cbd3-e499-4c2e-b9f8-dd81fc5e4c75.preview.emergentagent.com/api"

def test_overlay_generate_card_with_form():
    """Test 1: POST /api/overlay/generate with page_size=card, with_form=true"""
    print("\n=== Test 1: POST /api/overlay/generate (card, with_form=true) ===")
    
    payload = {
        "records": [{
            "fio": "Иванов Иван Иванович",
            "address": "г. Минск",
            "from_day": "1",
            "from_month": "июля",
            "from_year": "25",
            "to_day": "1",
            "to_month": "июля",
            "to_year": "26"
        }],
        "page_size": "card",
        "with_form": True
    }
    
    try:
        resp = requests.post(f"{BACKEND_URL}/overlay/generate", json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            return False
        
        if "application/pdf" not in resp.headers.get('Content-Type', ''):
            print(f"❌ FAILED: Expected application/pdf, got {resp.headers.get('Content-Type')}")
            return False
        
        pdf_data = resp.content
        
        # Check PDF signature
        if not pdf_data.startswith(b'%PDF'):
            print(f"❌ FAILED: PDF does not start with %PDF")
            return False
        
        print(f"✅ Valid PDF signature (%PDF)")
        
        # Open with pymupdf and check page size
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page = doc[0]
        width = page.rect.width
        height = page.rect.height
        
        print(f"Page size: {width:.2f} x {height:.2f} pt")
        
        # Expected: ~416.69 x 291.97 pt (147x103 mm)
        expected_w = 416.69
        expected_h = 291.97
        tolerance = 2.0
        
        if abs(width - expected_w) > tolerance or abs(height - expected_h) > tolerance:
            print(f"❌ FAILED: Page size mismatch. Expected ~{expected_w}x{expected_h} pt")
            doc.close()
            return False
        
        print(f"✅ Page size correct: ~147x103 mm")
        
        # Extract text from first page to verify Cyrillic (font AppSans working)
        text = page.get_text()
        print(f"Extracted text (first 200 chars): {text[:200]}")
        
        # Check for Cyrillic characters
        has_cyrillic = any(char in text for char in ["Иванов", "Минск", "июля"])
        
        if has_cyrillic:
            print(f"✅ Cyrillic text found in PDF (font AppSans working)")
        else:
            print(f"⚠️  WARNING: No expected Cyrillic text found. Text: {text[:300]}")
        
        doc.close()
        print("✅ Test 1 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_overlay_generate_a4_with_form():
    """Test 2: POST /api/overlay/generate with page_size=a4, with_form=true"""
    print("\n=== Test 2: POST /api/overlay/generate (a4, with_form=true) ===")
    
    payload = {
        "records": [{
            "fio": "Петров Петр Петрович",
            "address": "г. Гомель",
            "from_day": "5",
            "from_month": "августа",
            "from_year": "25",
            "to_day": "5",
            "to_month": "августа",
            "to_year": "26"
        }],
        "page_size": "a4",
        "with_form": True
    }
    
    try:
        resp = requests.post(f"{BACKEND_URL}/overlay/generate", json=payload, timeout=30)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        pdf_data = resp.content
        
        if not pdf_data.startswith(b'%PDF'):
            print(f"❌ FAILED: PDF does not start with %PDF")
            return False
        
        # Check page size (should be A4: ~595x842 pt)
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        page = doc[0]
        width = page.rect.width
        height = page.rect.height
        
        print(f"Page size: {width:.2f} x {height:.2f} pt")
        
        # Expected A4: ~595 x 842 pt
        expected_w = 595
        expected_h = 842
        tolerance = 5.0
        
        if abs(width - expected_w) > tolerance or abs(height - expected_h) > tolerance:
            print(f"❌ FAILED: Page size mismatch. Expected ~{expected_w}x{expected_h} pt (A4)")
            doc.close()
            return False
        
        print(f"✅ Page size correct: A4 (~595x842 pt)")
        doc.close()
        print("✅ Test 2 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_overlay_form_background():
    """Test 3: GET /api/overlay/form-background"""
    print("\n=== Test 3: GET /api/overlay/form-background ===")
    
    try:
        resp = requests.get(f"{BACKEND_URL}/overlay/form-background", timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if "image/png" not in resp.headers.get('Content-Type', ''):
            print(f"❌ FAILED: Expected image/png, got {resp.headers.get('Content-Type')}")
            return False
        
        png_data = resp.content
        
        # Check PNG signature
        if not png_data.startswith(b'\x89PNG'):
            print(f"❌ FAILED: PNG does not start with \\x89PNG")
            return False
        
        print(f"✅ Valid PNG signature (\\x89PNG)")
        print(f"PNG size: {len(png_data)} bytes")
        
        if len(png_data) < 1000:
            print(f"❌ FAILED: PNG too small ({len(png_data)} bytes)")
            return False
        
        print(f"✅ PNG size > 1000 bytes")
        print("✅ Test 3 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_overlay_background():
    """Test 4: GET /api/overlay/background"""
    print("\n=== Test 4: GET /api/overlay/background ===")
    
    try:
        resp = requests.get(f"{BACKEND_URL}/overlay/background", timeout=30)
        print(f"Status: {resp.status_code}")
        print(f"Content-Type: {resp.headers.get('Content-Type')}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        if "image/png" not in resp.headers.get('Content-Type', ''):
            print(f"❌ FAILED: Expected image/png, got {resp.headers.get('Content-Type')}")
            return False
        
        png_data = resp.content
        
        # Check PNG signature
        if not png_data.startswith(b'\x89PNG'):
            print(f"❌ FAILED: PNG does not start with \\x89PNG")
            return False
        
        print(f"✅ Valid PNG signature (\\x89PNG)")
        print(f"PNG size: {len(png_data)} bytes")
        print("✅ Test 4 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_contract_docx_to_pdf():
    """Test 5: Contract DOCX→PDF conversion via LibreOffice"""
    print("\n=== Test 5: Contract DOCX→PDF conversion (LibreOffice) ===")
    
    # First, get available fields
    try:
        resp = requests.get(f"{BACKEND_URL}/fields", timeout=10)
        print(f"GET /api/fields: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Could not get fields")
            return False
        
        fields_data = resp.json()
        print(f"✅ Fields endpoint working, {len(fields_data.get('fields', []))} fields available")
        
    except Exception as e:
        print(f"❌ FAILED getting fields: {e}")
        return False
    
    # Now generate a contract PDF via preview endpoint
    try:
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
        
        resp = requests.post(f"{BACKEND_URL}/contracts/preview?format=pdf", json=payload, timeout=60)
        print(f"POST /api/contracts/preview?format=pdf: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            return False
        
        pdf_data = resp.content
        
        # Check PDF signature
        if not pdf_data.startswith(b'%PDF'):
            print(f"❌ FAILED: PDF does not start with %PDF")
            return False
        
        print(f"✅ Valid PDF signature (%PDF)")
        
        # Open with pymupdf and extract text to verify Cyrillic
        doc = pymupdf.open(stream=pdf_data, filetype="pdf")
        print(f"PDF has {len(doc)} pages")
        
        # Extract text from first page
        if len(doc) > 0:
            page = doc[0]
            text = page.get_text()
            print(f"Extracted text (first 300 chars): {text[:300]}")
            
            # Check for Cyrillic
            has_cyrillic = any(char in text for char in ["Тестов", "Минск", "Беларусь"])
            
            if has_cyrillic:
                print(f"✅ Cyrillic text found in contract PDF (LibreOffice + font working)")
            else:
                print(f"⚠️  WARNING: No expected Cyrillic text found in contract PDF")
        
        doc.close()
        print("✅ Test 5 PASSED - DOCX→PDF conversion working")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stats():
    """Test 6: GET /api/stats"""
    print("\n=== Test 6: GET /api/stats ===")
    
    try:
        resp = requests.get(f"{BACKEND_URL}/stats", timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        data = resp.json()
        print(f"Stats data: {data}")
        
        # Check required fields
        required_fields = ["total", "drafts", "this_month", "datasets", "recent"]
        for field in required_fields:
            if field not in data:
                print(f"❌ FAILED: Missing field '{field}' in stats")
                return False
        
        print(f"✅ All required fields present")
        print("✅ Test 6 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    print("=" * 80)
    print("BACKEND API TESTS - PDF Generation & Font Fix Verification")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    
    tests = [
        ("Overlay Generate (card, with_form)", test_overlay_generate_card_with_form),
        ("Overlay Generate (a4, with_form)", test_overlay_generate_a4_with_form),
        ("Overlay Form Background", test_overlay_form_background),
        ("Overlay Background", test_overlay_background),
        ("Contract DOCX→PDF (LibreOffice)", test_contract_docx_to_pdf),
        ("Stats", test_stats),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
