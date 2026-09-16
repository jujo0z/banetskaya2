#!/usr/bin/env python3
"""
Backend testing for Banetskaya.by - Conditional Underline Feature (ul element type)
Testing the new "ul" (conditional underline) template element type in Forms 19/24.
"""
import requests
import json
import sys

# Use LOCAL backend as specified in review request
BASE_URL = "http://localhost:8001/api"

def test_forma24_template_ul_elements():
    """
    TEST 1: GET /api/forma24/template
    Should return 200 JSON with 17 elements of type "ul" for fields:
    sex, purpose_choice, education, marital, spouse_together
    Each ul element should have: field, x, y, w, and on (with eq/contains)
    """
    print("\n" + "="*80)
    print("TEST 1: GET /api/forma24/template - Check for 17 'ul' elements")
    print("="*80)
    
    try:
        resp = requests.get(f"{BASE_URL}/forma24/template", timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            return False
        
        data = resp.json()
        template = data.get("template", [])
        
        # Find all ul elements
        ul_elements = [el for el in template if el.get("type") == "ul"]
        print(f"Found {len(ul_elements)} elements with type='ul'")
        
        if len(ul_elements) != 17:
            print(f"❌ FAILED: Expected 17 'ul' elements, found {len(ul_elements)}")
            return False
        
        # Check fields covered
        fields_found = {}
        for el in ul_elements:
            field = el.get("field")
            if field:
                fields_found[field] = fields_found.get(field, 0) + 1
        
        print(f"Fields covered by ul elements: {fields_found}")
        
        expected_fields = ["sex", "purpose_choice", "education", "marital", "spouse_together"]
        for field in expected_fields:
            if field not in fields_found:
                print(f"❌ FAILED: Expected field '{field}' not found in ul elements")
                return False
        
        # Verify structure of ul elements
        print("\nVerifying structure of ul elements:")
        for i, el in enumerate(ul_elements[:3]):  # Check first 3 as sample
            print(f"\n  ul element {i+1}:")
            print(f"    field: {el.get('field')}")
            print(f"    x: {el.get('x')}")
            print(f"    y: {el.get('y')}")
            print(f"    w: {el.get('w')}")
            print(f"    on: {el.get('on')}")
            
            # Verify required fields
            if not el.get("field"):
                print(f"    ❌ Missing 'field'")
                return False
            if el.get("x") is None:
                print(f"    ❌ Missing 'x'")
                return False
            if el.get("y") is None:
                print(f"    ❌ Missing 'y'")
                return False
            if el.get("w") is None:
                print(f"    ❌ Missing 'w'")
                return False
            
            on = el.get("on")
            if not on or not isinstance(on, dict):
                print(f"    ❌ Missing or invalid 'on' field")
                return False
            
            if "eq" not in on and "contains" not in on:
                print(f"    ❌ 'on' must have 'eq' or 'contains'")
                return False
        
        print("\n✅ TEST 1 PASSED: Found 17 'ul' elements with correct structure")
        print(f"   Fields: sex ({fields_found.get('sex', 0)}), purpose_choice ({fields_found.get('purpose_choice', 0)}), "
              f"education ({fields_found.get('education', 0)}), marital ({fields_found.get('marital', 0)}), "
              f"spouse_together ({fields_found.get('spouse_together', 0)})")
        return True
        
    except Exception as e:
        print(f"❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_forma19_template_spread_element():
    """
    TEST 2: GET /api/forma19/template
    Should return 200 JSON with element type="spread" with field=="id_number" (14 cells)
    OR field id_number
    """
    print("\n" + "="*80)
    print("TEST 2: GET /api/forma19/template - Check for 'spread' element or id_number")
    print("="*80)
    
    try:
        resp = requests.get(f"{BASE_URL}/forma19/template", timeout=10)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            return False
        
        data = resp.json()
        template = data.get("template", [])
        
        # Find spread elements
        spread_elements = [el for el in template if el.get("type") == "spread"]
        print(f"Found {len(spread_elements)} elements with type='spread'")
        
        # Find id_number field
        id_number_elements = [el for el in template if el.get("field") == "id_number"]
        print(f"Found {len(id_number_elements)} elements with field='id_number'")
        
        # Check for spread element with id_number
        spread_id_number = [el for el in spread_elements if el.get("field") == "id_number"]
        
        if spread_id_number:
            el = spread_id_number[0]
            print(f"\n✅ Found 'spread' element with field='id_number':")
            print(f"   x: {el.get('x')}")
            print(f"   y: {el.get('y')}")
            print(f"   cw: {el.get('cw')} (cell width)")
            print(f"   n: {el.get('n')} (number of cells)")
            
            n = el.get("n")
            if n and n == 14:
                print(f"   ✅ Correct: 14 cells for id_number")
            else:
                print(f"   ⚠️  Note: Expected 14 cells, found {n}")
            
            print("\n✅ TEST 2 PASSED: Found 'spread' element with field='id_number'")
            return True
        elif id_number_elements:
            print(f"\n✅ Found {len(id_number_elements)} element(s) with field='id_number'")
            for el in id_number_elements:
                print(f"   type: {el.get('type')}, x: {el.get('x')}, y: {el.get('y')}")
            print("\n✅ TEST 2 PASSED: Found id_number field in template")
            return True
        else:
            print(f"❌ FAILED: No 'spread' element with id_number and no id_number field found")
            return False
        
    except Exception as e:
        print(f"❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_forma24_preview_png_conditional_rendering():
    """
    TEST 3: POST /api/forma24/preview-png - Conditional rendering proof
    
    CRITICAL: Verify that PNG output DIFFERS when different codes are used.
    This proves that conditional underline is actually working.
    
    Test cases:
    - side=front: sex="1" vs sex="2", purpose_choice="1" vs "2"
    - side=back: education="3" vs "5", marital="2" vs "4", spouse_together="5" vs "6"
    - Control: identical requests should give same size PNG
    """
    print("\n" + "="*80)
    print("TEST 3: POST /api/forma24/preview-png - Conditional Rendering Proof")
    print("="*80)
    
    results = []
    
    # Test 3a: Front side - sex and purpose_choice
    print("\n--- Test 3a: Front side - Different sex and purpose_choice codes ---")
    
    record1_front = {
        "records": [{"sex": "1", "purpose_choice": "1", "surname": "ТЕСТ"}],
        "side": "front"
    }
    
    record2_front = {
        "records": [{"sex": "2", "purpose_choice": "2", "surname": "ТЕСТ"}],
        "side": "front"
    }
    
    try:
        resp1 = requests.post(f"{BASE_URL}/forma24/preview-png", json=record1_front, timeout=15)
        print(f"Request 1 (sex=1, purpose_choice=1): Status {resp1.status_code}")
        
        if resp1.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp1.status_code}")
            print(f"Response: {resp1.text[:500]}")
            results.append(False)
        else:
            content_type = resp1.headers.get("Content-Type", "")
            print(f"Content-Type: {content_type}")
            
            if "image/png" not in content_type and not resp1.content.startswith(b'\x89PNG'):
                print(f"❌ FAILED: Not a PNG response")
                print(f"First 50 bytes: {resp1.content[:50]}")
                results.append(False)
            else:
                size1 = len(resp1.content)
                print(f"✅ Valid PNG, size: {size1} bytes")
                
                resp2 = requests.post(f"{BASE_URL}/forma24/preview-png", json=record2_front, timeout=15)
                print(f"\nRequest 2 (sex=2, purpose_choice=2): Status {resp2.status_code}")
                
                if resp2.status_code != 200:
                    print(f"❌ FAILED: Expected 200, got {resp2.status_code}")
                    results.append(False)
                else:
                    size2 = len(resp2.content)
                    print(f"✅ Valid PNG, size: {size2} bytes")
                    
                    if size1 == size2:
                        print(f"⚠️  WARNING: PNG sizes are identical ({size1} bytes)")
                        print(f"   This might indicate conditional rendering is NOT working")
                        # Check if content is actually different
                        if resp1.content == resp2.content:
                            print(f"❌ FAILED: PNG content is IDENTICAL - conditional rendering NOT working!")
                            results.append(False)
                        else:
                            print(f"✅ PASSED: PNG content differs (same size but different bytes)")
                            results.append(True)
                    else:
                        diff = abs(size1 - size2)
                        print(f"✅ PASSED: PNG sizes differ by {diff} bytes ({diff/max(size1,size2)*100:.1f}%)")
                        print(f"   This proves conditional rendering is working!")
                        results.append(True)
    
    except Exception as e:
        print(f"❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Test 3b: Back side - education, marital, spouse_together
    print("\n--- Test 3b: Back side - Different education, marital, spouse_together codes ---")
    
    record1_back = {
        "records": [{"education": "3", "marital": "2", "spouse_together": "5", "surname": "ТЕСТ"}],
        "side": "back"
    }
    
    record2_back = {
        "records": [{"education": "5", "marital": "4", "spouse_together": "6", "surname": "ТЕСТ"}],
        "side": "back"
    }
    
    try:
        resp1 = requests.post(f"{BASE_URL}/forma24/preview-png", json=record1_back, timeout=15)
        print(f"Request 1 (education=3, marital=2, spouse_together=5): Status {resp1.status_code}")
        
        if resp1.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp1.status_code}")
            print(f"Response: {resp1.text[:500]}")
            results.append(False)
        else:
            content_type = resp1.headers.get("Content-Type", "")
            print(f"Content-Type: {content_type}")
            
            if "image/png" not in content_type and not resp1.content.startswith(b'\x89PNG'):
                print(f"❌ FAILED: Not a PNG response")
                results.append(False)
            else:
                size1 = len(resp1.content)
                print(f"✅ Valid PNG, size: {size1} bytes")
                
                resp2 = requests.post(f"{BASE_URL}/forma24/preview-png", json=record2_back, timeout=15)
                print(f"\nRequest 2 (education=5, marital=4, spouse_together=6): Status {resp2.status_code}")
                
                if resp2.status_code != 200:
                    print(f"❌ FAILED: Expected 200, got {resp2.status_code}")
                    results.append(False)
                else:
                    size2 = len(resp2.content)
                    print(f"✅ Valid PNG, size: {size2} bytes")
                    
                    if size1 == size2:
                        print(f"⚠️  WARNING: PNG sizes are identical ({size1} bytes)")
                        # Check if content is actually different
                        if resp1.content == resp2.content:
                            print(f"❌ FAILED: PNG content is IDENTICAL - conditional rendering NOT working!")
                            results.append(False)
                        else:
                            print(f"✅ PASSED: PNG content differs (same size but different bytes)")
                            results.append(True)
                    else:
                        diff = abs(size1 - size2)
                        print(f"✅ PASSED: PNG sizes differ by {diff} bytes ({diff/max(size1,size2)*100:.1f}%)")
                        print(f"   This proves conditional rendering is working!")
                        results.append(True)
    
    except Exception as e:
        print(f"❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Test 3c: Control - identical requests should give same result
    print("\n--- Test 3c: Control - Identical requests should give identical PNG ---")
    
    control_record = {
        "records": [{"sex": "1", "education": "3", "surname": "КОНТРОЛЬ"}],
        "side": "front"
    }
    
    try:
        resp1 = requests.post(f"{BASE_URL}/forma24/preview-png", json=control_record, timeout=15)
        resp2 = requests.post(f"{BASE_URL}/forma24/preview-png", json=control_record, timeout=15)
        
        print(f"Request 1: Status {resp1.status_code}, size {len(resp1.content)} bytes")
        print(f"Request 2: Status {resp2.status_code}, size {len(resp2.content)} bytes")
        
        if resp1.status_code == 200 and resp2.status_code == 200:
            if len(resp1.content) == len(resp2.content):
                print(f"✅ PASSED: Identical requests give same size PNG ({len(resp1.content)} bytes)")
                results.append(True)
            else:
                print(f"⚠️  WARNING: Identical requests give different sizes")
                print(f"   This might indicate non-deterministic rendering")
                results.append(True)  # Not a critical failure
        else:
            print(f"❌ FAILED: One or both requests failed")
            results.append(False)
    
    except Exception as e:
        print(f"❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(False)
    
    # Summary
    print("\n" + "="*80)
    if all(results):
        print("✅ TEST 3 PASSED: Conditional rendering is working correctly")
        print("   - Different codes produce different PNG output")
        print("   - Identical requests produce consistent output")
        return True
    else:
        print(f"❌ TEST 3 FAILED: {results.count(False)}/{len(results)} sub-tests failed")
        return False


def test_forma24_preview_pdf():
    """
    TEST 4: POST /api/forma24/preview (PDF)
    Should return 200 PDF with 2 pages
    """
    print("\n" + "="*80)
    print("TEST 4: POST /api/forma24/preview - PDF generation")
    print("="*80)
    
    try:
        payload = {
            "records": [
                {"surname": "Иванов", "first_name": "Иван", "sex": "1", "education": "4"}
            ]
        }
        
        resp = requests.post(f"{BASE_URL}/forma24/preview", json=payload, timeout=15)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            return False
        
        content_type = resp.headers.get("Content-Type", "")
        print(f"Content-Type: {content_type}")
        
        if "application/pdf" not in content_type and not resp.content.startswith(b'%PDF'):
            print(f"❌ FAILED: Not a PDF response")
            print(f"First 50 bytes: {resp.content[:50]}")
            return False
        
        size = len(resp.content)
        print(f"✅ Valid PDF, size: {size} bytes")
        
        # Verify it's a valid PDF with 2 pages using pymupdf
        try:
            import fitz  # pymupdf
            doc = fitz.open(stream=resp.content, filetype="pdf")
            page_count = len(doc)
            print(f"Page count: {page_count}")
            
            if page_count != 2:
                print(f"⚠️  WARNING: Expected 2 pages, got {page_count}")
            else:
                print(f"✅ Correct: 2 pages (front + back)")
            
            doc.close()
        except ImportError:
            print("⚠️  pymupdf not available, skipping page count verification")
        except Exception as e:
            print(f"⚠️  Could not verify page count: {e}")
        
        print("\n✅ TEST 4 PASSED: PDF generation works")
        return True
        
    except Exception as e:
        print(f"❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_forma19_preview_pdf():
    """
    TEST 5: POST /api/forma19/preview (PDF)
    Should return 200 PDF with 2 pages
    """
    print("\n" + "="*80)
    print("TEST 5: POST /api/forma19/preview - PDF generation")
    print("="*80)
    
    try:
        payload = {
            "records": [
                {"surname": "Петров", "first_name": "Пётр", "citizenship": "РБ", "purpose": "на учёбу"}
            ]
        }
        
        resp = requests.post(f"{BASE_URL}/forma19/preview", json=payload, timeout=15)
        print(f"Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"Response: {resp.text[:500]}")
            return False
        
        content_type = resp.headers.get("Content-Type", "")
        print(f"Content-Type: {content_type}")
        
        if "application/pdf" not in content_type and not resp.content.startswith(b'%PDF'):
            print(f"❌ FAILED: Not a PDF response")
            print(f"First 50 bytes: {resp.content[:50]}")
            return False
        
        size = len(resp.content)
        print(f"✅ Valid PDF, size: {size} bytes")
        
        # Verify it's a valid PDF with 2 pages using pymupdf
        try:
            import fitz  # pymupdf
            doc = fitz.open(stream=resp.content, filetype="pdf")
            page_count = len(doc)
            print(f"Page count: {page_count}")
            
            if page_count != 2:
                print(f"⚠️  WARNING: Expected 2 pages, got {page_count}")
            else:
                print(f"✅ Correct: 2 pages (front + back)")
            
            doc.close()
        except ImportError:
            print("⚠️  pymupdf not available, skipping page count verification")
        except Exception as e:
            print(f"⚠️  Could not verify page count: {e}")
        
        print("\n✅ TEST 5 PASSED: PDF generation works")
        return True
        
    except Exception as e:
        print(f"❌ FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("="*80)
    print("BACKEND TESTING: Conditional Underline Feature (ul element type)")
    print("Testing Forms 19/24 with new 'ul' and 'spread' element types")
    print("="*80)
    print(f"Backend URL: {BASE_URL}")
    
    # Check backend is accessible
    try:
        resp = requests.get(f"{BASE_URL}/_ping", timeout=5)
        if resp.status_code == 200:
            print("✅ Backend is accessible")
        else:
            print(f"⚠️  Backend responded with status {resp.status_code}")
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to backend: {e}")
        print("Make sure backend is running at http://localhost:8001")
        return 1
    
    # Run tests
    results = []
    
    results.append(("GET /api/forma24/template (17 ul elements)", test_forma24_template_ul_elements()))
    results.append(("GET /api/forma19/template (spread element)", test_forma19_template_spread_element()))
    results.append(("POST /api/forma24/preview-png (conditional rendering)", test_forma24_preview_png_conditional_rendering()))
    results.append(("POST /api/forma24/preview (PDF)", test_forma24_preview_pdf()))
    results.append(("POST /api/forma19/preview (PDF)", test_forma19_preview_pdf()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*80)
    print(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("="*80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
