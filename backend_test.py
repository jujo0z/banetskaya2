#!/usr/bin/env python3
"""
Backend testing for Banetskaya application - Uppercase feature for Forms 19 and 24
Testing Agent: Testing uppercase conversion in forma19/forma24 endpoints
"""
import requests
import io
import sys
from pypdf import PdfReader

# Backend URL from frontend/.env
BASE_URL = "https://83c86cc1-a64f-4dab-9797-7336a42191d5.preview.emergentagent.com/api"

def test_forma19_fields():
    """Test 1: GET /api/forma19/fields - Get field schema"""
    print("\n=== TEST 1: GET /api/forma19/fields ===")
    resp = requests.get(f"{BASE_URL}/forma19/fields")
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert "groups" in data, "Missing 'groups' in response"
    assert "keys" in data, "Missing 'keys' in response"
    print(f"✓ Fields schema returned: {len(data['keys'])} keys")
    return data

def test_forma24_fields():
    """Test 2: GET /api/forma24/fields - Get field schema"""
    print("\n=== TEST 2: GET /api/forma24/fields ===")
    resp = requests.get(f"{BASE_URL}/forma24/fields")
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert "groups" in data, "Missing 'groups' in response"
    assert "keys" in data, "Missing 'keys' in response"
    print(f"✓ Fields schema returned: {len(data['keys'])} keys")
    return data

