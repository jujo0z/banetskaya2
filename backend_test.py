#!/usr/bin/env python3
"""
Backend API Testing for Banetskaya.by Contract Generator
Tests the new GET /api/overlay/form-background endpoint and regression tests
"""

import os
import sys
import requests
import json
from io import BytesIO

# Backend URL from environment
BACKEND_URL = "https://1a44cbd3-e499-4c2e-b9f8-dd81fc5e4c75.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

def log_test(name, passed, details=""):
    """Log test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"  Details: {details}")
    
    test_results["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })
    
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1

def test_new_form_background_endpoint():
    """
    TEST 1: GET /api/overlay/form-background
    Should return 200, Content-Type: image/png, body starts with PNG signature, size > 1000 bytes
    """
    print("\n" + "="*80)
    print("TEST 1: GET /api/overlay/form-background (NEW ENDPOINT)")
    print("="*80)
    
    try:
        response = requests.get(f"{API_BASE}/overlay/form-background", timeout=30)
        
        # Check status code
        if response.status_code != 200:
            log_test(
                "GET /api/overlay/form-background - Status Code",
                False,
                f"Expected 200, got {response.status_code}"
            )
            return
        
        log_test("GET /api/overlay/form-background - Status Code", True, "200 OK")
        
        # Check Content-Type
        content_type = response.headers.get('Content-Type', '')
        if 'image/png' not in content_type:
            log_test(
                "GET /api/overlay/form-background - Content-Type",
                False,
                f"Expected 'image/png', got '{content_type}'"
            )
        else:
            log_test("GET /api/overlay/form-background - Content-Type", True, "image/png")
        
        # Check PNG signature (first 4 bytes should be \x89PNG)
        body = response.content
        if len(body) < 4:
            log_test(
                "GET /api/overlay/form-background - Body Size",
                False,
                f"Body too small: {len(body)} bytes"
            )
            return
        
        png_signature = body[:4]
        expected_signature = b'\x89PNG'
        if png_signature != expected_signature:
            log_test(
                "GET /api/overlay/form-background - PNG Signature",
                False,
                f"Expected {expected_signature.hex()}, got {png_signature.hex()}"
            )
        else:
            log_test("GET /api/overlay/form-background - PNG Signature", True, "Valid PNG (\\x89PNG)")
        
        # Check size > 1000 bytes
        body_size = len(body)
        if body_size <= 1000:
            log_test(
                "GET /api/overlay/form-background - Size > 1000 bytes",
                False,
                f"Expected > 1000 bytes, got {body_size} bytes"
            )
        else:
            log_test(
                "GET /api/overlay/form-background - Size > 1000 bytes",
                True,
                f"{body_size} bytes"
            )
        
    except Exception as e:
        log_test("GET /api/overlay/form-background", False, f"Exception: {str(e)}")

def test_regression_overlay_generate_card():
    """
    TEST 2: POST /api/overlay/generate with page_size=card, with_form=true
    Should return 200, Content-Type: application/pdf, valid PDF
    """
    print("\n" + "="*80)
    print("TEST 2: POST /api/overlay/generate (page_size=card, with_form=true) - REGRESSION")
    print("="*80)
    
    try:
        payload = {
            "records": [
                {
                    "fio": "Иванов Иван Иванович",
                    "passport_series": "МР",
                    "passport_number": "1234567",
                    "date_day": "5",
                    "date_year": "25"
                }
            ],
            "page_size": "card",
            "with_form": True
        }
        
        response = requests.post(
            f"{API_BASE}/overlay/generate",
            json=payload,
            timeout=30
        )
        
        # Check status code
        if response.status_code != 200:
            log_test(
                "POST /api/overlay/generate (card, with_form=true) - Status Code",
                False,
                f"Expected 200, got {response.status_code}. Response: {response.text[:200]}"
            )
            return
        
        log_test("POST /api/overlay/generate (card, with_form=true) - Status Code", True, "200 OK")
        
        # Check Content-Type
        content_type = response.headers.get('Content-Type', '')
        if 'application/pdf' not in content_type:
            log_test(
                "POST /api/overlay/generate (card, with_form=true) - Content-Type",
                False,
                f"Expected 'application/pdf', got '{content_type}'"
            )
        else:
            log_test("POST /api/overlay/generate (card, with_form=true) - Content-Type", True, "application/pdf")
        
        # Check PDF signature (should start with %PDF)
        body = response.content
        if not body.startswith(b'%PDF'):
            log_test(
                "POST /api/overlay/generate (card, with_form=true) - PDF Signature",
                False,
                f"Expected '%PDF', got '{body[:10]}'"
            )
        else:
            log_test(
                "POST /api/overlay/generate (card, with_form=true) - PDF Signature",
                True,
                f"Valid PDF (%PDF), size: {len(body)} bytes"
            )
        
    except Exception as e:
        log_test("POST /api/overlay/generate (card, with_form=true)", False, f"Exception: {str(e)}")

def test_regression_overlay_generate_a4():
    """
    TEST 3: POST /api/overlay/generate with page_size=a4, with_form=true
    Should return 200, valid PDF
    """
    print("\n" + "="*80)
    print("TEST 3: POST /api/overlay/generate (page_size=a4, with_form=true) - REGRESSION")
    print("="*80)
    
    try:
        payload = {
            "records": [
                {
                    "fio": "Петров Петр Петрович",
                    "passport_series": "АВ",
                    "passport_number": "7654321",
                    "date_day": "10",
                    "date_year": "26"
                }
            ],
            "page_size": "a4",
            "with_form": True
        }
        
        response = requests.post(
            f"{API_BASE}/overlay/generate",
            json=payload,
            timeout=30
        )
        
        # Check status code
        if response.status_code != 200:
            log_test(
                "POST /api/overlay/generate (a4, with_form=true) - Status Code",
                False,
                f"Expected 200, got {response.status_code}. Response: {response.text[:200]}"
            )
            return
        
        log_test("POST /api/overlay/generate (a4, with_form=true) - Status Code", True, "200 OK")
        
        # Check PDF signature
        body = response.content
        if not body.startswith(b'%PDF'):
            log_test(
                "POST /api/overlay/generate (a4, with_form=true) - PDF Signature",
                False,
                f"Expected '%PDF', got '{body[:10]}'"
            )
        else:
            log_test(
                "POST /api/overlay/generate (a4, with_form=true) - PDF Signature",
                True,
                f"Valid PDF (%PDF), size: {len(body)} bytes"
            )
        
    except Exception as e:
        log_test("POST /api/overlay/generate (a4, with_form=true)", False, f"Exception: {str(e)}")

def test_regression_overlay_background():
    """
    TEST 4: GET /api/overlay/background (scanned blank image)
    Should return 200, Content-Type: image/png
    """
    print("\n" + "="*80)
    print("TEST 4: GET /api/overlay/background (scanned blank) - REGRESSION")
    print("="*80)
    
    try:
        response = requests.get(f"{API_BASE}/overlay/background", timeout=30)
        
        # Check status code
        if response.status_code != 200:
            log_test(
                "GET /api/overlay/background - Status Code",
                False,
                f"Expected 200, got {response.status_code}"
            )
            return
        
        log_test("GET /api/overlay/background - Status Code", True, "200 OK")
        
        # Check Content-Type
        content_type = response.headers.get('Content-Type', '')
        if 'image/png' not in content_type:
            log_test(
                "GET /api/overlay/background - Content-Type",
                False,
                f"Expected 'image/png', got '{content_type}'"
            )
        else:
            log_test("GET /api/overlay/background - Content-Type", True, "image/png")
        
        # Check PNG signature
        body = response.content
        if not body.startswith(b'\x89PNG'):
            log_test(
                "GET /api/overlay/background - PNG Signature",
                False,
                f"Expected PNG signature, got '{body[:10]}'"
            )
        else:
            log_test(
                "GET /api/overlay/background - PNG Signature",
                True,
                f"Valid PNG, size: {len(body)} bytes"
            )
        
    except Exception as e:
        log_test("GET /api/overlay/background", False, f"Exception: {str(e)}")

def test_regression_overlay_layout():
    """
    TEST 5: GET /api/overlay/layout
    Should return 200, JSON with keys: layout, dx_mm, dy_mm, page_mm
    """
    print("\n" + "="*80)
    print("TEST 5: GET /api/overlay/layout - REGRESSION")
    print("="*80)
    
    try:
        response = requests.get(f"{API_BASE}/overlay/layout", timeout=30)
        
        # Check status code
        if response.status_code != 200:
            log_test(
                "GET /api/overlay/layout - Status Code",
                False,
                f"Expected 200, got {response.status_code}"
            )
            return
        
        log_test("GET /api/overlay/layout - Status Code", True, "200 OK")
        
        # Parse JSON
        try:
            data = response.json()
        except Exception as e:
            log_test(
                "GET /api/overlay/layout - JSON Parse",
                False,
                f"Failed to parse JSON: {str(e)}"
            )
            return
        
        # Check required keys
        required_keys = ['layout', 'dx_mm', 'dy_mm', 'page_mm']
        missing_keys = [k for k in required_keys if k not in data]
        
        if missing_keys:
            log_test(
                "GET /api/overlay/layout - Required Keys",
                False,
                f"Missing keys: {missing_keys}"
            )
        else:
            log_test(
                "GET /api/overlay/layout - Required Keys",
                True,
                f"All keys present: {required_keys}"
            )
        
        # Check layout is a list
        if not isinstance(data.get('layout'), list):
            log_test(
                "GET /api/overlay/layout - Layout Type",
                False,
                f"Expected list, got {type(data.get('layout'))}"
            )
        else:
            log_test(
                "GET /api/overlay/layout - Layout Type",
                True,
                f"Layout is list with {len(data['layout'])} fields"
            )
        
    except Exception as e:
        log_test("GET /api/overlay/layout", False, f"Exception: {str(e)}")

def test_regression_stats():
    """
    TEST 6: GET /api/stats
    Should return 200, JSON
    """
    print("\n" + "="*80)
    print("TEST 6: GET /api/stats - REGRESSION")
    print("="*80)
    
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=30)
        
        # Check status code
        if response.status_code != 200:
            log_test(
                "GET /api/stats - Status Code",
                False,
                f"Expected 200, got {response.status_code}"
            )
            return
        
        log_test("GET /api/stats - Status Code", True, "200 OK")
        
        # Parse JSON
        try:
            data = response.json()
        except Exception as e:
            log_test(
                "GET /api/stats - JSON Parse",
                False,
                f"Failed to parse JSON: {str(e)}"
            )
            return
        
        # Check for expected keys
        expected_keys = ['total', 'drafts', 'this_month', 'datasets', 'recent']
        missing_keys = [k for k in expected_keys if k not in data]
        
        if missing_keys:
            log_test(
                "GET /api/stats - Expected Keys",
                False,
                f"Missing keys: {missing_keys}"
            )
        else:
            log_test(
                "GET /api/stats - Expected Keys",
                True,
                f"All keys present: {expected_keys}"
            )
        
    except Exception as e:
        log_test("GET /api/stats", False, f"Exception: {str(e)}")

def print_summary():
    """Print test summary"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {test_results['passed'] + test_results['failed']}")
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"Success Rate: {test_results['passed'] / (test_results['passed'] + test_results['failed']) * 100:.1f}%")
    
    if test_results['failed'] > 0:
        print("\n" + "="*80)
        print("FAILED TESTS:")
        print("="*80)
        for test in test_results['tests']:
            if not test['passed']:
                print(f"❌ {test['name']}")
                if test['details']:
                    print(f"   {test['details']}")

def main():
    """Run all tests"""
    print("="*80)
    print("BACKEND API TESTING - Banetskaya.by")
    print("Testing NEW endpoint: GET /api/overlay/form-background")
    print("Testing REGRESSION endpoints")
    print("="*80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"API Base: {API_BASE}")
    print("="*80)
    
    # Test new endpoint
    test_new_form_background_endpoint()
    
    # Test regression endpoints
    test_regression_overlay_generate_card()
    test_regression_overlay_generate_a4()
    test_regression_overlay_background()
    test_regression_overlay_layout()
    test_regression_stats()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if test_results['failed'] == 0 else 1)

if __name__ == "__main__":
    main()
