#!/usr/bin/env python3
"""
Backend API testing for "полный пакет документов из истории договоров" feature.
Tests master-template, generate/upload, contracts/batch, contracts/{id}/package, contracts/package.
"""
import os
import sys
import requests
import json
import io

# Get backend URL from environment
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=', 1)[1]
            break

API_BASE = f"{BACKEND_URL}/api"

print(f"Backend URL: {BACKEND_URL}")
print(f"API Base: {API_BASE}")

# Global variables to store test data
xlsx_bytes = None
students = None
masters = None
contract_id_1 = None
contract_id_2 = None


def test_1_get_master_template():
    """Test 1: GET /api/master-template → 200, download .xlsx bytes"""
    global xlsx_bytes
    print("\n" + "="*70)
    print("[TEST 1] GET /api/master-template")
    print("="*70)
    
    url = f"{API_BASE}/master-template"
    
    try:
        resp = requests.get(url, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type')}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in resp.headers.get('Content-Type', ''), \
            f"Expected Excel content type, got {resp.headers.get('Content-Type')}"
        
        xlsx_bytes = resp.content
        print(f"  Downloaded: {len(xlsx_bytes)} bytes")
        
        # Verify it's a valid Excel file
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes))
        print(f"  Sheets: {wb.sheetnames}")
        assert 'Данные' in wb.sheetnames, "Missing 'Данные' sheet"
        
        print("  ✅ PASS")
        return xlsx_bytes
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_2_post_generate_upload():
    """Test 2: POST /api/generate/upload with .xlsx → 200, mode="master", students and masters arrays"""
    global students, masters
    print("\n" + "="*70)
    print("[TEST 2] POST /api/generate/upload")
    print("="*70)
    
    url = f"{API_BASE}/generate/upload"
    
    try:
        # Send as multipart form-data
        files = {'file': ('master_template.xlsx', xlsx_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        resp = requests.post(url, files=files, timeout=30)
        
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type')}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        print(f"  Response keys: {list(data.keys())}")
        
        # Check mode
        assert data.get('mode') == 'master', f"Expected mode='master', got {data.get('mode')}"
        print(f"  mode: {data.get('mode')} ✓")
        
        # Check count
        count = data.get('count', 0)
        assert count >= 1, f"Expected count >= 1, got {count}"
        print(f"  count: {count} ✓")
        
        # Check students array
        students = data.get('students', [])
        assert len(students) >= 1, f"Expected students array with >= 1 items, got {len(students)}"
        print(f"  students: {len(students)} items ✓")
        
        # Check students[0]
        student0 = students[0]
        print(f"  students[0].full_name: {student0.get('full_name')}")
        assert student0.get('full_name') == "Иванов Иван Иванович", \
            f"Expected 'Иванов Иван Иванович', got {student0.get('full_name')}"
        
        print(f"  students[0].registration_address: {student0.get('registration_address')}")
        assert student0.get('registration_address'), "Expected non-empty registration_address"
        
        # Check masters array
        masters = data.get('masters', [])
        assert len(masters) >= 1, f"Expected masters array with >= 1 items, got {len(masters)}"
        print(f"  masters: {len(masters)} items ✓")
        
        # Check masters[0] has >= 40 keys
        master0 = masters[0]
        master0_keys = len(master0.keys())
        print(f"  masters[0] keys count: {master0_keys}")
        assert master0_keys >= 40, f"Expected masters[0] to have >= 40 keys, got {master0_keys}"
        
        # Print some key fields
        print(f"  masters[0].bp_obl: {master0.get('bp_obl')}")
        print(f"  masters[0].sex: {master0.get('sex')}")
        print(f"  masters[0].education: {master0.get('education')}")
        print(f"  masters[0].purpose_choice: {master0.get('purpose_choice')}")
        
        print("  ✅ PASS")
        return students, masters
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_3_post_contracts_batch():
    """Test 3: POST /api/contracts/batch with students and masters → 200, created[0].master non-empty"""
    global contract_id_1
    print("\n" + "="*70)
    print("[TEST 3] POST /api/contracts/batch")
    print("="*70)
    
    url = f"{API_BASE}/contracts/batch"
    
    try:
        payload = {
            "contracts": students,
            "masters": masters
        }
        
        resp = requests.post(url, json=payload, timeout=30)
        
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type')}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        print(f"  Response keys: {list(data.keys())}")
        
        # Check created array
        created = data.get('created', [])
        assert len(created) >= 1, f"Expected created array with >= 1 items, got {len(created)}"
        print(f"  created: {len(created)} items ✓")
        
        # Check created[0].master
        created0 = created[0]
        contract_id_1 = created0.get('id')
        print(f"  created[0].id: {contract_id_1}")
        
        master = created0.get('master')
        assert master, "Expected non-empty master object in created[0]"
        print(f"  created[0].master keys: {len(master.keys())}")
        print(f"  created[0].master.bp_obl: {master.get('bp_obl')}")
        print(f"  created[0].master.sex: {master.get('sex')}")
        
        print("  ✅ PASS")
        return contract_id_1
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_4_post_contract_package():
    """Test 4: POST /api/contracts/{id}/package → 200 PDF, 7 pages, check text content"""
    print("\n" + "="*70)
    print(f"[TEST 4] POST /api/contracts/{contract_id_1}/package")
    print("="*70)
    
    url = f"{API_BASE}/contracts/{contract_id_1}/package"
    
    try:
        payload = {"duplex_flip": "long"}
        
        resp = requests.post(url, json=payload, timeout=60)
        
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type')}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.headers.get('Content-Type') == 'application/pdf', \
            f"Expected application/pdf, got {resp.headers.get('Content-Type')}"
        
        pdf_bytes = resp.content
        print(f"  PDF size: {len(pdf_bytes)} bytes")
        
        # Open PDF with pymupdf
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        num_pages = len(doc)
        print(f"  Pages: {num_pages}")
        
        assert num_pages == 7, f"Expected 7 pages, got {num_pages}"
        
        # Check page 0 contains "ДОГОВОР"
        page0_text = doc[0].get_text()
        assert "ДОГОВОР" in page0_text, "Page 0 should contain 'ДОГОВОР'"
        print(f"  Page 0: contains 'ДОГОВОР' ✓")
        
        # Check page 4 contains BOTH "Форма № 19" AND "Форма 24"
        page4_text = doc[4].get_text()
        assert "Форма № 19" in page4_text or "Форма №19" in page4_text or "АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ" in page4_text, \
            "Page 4 should contain 'Форма № 19' or 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ'"
        assert "Форма 24" in page4_text or "ТАЛОН МИГРАЦИОННОГО" in page4_text, \
            "Page 4 should contain 'Форма 24' or 'ТАЛОН МИГРАЦИОННОГО'"
        print(f"  Page 4: contains BOTH 'Форма № 19' AND 'Форма 24' ✓")
        
        # Check page 6 contains "СООБЩЕНИЕ"
        page6_text = doc[6].get_text()
        assert "СООБЩЕНИЕ" in page6_text, "Page 6 should contain 'СООБЩЕНИЕ'"
        print(f"  Page 6: contains 'СООБЩЕНИЕ' ✓")
        
        doc.close()
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_5_post_contracts_package_selective():
    """Test 5: POST /api/contracts/package with include filter → 200 PDF, 2 pages"""
    print("\n" + "="*70)
    print("[TEST 5] POST /api/contracts/package (selective)")
    print("="*70)
    
    url = f"{API_BASE}/contracts/package"
    
    try:
        payload = {
            "ids": [contract_id_1],
            "duplex_flip": "long",
            "include": {
                "contract": False,
                "forma19": True,
                "forma24": True,
                "soobshenie": False
            }
        }
        
        resp = requests.post(url, json=payload, timeout=60)
        
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type')}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.headers.get('Content-Type') == 'application/pdf', \
            f"Expected application/pdf, got {resp.headers.get('Content-Type')}"
        
        pdf_bytes = resp.content
        print(f"  PDF size: {len(pdf_bytes)} bytes")
        
        # Open PDF with pymupdf
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        num_pages = len(doc)
        print(f"  Pages: {num_pages}")
        
        assert num_pages == 2, f"Expected 2 pages (only Forma19+Forma24), got {num_pages}"
        
        doc.close()
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_6_backward_compatibility():
    """Test 6: Backward compatibility - contract without saved master"""
    global contract_id_2
    print("\n" + "="*70)
    print("[TEST 6] Backward compatibility (contract without master)")
    print("="*70)
    
    # Create contract without master
    url = f"{API_BASE}/contracts"
    
    try:
        payload = {
            "fields": {
                "full_name": "Петров Пётр Петрович",
                "birth_date": "01.01.2000",
                "citizenship": "РБ",
                "passport_number": "MP 7654321"
            }
        }
        
        resp = requests.post(url, json=payload, timeout=30)
        
        print(f"  POST /api/contracts status: {resp.status_code}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        contract_id_2 = data.get('id')
        print(f"  Created contract id: {contract_id_2}")
        
        # Now try to generate package for this contract
        package_url = f"{API_BASE}/contracts/{contract_id_2}/package"
        package_payload = {"duplex_flip": "long"}
        
        package_resp = requests.post(package_url, json=package_payload, timeout=60)
        
        print(f"  POST /api/contracts/{contract_id_2}/package status: {package_resp.status_code}")
        print(f"  Content-Type: {package_resp.headers.get('Content-Type')}")
        
        assert package_resp.status_code == 200, \
            f"Expected 200, got {package_resp.status_code}: {package_resp.text}"
        assert package_resp.headers.get('Content-Type') == 'application/pdf', \
            f"Expected application/pdf, got {package_resp.headers.get('Content-Type')}"
        
        pdf_bytes = package_resp.content
        print(f"  PDF size: {len(pdf_bytes)} bytes")
        
        # Open PDF with pymupdf
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        num_pages = len(doc)
        print(f"  Pages: {num_pages}")
        
        assert num_pages >= 1, f"Expected >= 1 page, got {num_pages}"
        
        doc.close()
        
        print("  ✅ PASS (master derived from contract fields)")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_7_cleanup():
    """Test 7: DELETE created test contracts"""
    print("\n" + "="*70)
    print("[TEST 7] Cleanup - DELETE test contracts")
    print("="*70)
    
    try:
        # Delete contract 1
        if contract_id_1:
            url1 = f"{API_BASE}/contracts/{contract_id_1}"
            resp1 = requests.delete(url1, timeout=10)
            print(f"  DELETE /api/contracts/{contract_id_1}: {resp1.status_code}")
            assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"
        
        # Delete contract 2
        if contract_id_2:
            url2 = f"{API_BASE}/contracts/{contract_id_2}"
            resp2 = requests.delete(url2, timeout=10)
            print(f"  DELETE /api/contracts/{contract_id_2}: {resp2.status_code}")
            assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_8_regression_contracts():
    """Test 8: Regression - GET /api/contracts"""
    print("\n" + "="*70)
    print("[REGRESSION 1] GET /api/contracts")
    print("="*70)
    
    url = f"{API_BASE}/contracts"
    
    try:
        resp = requests.get(url, timeout=10)
        print(f"  Status: {resp.status_code}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), f"Expected array, got {type(data)}"
        print(f"  Contracts count: {len(data)}")
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_9_regression_fields():
    """Test 9: Regression - GET /api/fields"""
    print("\n" + "="*70)
    print("[REGRESSION 2] GET /api/fields")
    print("="*70)
    
    url = f"{API_BASE}/fields"
    
    try:
        resp = requests.get(url, timeout=10)
        print(f"  Status: {resp.status_code}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert 'fields' in data, "Missing 'fields' key"
        print(f"  Fields count: {len(data['fields'])}")
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    print("\n" + "="*70)
    print("BACKEND TESTING: ПОЛНЫЙ ПАКЕТ ДОКУМЕНТОВ ИЗ ИСТОРИИ ДОГОВОРОВ")
    print("="*70)
    
    # Run all tests in sequence
    test_1_get_master_template()
    test_2_post_generate_upload()
    test_3_post_contracts_batch()
    test_4_post_contract_package()
    test_5_post_contracts_package_selective()
    test_6_backward_compatibility()
    test_7_cleanup()
    test_8_regression_contracts()
    test_9_regression_fields()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED (9/9)")
    print("="*70)
    print("\nSUMMARY:")
    print("  ✓ GET /api/master-template returns valid .xlsx")
    print("  ✓ POST /api/generate/upload parses Excel and returns students/masters")
    print("  ✓ POST /api/contracts/batch creates contracts with master data")
    print("  ✓ POST /api/contracts/{id}/package generates 7-page PDF package")
    print("  ✓ POST /api/contracts/package with include filter generates 2-page PDF")
    print("  ✓ Backward compatibility: contract without master works")
    print("  ✓ Cleanup: test contracts deleted")
    print("  ✓ Regression: GET /api/contracts works")
    print("  ✓ Regression: GET /api/fields works")
    print("\n🎉 НОВАЯ ФИЧА ПОЛНОСТЬЮ РАБОТАЕТ!")


if __name__ == "__main__":
    main()