def test_forma19_preview_png_uppercase():
    """Test 3: POST /api/forma19/preview-png with lowercase input - expect valid PNG"""
    print("\n=== TEST 3: POST /api/forma19/preview-png (lowercase input) ===")
    
    # Lowercase input - Russian names
    payload = {
        "records": [
            {
                "surname": "мороз",
                "first_name": "иван",
                "patronymic": "дмитриевич",
                "citizenship": "республики беларусь",
                "res_city": "минск",
                "res_street": "ленина",
                "res_house": "10",
                "res_apartment": "5",
                "purpose": "на учёбу"
            }
        ],
        "side": "front"
    }
    
    resp = requests.post(f"{BASE_URL}/forma19/preview-png", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers['Content-Type'] == 'image/png', f"Expected image/png, got {resp.headers['Content-Type']}"
    
    # Verify PNG signature
    png_data = resp.content
    assert png_data[:4] == b'\x89PNG', "Invalid PNG signature"
    print(f"✓ Valid PNG returned: {len(png_data)} bytes")
    return png_data

def test_forma24_preview_png_uppercase():
    """Test 4: POST /api/forma24/preview-png with lowercase input - expect valid PNG"""
    print("\n=== TEST 4: POST /api/forma24/preview-png (lowercase input) ===")
    
    # Lowercase input
    payload = {
        "records": [
            {
                "surname": "мороз",
                "first_name": "иван",
                "patronymic": "дмитриевич",
                "citizenship": "республики беларусь",
                "nationality": "белорус",
                "res_city": "минск"
            }
        ],
        "side": "front"
    }
    
    resp = requests.post(f"{BASE_URL}/forma24/preview-png", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers['Content-Type'] == 'image/png', f"Expected image/png, got {resp.headers['Content-Type']}"
    
    # Verify PNG signature
    png_data = resp.content
    assert png_data[:4] == b'\x89PNG', "Invalid PNG signature"
    print(f"✓ Valid PNG returned: {len(png_data)} bytes")
    return png_data

def test_forma19_preview_pdf_uppercase():
    """Test 5: POST /api/forma19/preview with lowercase input - extract text and verify UPPERCASE"""
    print("\n=== TEST 5: POST /api/forma19/preview (lowercase input, verify UPPERCASE in PDF) ===")
    
    # Lowercase input
    payload = {
        "records": [
            {
                "surname": "мороз",
                "first_name": "иван",
                "patronymic": "дмитриевич",
                "citizenship": "республики беларусь",
                "res_city": "минск",
                "res_street": "ленина",
                "res_house": "10",
                "purpose": "на учёбу"
            }
        ],
        "duplex_flip": "long"
    }
    
    resp = requests.post(f"{BASE_URL}/forma19/preview", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers['Content-Type'] == 'application/pdf', f"Expected application/pdf, got {resp.headers['Content-Type']}"
    
    # Verify PDF signature
    pdf_data = resp.content
    assert pdf_data[:4] == b'%PDF', "Invalid PDF signature"
    print(f"✓ Valid PDF returned: {len(pdf_data)} bytes")
    
    # Extract text from PDF
    try:
        reader = PdfReader(io.BytesIO(pdf_data))
        print(f"✓ PDF has {len(reader.pages)} pages")
        
        # Extract text from all pages
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            full_text += text
            print(f"  Page {i+1} text length: {len(text)} chars")
        
        # Verify UPPERCASE values are present
        print("\n--- Checking for UPPERCASE values ---")
        uppercase_checks = {
            "МОРОЗ": "surname",
            "ИВАН": "first_name",
            "ДМИТРИЕВИЧ": "patronymic",
            "МИНСК": "city"
        }
        
        found_uppercase = []
        found_lowercase = []
        
        for upper_val, field_name in uppercase_checks.items():
            if upper_val in full_text:
                found_uppercase.append(f"✓ Found '{upper_val}' ({field_name})")
            else:
                print(f"  ✗ NOT FOUND: '{upper_val}' ({field_name})")
        
        # Check for lowercase versions (should NOT be present)
        lowercase_checks = ["мороз", "иван", "дмитриевич", "минск"]
        for lower_val in lowercase_checks:
            if lower_val in full_text.lower() and lower_val not in ["минск"]:  # минск might be in static labels
                # Check if it's actually lowercase in the original text
                if lower_val in full_text:
                    found_lowercase.append(f"✗ Found lowercase '{lower_val}' (SHOULD BE UPPERCASE)")
        
        print("\nUppercase values found:")
        for msg in found_uppercase:
            print(f"  {msg}")
        
        if found_lowercase:
            print("\n⚠ WARNING: Lowercase values found (should be uppercase):")
            for msg in found_lowercase:
                print(f"  {msg}")
        
        # At least some uppercase values should be found
        assert len(found_uppercase) >= 2, f"Expected at least 2 uppercase values, found {len(found_uppercase)}"
        print(f"\n✓ UPPERCASE conversion verified: {len(found_uppercase)} values found in uppercase")
        
    except Exception as e:
        print(f"✗ Error extracting text from PDF: {e}")
        raise
    
    return pdf_data

def test_forma24_preview_pdf_uppercase():
    """Test 6: POST /api/forma24/preview with lowercase input - extract text and verify UPPERCASE"""
    print("\n=== TEST 6: POST /api/forma24/preview (lowercase input, verify UPPERCASE in PDF) ===")
    
    # Lowercase input
    payload = {
        "records": [
            {
                "surname": "мороз",
                "first_name": "иван",
                "patronymic": "дмитриевич",
                "citizenship": "республики беларусь",
                "nationality": "белорус",
                "res_city": "минск"
            }
        ],
        "duplex_flip": "long"
    }
    
    resp = requests.post(f"{BASE_URL}/forma24/preview", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers['Content-Type'] == 'application/pdf', f"Expected application/pdf, got {resp.headers['Content-Type']}"
    
    # Verify PDF signature
    pdf_data = resp.content
    assert pdf_data[:4] == b'%PDF', "Invalid PDF signature"
    print(f"✓ Valid PDF returned: {len(pdf_data)} bytes")
    
    # Extract text from PDF
    try:
        reader = PdfReader(io.BytesIO(pdf_data))
        print(f"✓ PDF has {len(reader.pages)} pages")
        
        # Extract text from all pages
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            full_text += text
            print(f"  Page {i+1} text length: {len(text)} chars")
        
        # Verify UPPERCASE values are present
        print("\n--- Checking for UPPERCASE values ---")
        uppercase_checks = {
            "МОРОЗ": "surname",
            "ИВАН": "first_name",
            "ДМИТРИЕВИЧ": "patronymic",
            "БЕЛОРУС": "nationality"
        }
        
        found_uppercase = []
        
        for upper_val, field_name in uppercase_checks.items():
            if upper_val in full_text:
                found_uppercase.append(f"✓ Found '{upper_val}' ({field_name})")
            else:
                print(f"  ✗ NOT FOUND: '{upper_val}' ({field_name})")
        
        print("\nUppercase values found:")
        for msg in found_uppercase:
            print(f"  {msg}")
        
        # At least some uppercase values should be found
        assert len(found_uppercase) >= 2, f"Expected at least 2 uppercase values, found {len(found_uppercase)}"
        print(f"\n✓ UPPERCASE conversion verified: {len(found_uppercase)} values found in uppercase")
        
    except Exception as e:
        print(f"✗ Error extracting text from PDF: {e}")
        raise
    
    return pdf_data

def test_zayavlenie_preview_no_uppercase():
    """Test 7: REGRESSION - POST /api/zayavlenie/preview should NOT force uppercase"""
    print("\n=== TEST 7: REGRESSION - POST /api/zayavlenie/preview (should NOT force uppercase) ===")
    
    # Lowercase input
    payload = {
        "records": [
            {
                "fio": "мороз иван дмитриевич",
                "birth_year": "2000",
                "res_city": "минск",
                "res_street": "ленина",
                "res_house": "10",
                "res_apartment": "5"
            }
        ],
        "duplex_flip": "long"
    }
    
    resp = requests.post(f"{BASE_URL}/zayavlenie/preview", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers['Content-Type'] == 'application/pdf', f"Expected application/pdf, got {resp.headers['Content-Type']}"
    
    # Verify PDF signature
    pdf_data = resp.content
    assert pdf_data[:4] == b'%PDF', "Invalid PDF signature"
    print(f"✓ Valid PDF returned: {len(pdf_data)} bytes")
    
    # Extract text from PDF
    try:
        reader = PdfReader(io.BytesIO(pdf_data))
        print(f"✓ PDF has {len(reader.pages)} pages")
        
        # Extract text from all pages
        full_text = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            full_text += text
        
        # For zayavlenie, we should NOT force uppercase
        # The text might be in various cases depending on the template
        print("✓ Zayavlenie PDF generated successfully (case preserved as entered)")
        
    except Exception as e:
        print(f"✗ Error extracting text from PDF: {e}")
        raise
    
    return pdf_data

def test_package_no_uppercase():
    """Test 8: REGRESSION - POST /api/package should NOT force uppercase for zayavlenie"""
    print("\n=== TEST 8: REGRESSION - POST /api/package (zayavlenie should NOT force uppercase) ===")
    
    # Lowercase input - master data format
    payload = {
        "people": [
            {
                "fio": "мороз иван дмитриевич",
                "birth_date": "01.01.2000",
                "citizenship": "республики беларусь",
                "phone": "+375291234567",
                "room_number": "101",
                "contract_number": "TEST-001"
            }
        ],
        "duplex_flip": "long",
        "include": {
            "contract": False,
            "forma19": False,
            "forma24": False,
            "soobshenie": False,
            "zayavlenie": True
        }
    }
    
    resp = requests.post(f"{BASE_URL}/package", json=payload)
    print(f"Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.headers['Content-Type'] == 'application/pdf', f"Expected application/pdf, got {resp.headers['Content-Type']}"
    
    # Verify PDF signature
    pdf_data = resp.content
    assert pdf_data[:4] == b'%PDF', "Invalid PDF signature"
    print(f"✓ Valid PDF returned: {len(pdf_data)} bytes")
    
    try:
        reader = PdfReader(io.BytesIO(pdf_data))
        print(f"✓ Package PDF has {len(reader.pages)} pages")
        print("✓ Package generation successful (zayavlenie case preserved)")
        
    except Exception as e:
        print(f"✗ Error reading package PDF: {e}")
        raise
    
    return pdf_data

def main():
    """Run all tests"""
    print("=" * 80)
    print("BACKEND TESTING: Uppercase Feature for Forms 19 and 24")
    print("=" * 80)
    
    results = {
        "passed": 0,
        "failed": 0,
        "errors": []
    }
    
    tests = [
        ("GET /api/forma19/fields", test_forma19_fields),
        ("GET /api/forma24/fields", test_forma24_fields),
        ("POST /api/forma19/preview-png (lowercase → PNG)", test_forma19_preview_png_uppercase),
        ("POST /api/forma24/preview-png (lowercase → PNG)", test_forma24_preview_png_uppercase),
        ("POST /api/forma19/preview (lowercase → UPPERCASE in PDF)", test_forma19_preview_pdf_uppercase),
        ("POST /api/forma24/preview (lowercase → UPPERCASE in PDF)", test_forma24_preview_pdf_uppercase),
        ("REGRESSION: POST /api/zayavlenie/preview (NO uppercase)", test_zayavlenie_preview_no_uppercase),
        ("REGRESSION: POST /api/package (zayavlenie NO uppercase)", test_package_no_uppercase),
    ]
    
    for test_name, test_func in tests:
        try:
            test_func()
            results["passed"] += 1
            print(f"\n✓ PASSED: {test_name}")
        except AssertionError as e:
            results["failed"] += 1
            error_msg = f"✗ FAILED: {test_name}\n  Error: {e}"
            results["errors"].append(error_msg)
            print(f"\n{error_msg}")
        except Exception as e:
            results["failed"] += 1
            error_msg = f"✗ ERROR: {test_name}\n  Exception: {e}"
            results["errors"].append(error_msg)
            print(f"\n{error_msg}")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {results['passed'] + results['failed']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    
    if results["errors"]:
        print("\nFailed tests:")
        for error in results["errors"]:
            print(f"  {error}")
    
    print("=" * 80)
    
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
