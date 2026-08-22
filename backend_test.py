#!/usr/bin/env python3
"""
Backend testing for desktop version/updates endpoints + regression tests.
Tests:
NEW ENDPOINTS:
1. GET /api/app-version - version info (cloud: is_desktop=false, version="dev", repo="")
2. GET /api/updates/check - update check (cloud: supported=false, error present)
3. POST /api/updates/apply - apply update (cloud: 400 - only in installed app)

REGRESSION (critical functionality):
4. GET /api/contracts - list contracts
5. POST /api/overlay/generate - batch blank generation (147×103 mm)
6. GET /api/overlay/form-background - form background PNG
7. GET/POST /api/reg-profile - registration organ profile
8. GET /api/stats - statistics
9. GET /api/sample-template - Excel sample (if exists)
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

# Test counters
tests_passed = 0
tests_failed = 0
test_results = []

def log_result(test_name, passed, message=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        status = "✅ PASS"
    else:
        tests_failed += 1
        status = "❌ FAIL"
    result = f"{status}: {test_name}"
    if message:
        result += f" - {message}"
    print(result)
    test_results.append(result)

# ========== NEW ENDPOINTS ==========

def test_app_version():
    """Test 1: GET /api/app-version
    Expected in cloud: 200 JSON with keys version, build_time, git_sha, repo, is_desktop
    is_desktop=false, version="dev", repo=""
    """
    print("\n=== TEST 1: GET /api/app-version ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/app-version")
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            log_result("GET /api/app-version", False, f"Expected 200, got {response.status_code}")
            return
        
        data = response.json()
        print(f"Response: {data}")
        
        # Check required keys
        required_keys = ["version", "build_time", "git_sha", "repo", "is_desktop"]
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            log_result("GET /api/app-version", False, f"Missing keys: {missing_keys}")
            return
        
        # Check cloud-specific values
        if data.get("is_desktop") != False:
            log_result("GET /api/app-version", False, f"Expected is_desktop=false, got {data.get('is_desktop')}")
            return
        
        if data.get("version") != "dev":
            log_result("GET /api/app-version", False, f"Expected version='dev', got {data.get('version')}")
            return
        
        if data.get("repo") != "":
            log_result("GET /api/app-version", False, f"Expected repo='', got {data.get('repo')}")
            return
        
        log_result("GET /api/app-version", True, f"All keys present, is_desktop=false, version='dev', repo=''")
        
    except Exception as e:
        log_result("GET /api/app-version", False, f"Exception: {e}")

def test_updates_check():
    """Test 2: GET /api/updates/check
    Expected in cloud: 200 JSON with supported=false, current_version="dev", 
    update_available=false, error field present (repo not set)
    """
    print("\n=== TEST 2: GET /api/updates/check ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/updates/check")
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            log_result("GET /api/updates/check", False, f"Expected 200, got {response.status_code}")
            return
        
        data = response.json()
        print(f"Response: {data}")
        
        # Check required fields
        if data.get("supported") != False:
            log_result("GET /api/updates/check", False, f"Expected supported=false, got {data.get('supported')}")
            return
        
        if data.get("current_version") != "dev":
            log_result("GET /api/updates/check", False, f"Expected current_version='dev', got {data.get('current_version')}")
            return
        
        if data.get("update_available") != False:
            log_result("GET /api/updates/check", False, f"Expected update_available=false, got {data.get('update_available')}")
            return
        
        # Check error field is present (repo not set)
        if "error" not in data:
            log_result("GET /api/updates/check", False, "Expected 'error' field to be present (repo not set)")
            return
        
        log_result("GET /api/updates/check", True, f"supported=false, current_version='dev', update_available=false, error present: '{data.get('error')}'")
        
    except Exception as e:
        log_result("GET /api/updates/check", False, f"Exception: {e}")

def test_updates_apply():
    """Test 3: POST /api/updates/apply
    Expected in cloud: 400 (detail about "only in installed app")
    """
    print("\n=== TEST 3: POST /api/updates/apply ===")
    
    try:
        response = requests.post(f"{BACKEND_URL}/updates/apply", json={})
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 400:
            log_result("POST /api/updates/apply", False, f"Expected 400, got {response.status_code}")
            return
        
        data = response.json()
        print(f"Response: {data}")
        
        # Check detail message
        detail = data.get("detail", "")
        if "установленном" not in detail.lower() or "приложении" not in detail.lower():
            log_result("POST /api/updates/apply", False, f"Expected detail about 'installed app', got: {detail}")
            return
        
        log_result("POST /api/updates/apply", True, f"400 with correct detail: '{detail}'")
        
    except Exception as e:
        log_result("POST /api/updates/apply", False, f"Exception: {e}")

# ========== REGRESSION TESTS ==========

def test_contracts_list():
    """Test 4: GET /api/contracts
    Expected: 200, list (array)
    """
    print("\n=== TEST 4: GET /api/contracts (REGRESSION) ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/contracts")
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            log_result("GET /api/contracts", False, f"Expected 200, got {response.status_code}")
            return
        
        data = response.json()
        
        if not isinstance(data, list):
            log_result("GET /api/contracts", False, f"Expected list/array, got {type(data)}")
            return
        
        print(f"Response: list with {len(data)} items")
        log_result("GET /api/contracts", True, f"Returns list with {len(data)} contracts")
        
    except Exception as e:
        log_result("GET /api/contracts", False, f"Exception: {e}")

def test_overlay_generate():
    """Test 5: POST /api/overlay/generate
    Expected: 200 application/pdf, page 147×103 mm (416.69×291.97 pt)
    """
    print("\n=== TEST 5: POST /api/overlay/generate (REGRESSION) ===")
    
    try:
        payload = {
            "records": [{"fio": "Тестовый Гражданин"}],
            "page_size": "card",
            "with_form": True
        }
        
        response = requests.post(f"{BACKEND_URL}/overlay/generate", json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            log_result("POST /api/overlay/generate", False, f"Expected 200, got {response.status_code}")
            return
        
        if "application/pdf" not in response.headers.get('Content-Type', ''):
            log_result("POST /api/overlay/generate", False, f"Expected Content-Type application/pdf")
            return
        
        # Check PDF validity and page size
        pdf_bytes = response.content
        if not pdf_bytes.startswith(b'%PDF'):
            log_result("POST /api/overlay/generate", False, "PDF does not start with %PDF")
            return
        
        # Check page size with pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) == 0:
            log_result("POST /api/overlay/generate", False, "PDF has 0 pages")
            doc.close()
            return
        
        page = doc[0]
        rect = page.rect
        width_pt = rect.width
        height_pt = rect.height
        
        print(f"Page size: {width_pt:.2f} × {height_pt:.2f} pt")
        
        width_ok = abs(width_pt - CARD_WIDTH_PT) <= TOLERANCE_PT
        height_ok = abs(height_pt - CARD_HEIGHT_PT) <= TOLERANCE_PT
        
        doc.close()
        
        if not (width_ok and height_ok):
            log_result("POST /api/overlay/generate", False, 
                      f"Page size {width_pt:.2f}×{height_pt:.2f} pt not within tolerance of {CARD_WIDTH_PT}×{CARD_HEIGHT_PT} pt")
            return
        
        log_result("POST /api/overlay/generate", True, 
                  f"Valid PDF, page size {width_pt:.2f}×{height_pt:.2f} pt (147×103 mm)")
        
    except Exception as e:
        log_result("POST /api/overlay/generate", False, f"Exception: {e}")

def test_overlay_form_background():
    """Test 6: GET /api/overlay/form-background
    Expected: 200 image/png
    """
    print("\n=== TEST 6: GET /api/overlay/form-background (REGRESSION) ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/overlay/form-background")
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            log_result("GET /api/overlay/form-background", False, f"Expected 200, got {response.status_code}")
            return
        
        if "image/png" not in response.headers.get('Content-Type', ''):
            log_result("GET /api/overlay/form-background", False, f"Expected Content-Type image/png")
            return
        
        # Check PNG validity
        png_bytes = response.content
        if not png_bytes.startswith(b'\x89PNG'):
            log_result("GET /api/overlay/form-background", False, "PNG does not start with \\x89PNG")
            return
        
        print(f"PNG size: {len(png_bytes)} bytes")
        log_result("GET /api/overlay/form-background", True, f"Valid PNG, {len(png_bytes)} bytes")
        
    except Exception as e:
        log_result("GET /api/overlay/form-background", False, f"Exception: {e}")

def test_reg_profile_get():
    """Test 7a: GET /api/reg-profile
    Expected: 200 JSON
    """
    print("\n=== TEST 7a: GET /api/reg-profile (REGRESSION) ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/reg-profile")
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            log_result("GET /api/reg-profile", False, f"Expected 200, got {response.status_code}")
            return
        
        data = response.json()
        print(f"Response: {data}")
        
        log_result("GET /api/reg-profile", True, f"Returns JSON: {data}")
        
    except Exception as e:
        log_result("GET /api/reg-profile", False, f"Exception: {e}")

def test_reg_profile_post():
    """Test 7b: POST /api/reg-profile
    Expected: 200 {saved:true}
    """
    print("\n=== TEST 7b: POST /api/reg-profile (REGRESSION) ===")
    
    try:
        payload = {
            "reg_organ": "Тестовый Орган Регистрации",
            "chief": "Тестов Т.Т.",
            "city": "г. Тест"
        }
        
        response = requests.post(f"{BACKEND_URL}/reg-profile", json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            log_result("POST /api/reg-profile", False, f"Expected 200, got {response.status_code}")
            return
        
        data = response.json()
        print(f"Response: {data}")
        
        if data.get("saved") != True:
            log_result("POST /api/reg-profile", False, f"Expected saved=true, got {data.get('saved')}")
            return
        
        log_result("POST /api/reg-profile", True, f"saved=true, profile saved")
        
    except Exception as e:
        log_result("POST /api/reg-profile", False, f"Exception: {e}")

def test_stats():
    """Test 8: GET /api/stats
    Expected: 200 JSON
    """
    print("\n=== TEST 8: GET /api/stats (REGRESSION) ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/stats")
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code != 200:
            log_result("GET /api/stats", False, f"Expected 200, got {response.status_code}")
            return
        
        data = response.json()
        print(f"Response: {data}")
        
        # Check for expected keys
        expected_keys = ["total", "drafts", "this_month", "datasets", "recent"]
        missing_keys = [k for k in expected_keys if k not in data]
        if missing_keys:
            log_result("GET /api/stats", False, f"Missing keys: {missing_keys}")
            return
        
        log_result("GET /api/stats", True, f"Returns JSON with all expected keys")
        
    except Exception as e:
        log_result("GET /api/stats", False, f"Exception: {e}")

def test_sample_template():
    """Test 9: GET /api/sample-template
    Expected: 200 (xlsx) if endpoint exists, or 404 if not
    """
    print("\n=== TEST 9: GET /api/sample-template (REGRESSION) ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/sample-template")
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 404:
            log_result("GET /api/sample-template", True, "Endpoint not found (404) - acceptable")
            return
        
        if response.status_code != 200:
            log_result("GET /api/sample-template", False, f"Expected 200 or 404, got {response.status_code}")
            return
        
        # Check if it's an Excel file
        content_type = response.headers.get('Content-Type', '')
        if "spreadsheet" in content_type or "excel" in content_type:
            log_result("GET /api/sample-template", True, f"Returns Excel file, Content-Type: {content_type}")
        else:
            # Check if content starts with PK (ZIP signature for xlsx)
            if response.content.startswith(b'PK'):
                log_result("GET /api/sample-template", True, "Returns valid Excel file (starts with PK)")
            else:
                log_result("GET /api/sample-template", False, f"Unexpected Content-Type: {content_type}")
        
    except Exception as e:
        log_result("GET /api/sample-template", False, f"Exception: {e}")

# ========== MAIN ==========

def main():
    print("=" * 80)
    print("BACKEND TESTING: Desktop Version/Updates + Regression")
    print("=" * 80)
    
    # NEW ENDPOINTS
    print("\n" + "=" * 80)
    print("NEW ENDPOINTS (Desktop Version & Auto-Update)")
    print("=" * 80)
    test_app_version()
    test_updates_check()
    test_updates_apply()
    
    # REGRESSION TESTS
    print("\n" + "=" * 80)
    print("REGRESSION TESTS (Critical Functionality)")
    print("=" * 80)
    test_contracts_list()
    test_overlay_generate()
    test_overlay_form_background()
    test_reg_profile_get()
    test_reg_profile_post()
    test_stats()
    test_sample_template()
    
    # SUMMARY
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    total_tests = tests_passed + tests_failed
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print(f"Success Rate: {(tests_passed/total_tests*100):.1f}%")
    
    print("\n" + "=" * 80)
    print("DETAILED RESULTS")
    print("=" * 80)
    for result in test_results:
        print(result)
    
    if tests_failed > 0:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
