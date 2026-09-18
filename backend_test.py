#!/usr/bin/env python3
"""
Backend test for Banetskaya application - Cumulative Counters Feature
Tests ONLY backend (FastAPI on /api prefix)
"""
import requests
import sys
from io import BytesIO

# Backend URL from frontend/.env
BASE_URL = "https://vibrant-swartz-12.preview.emergentagent.com/api"

# Test results tracking
tests_passed = 0
tests_failed = 0
test_contracts = []  # Track created contracts for cleanup


def log_test(name, passed, detail=""):
    global tests_passed, tests_failed
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {name}")
    if detail:
        print(f"  {detail}")
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1
    return passed


def test_1_get_counters_base_default():
    """Test 1: GET /api/counters/base → default enabled:false"""
    print("\n=== TEST 1: GET /api/counters/base (default) ===")
    try:
        r = requests.get(f"{BASE_URL}/counters/base", timeout=30)
        if r.status_code != 200:
            return log_test("GET /api/counters/base", False, f"Status {r.status_code}")
        
        data = r.json()
        if not isinstance(data.get("enabled"), bool):
            return log_test("GET /api/counters/base", False, "enabled field missing or not bool")
        
        # Default should be enabled:false
        if data.get("enabled") == False:
            return log_test("GET /api/counters/base", True, f"Default enabled=false ✓ (data: {data})")
        else:
            return log_test("GET /api/counters/base", True, f"enabled={data.get('enabled')} (may be already configured)")
    except Exception as e:
        return log_test("GET /api/counters/base", False, str(e))


def test_2_create_contracts():
    """Test 2: Create 3 contracts with specific birth dates"""
    print("\n=== TEST 2: Create 3 contracts (04800, 04801, 04802) ===")
    
    contracts_data = [
        {
            "contract_number": "04800",
            "full_name": "Иванов Иван Иваныч",
            "birth_date": "01.01.2010",  # Minor (age < 18)
            "citizenship": "Республики Беларусь",
            "room_number": "101",
            "phone": "+375291111111"
        },
        {
            "contract_number": "04801",
            "full_name": "Петров Петр Петрович",
            "birth_date": "01.01.1990",  # Adult
            "citizenship": "Республики Беларусь",
            "room_number": "102",
            "phone": "+375292222222"
        },
        {
            "contract_number": "04802",
            "full_name": "Сидоров Сидор Сидорович",
            "birth_date": "01.01.1995",  # Adult
            "citizenship": "Республики Беларусь",
            "room_number": "103",
            "phone": "+375293333333"
        }
    ]
    
    created_ids = []
    for i, contract_data in enumerate(contracts_data):
        try:
            r = requests.post(
                f"{BASE_URL}/contracts",
                json={"fields": contract_data, "status": "final"},
                timeout=30
            )
            if r.status_code != 200:
                log_test(f"Create contract {contract_data['contract_number']}", False, 
                        f"Status {r.status_code}: {r.text[:200]}")
                continue
            
            data = r.json()
            contract_id = data.get("id")
            if not contract_id:
                log_test(f"Create contract {contract_data['contract_number']}", False, "No id in response")
                continue
            
            created_ids.append(contract_id)
            test_contracts.append(contract_id)
            log_test(f"Create contract {contract_data['contract_number']}", True, f"id={contract_id}")
        except Exception as e:
            log_test(f"Create contract {contract_data['contract_number']}", False, str(e))
    
    return len(created_ids) == 3


def test_3_set_counters_base_and_recompute():
    """Test 3: POST /api/counters/base with enabled:true and recompute=true"""
    print("\n=== TEST 3: POST /api/counters/base (enable + recompute) ===")
    
    try:
        payload = {
            "enabled": True,
            "total": 142,
            "minors": 99,
            "adults": 43,
            "free": 525
        }
        r = requests.post(
            f"{BASE_URL}/counters/base?recompute=true",
            json=payload,
            timeout=30
        )
        if r.status_code != 200:
            return log_test("POST /api/counters/base", False, f"Status {r.status_code}: {r.text[:200]}")
        
        data = r.json()
        if not data.get("saved"):
            return log_test("POST /api/counters/base", False, "saved != true")
        
        recompute_result = data.get("recompute")
        if not recompute_result:
            return log_test("POST /api/counters/base", False, "No recompute result")
        
        if not recompute_result.get("ok"):
            return log_test("POST /api/counters/base", False, 
                          f"recompute.ok=false: {recompute_result.get('reason')}")
        
        return log_test("POST /api/counters/base", True, 
                       f"saved=true, recompute.ok=true, computed={recompute_result.get('computed')}")
    except Exception as e:
        return log_test("POST /api/counters/base", False, str(e))


def test_4_verify_counters():
    """Test 4: Verify counters in contracts via GET /api/contracts"""
    print("\n=== TEST 4: Verify counters in contracts ===")
    
    try:
        r = requests.get(f"{BASE_URL}/contracts", timeout=30)
        if r.status_code != 200:
            return log_test("GET /api/contracts", False, f"Status {r.status_code}")
        
        contracts = r.json()
        if not isinstance(contracts, list):
            return log_test("GET /api/contracts", False, "Response not a list")
        
        # Find our test contracts by contract_number
        test_nums = ["04800", "04801", "04802"]
        found = {}
        for c in contracts:
            num = c.get("contract_number", "")
            if num in test_nums:
                found[num] = c
        
        if len(found) != 3:
            return log_test("Verify counters", False, 
                          f"Found only {len(found)}/3 test contracts")
        
        # Expected counters (sorted by contract_number):
        # 04800 (minor): total=143, minors=100, adults=43, free=524, minor=true
        # 04801 (adult): total=144, minors=100, adults=44, free=523
        # 04802 (adult): total=145, minors=100, adults=45, free=522
        
        expected = {
            "04800": {"occupancy_count": 143, "minors_count": 100, "adults_count": 43, "free_count": 524, "minor": True},
            "04801": {"occupancy_count": 144, "minors_count": 100, "adults_count": 44, "free_count": 523},
            "04802": {"occupancy_count": 145, "minors_count": 100, "adults_count": 45, "free_count": 522}
        }
        
        all_correct = True
        for num, exp in expected.items():
            contract = found.get(num)
            if not contract:
                log_test(f"Verify counters {num}", False, "Contract not found")
                all_correct = False
                continue
            
            counters = contract.get("counters")
            if not counters:
                log_test(f"Verify counters {num}", False, "No counters field")
                all_correct = False
                continue
            
            # Check each counter
            errors = []
            for key, expected_val in exp.items():
                actual_val = counters.get(key)
                if actual_val != expected_val:
                    errors.append(f"{key}: expected {expected_val}, got {actual_val}")
            
            if errors:
                log_test(f"Verify counters {num}", False, "; ".join(errors))
                all_correct = False
            else:
                log_test(f"Verify counters {num}", True, f"counters={counters}")
        
        return all_correct
    except Exception as e:
        return log_test("Verify counters", False, str(e))


def test_5_freeze_create_04803():
    """Test 5: FREEZE - create 04803 and verify old contracts unchanged"""
    print("\n=== TEST 5: FREEZE - create 04803 (adult) ===")
    
    try:
        # Create 04803
        contract_data = {
            "contract_number": "04803",
            "full_name": "Морозов Мороз Морозович",
            "birth_date": "01.01.1988",  # Adult
            "citizenship": "Республики Беларусь",
            "room_number": "104",
            "phone": "+375294444444"
        }
        r = requests.post(
            f"{BASE_URL}/contracts",
            json={"fields": contract_data, "status": "final"},
            timeout=30
        )
        if r.status_code != 200:
            return log_test("Create contract 04803", False, f"Status {r.status_code}")
        
        data = r.json()
        contract_id = data.get("id")
        if not contract_id:
            return log_test("Create contract 04803", False, "No id in response")
        
        test_contracts.append(contract_id)
        log_test("Create contract 04803", True, f"id={contract_id}")
        
        # Recompute with force=false
        r = requests.post(f"{BASE_URL}/contracts/recompute-counters?force=false", timeout=30)
        if r.status_code != 200:
            return log_test("Recompute counters (force=false)", False, f"Status {r.status_code}")
        
        result = r.json()
        if not result.get("ok"):
            return log_test("Recompute counters (force=false)", False, 
                          f"ok=false: {result.get('reason')}")
        
        log_test("Recompute counters (force=false)", True, f"computed={result.get('computed')}")
        
        # Verify: 04800/04801/04802 should be unchanged, 04803 should have new counters
        r = requests.get(f"{BASE_URL}/contracts", timeout=30)
        if r.status_code != 200:
            return log_test("Verify freeze", False, f"GET /api/contracts failed")
        
        contracts = r.json()
        found = {}
        for c in contracts:
            num = c.get("contract_number", "")
            if num in ["04800", "04801", "04802", "04803"]:
                found[num] = c
        
        # Check old contracts unchanged
        expected_old = {
            "04800": {"occupancy_count": 143, "minors_count": 100, "adults_count": 43, "free_count": 524},
            "04801": {"occupancy_count": 144, "minors_count": 100, "adults_count": 44, "free_count": 523},
            "04802": {"occupancy_count": 145, "minors_count": 100, "adults_count": 45, "free_count": 522}
        }
        
        all_correct = True
        for num, exp in expected_old.items():
            contract = found.get(num)
            if not contract:
                log_test(f"Verify freeze {num}", False, "Contract not found")
                all_correct = False
                continue
            
            counters = contract.get("counters", {})
            errors = []
            for key, expected_val in exp.items():
                actual_val = counters.get(key)
                if actual_val != expected_val:
                    errors.append(f"{key}: expected {expected_val}, got {actual_val}")
            
            if errors:
                log_test(f"Verify freeze {num} (unchanged)", False, "; ".join(errors))
                all_correct = False
            else:
                log_test(f"Verify freeze {num} (unchanged)", True, "✓")
        
        # Check 04803 has new counters
        contract_04803 = found.get("04803")
        if not contract_04803:
            log_test("Verify freeze 04803 (new)", False, "Contract not found")
            return False
        
        counters_04803 = contract_04803.get("counters", {})
        expected_04803 = {"occupancy_count": 146, "minors_count": 100, "adults_count": 46, "free_count": 521}
        
        errors = []
        for key, expected_val in expected_04803.items():
            actual_val = counters_04803.get(key)
            if actual_val != expected_val:
                errors.append(f"{key}: expected {expected_val}, got {actual_val}")
        
        if errors:
            log_test("Verify freeze 04803 (new)", False, "; ".join(errors))
            all_correct = False
        else:
            log_test("Verify freeze 04803 (new)", True, f"counters={counters_04803}")
        
        return all_correct
    except Exception as e:
        return log_test("Test freeze", False, str(e))


def test_6_not_all_numbered():
    """Test 6: NOT_ALL_NUMBERED - create contract without contract_number"""
    print("\n=== TEST 6: NOT_ALL_NUMBERED - contract without number ===")
    
    try:
        # Create contract WITHOUT contract_number
        contract_data = {
            "full_name": "Безномерный Человек Тестович",
            "birth_date": "01.01.2000",
            "citizenship": "Республики Беларусь",
            "room_number": "105",
            "phone": "+375295555555"
        }
        r = requests.post(
            f"{BASE_URL}/contracts",
            json={"fields": contract_data, "status": "final"},
            timeout=30
        )
        if r.status_code != 200:
            return log_test("Create contract without number", False, f"Status {r.status_code}")
        
        data = r.json()
        contract_id = data.get("id")
        if not contract_id:
            return log_test("Create contract without number", False, "No id in response")
        
        test_contracts.append(contract_id)
        log_test("Create contract without number", True, f"id={contract_id}")
        
        # Try to recompute - should fail with not_all_numbered
        r = requests.post(f"{BASE_URL}/contracts/recompute-counters?force=false", timeout=30)
        if r.status_code != 200:
            return log_test("Recompute (should fail)", False, f"Status {r.status_code}")
        
        result = r.json()
        if result.get("ok") == False and result.get("reason") == "not_all_numbered":
            missing = result.get("missing", [])
            log_test("Recompute (not_all_numbered)", True, 
                    f"ok=false, reason=not_all_numbered, missing_count={result.get('missing_count')}, missing={missing[:3]}")
            
            # Delete the contract without number
            r = requests.delete(f"{BASE_URL}/contracts/{contract_id}", timeout=30)
            if r.status_code == 200:
                test_contracts.remove(contract_id)
                log_test("Delete contract without number", True, "deleted")
            else:
                log_test("Delete contract without number", False, f"Status {r.status_code}")
            
            return True
        else:
            return log_test("Recompute (not_all_numbered)", False, 
                          f"Expected ok=false, reason=not_all_numbered, got {result}")
    except Exception as e:
        return log_test("Test not_all_numbered", False, str(e))


def test_7_injection_into_zayavlenie():
    """Test 7: INJECTION INTO APPLICATION - verify counters in zayavlenie/prefill"""
    print("\n=== TEST 7: INJECTION INTO APPLICATION ===")
    
    try:
        # POST /api/zayavlenie/prefill with contract 04800
        payload = {
            "students": [
                {
                    "contract_number": "04800",
                    "fio": "Иванов Иван Иваныч",
                    "birth_date": "01.01.2010"
                }
            ]
        }
        r = requests.post(f"{BASE_URL}/zayavlenie/prefill", json=payload, timeout=30)
        if r.status_code != 200:
            return log_test("POST /api/zayavlenie/prefill", False, f"Status {r.status_code}: {r.text[:200]}")
        
        data = r.json()
        records = data.get("records", [])
        if not records:
            return log_test("POST /api/zayavlenie/prefill", False, "No records in response")
        
        record = records[0]
        
        # Check counters in record
        expected_counters = {
            "occupancy_count": "143",
            "minors_count": "100",
            "adults_count": "43",
            "free_count": "524"
        }
        
        errors = []
        for key, expected_val in expected_counters.items():
            actual_val = str(record.get(key, ""))
            if actual_val != expected_val:
                errors.append(f"{key}: expected {expected_val}, got {actual_val}")
        
        if errors:
            return log_test("Verify counters in zayavlenie/prefill", False, "; ".join(errors))
        else:
            log_test("Verify counters in zayavlenie/prefill", True, 
                    f"occupancy={record.get('occupancy_count')}, minors={record.get('minors_count')}, "
                    f"adults={record.get('adults_count')}, free={record.get('free_count')}")
        
        # POST /api/zayavlenie/preview with this record and side="back"
        preview_payload = {
            "records": [record],
            "side": "back"
        }
        r = requests.post(f"{BASE_URL}/zayavlenie/preview", json=preview_payload, timeout=30)
        if r.status_code != 200:
            return log_test("POST /api/zayavlenie/preview", False, f"Status {r.status_code}")
        
        if r.headers.get("Content-Type") != "application/pdf":
            return log_test("POST /api/zayavlenie/preview", False, 
                          f"Content-Type: {r.headers.get('Content-Type')}")
        
        pdf_bytes = r.content
        if not pdf_bytes.startswith(b"%PDF"):
            return log_test("POST /api/zayavlenie/preview", False, "Not a valid PDF")
        
        log_test("POST /api/zayavlenie/preview", True, f"Valid PDF, {len(pdf_bytes)} bytes")
        
        # Extract text from page 1 (index 1, page 2) using pypdf
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(pdf_bytes))
            if len(reader.pages) < 2:
                return log_test("Extract text from PDF page 2", False, 
                              f"PDF has only {len(reader.pages)} page(s)")
            
            page_text = reader.pages[1].extract_text()
            
            # Check for counter values in text
            required_values = ["143", "100", "43", "524"]
            found_values = []
            missing_values = []
            
            for val in required_values:
                if val in page_text:
                    found_values.append(val)
                else:
                    missing_values.append(val)
            
            if missing_values:
                return log_test("Verify counters in PDF text", False, 
                              f"Missing values: {missing_values}. Found: {found_values}")
            else:
                return log_test("Verify counters in PDF text", True, 
                              f"All counter values found in PDF: {found_values}")
        except Exception as e:
            return log_test("Extract text from PDF", False, str(e))
    except Exception as e:
        return log_test("Test injection into zayavlenie", False, str(e))


def test_8_regression():
    """Test 8: REGRESSION - test forma19/forma24/zayavlenie preview endpoints"""
    print("\n=== TEST 8: REGRESSION - forma19/forma24/zayavlenie preview ===")
    
    all_passed = True
    
    # Test forma19/preview
    try:
        payload = {
            "records": [
                {
                    "surname": "Тестов",
                    "first_name": "Тест",
                    "citizenship": "Республики Беларусь"
                }
            ]
        }
        r = requests.post(f"{BASE_URL}/forma19/preview", json=payload, timeout=30)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            log_test("POST /api/forma19/preview", True, f"Valid PDF, {len(r.content)} bytes")
        else:
            log_test("POST /api/forma19/preview", False, f"Status {r.status_code}")
            all_passed = False
    except Exception as e:
        log_test("POST /api/forma19/preview", False, str(e))
        all_passed = False
    
    # Test forma24/preview
    try:
        payload = {
            "records": [
                {
                    "surname": "Тестов",
                    "first_name": "Тест",
                    "sex": "1"
                }
            ]
        }
        r = requests.post(f"{BASE_URL}/forma24/preview", json=payload, timeout=30)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            log_test("POST /api/forma24/preview", True, f"Valid PDF, {len(r.content)} bytes")
        else:
            log_test("POST /api/forma24/preview", False, f"Status {r.status_code}")
            all_passed = False
    except Exception as e:
        log_test("POST /api/forma24/preview", False, str(e))
        all_passed = False
    
    # Test zayavlenie/preview (already tested in test 7, but test again with simple data)
    try:
        payload = {
            "records": [
                {
                    "fio": "Тестов Тест Тестович",
                    "birth_year": "2000"
                }
            ],
            "side": "front"
        }
        r = requests.post(f"{BASE_URL}/zayavlenie/preview", json=payload, timeout=30)
        if r.status_code == 200 and r.content.startswith(b"%PDF"):
            log_test("POST /api/zayavlenie/preview (regression)", True, f"Valid PDF, {len(r.content)} bytes")
        else:
            log_test("POST /api/zayavlenie/preview (regression)", False, f"Status {r.status_code}")
            all_passed = False
    except Exception as e:
        log_test("POST /api/zayavlenie/preview (regression)", False, str(e))
        all_passed = False
    
    return all_passed


def test_9_cleanup():
    """Test 9: CLEANUP - delete all test contracts and reset counters"""
    print("\n=== TEST 9: CLEANUP ===")
    
    all_passed = True
    
    # Delete all test contracts
    for contract_id in test_contracts:
        try:
            r = requests.delete(f"{BASE_URL}/contracts/{contract_id}", timeout=30)
            if r.status_code == 200:
                log_test(f"Delete contract {contract_id[:8]}", True, "deleted")
            else:
                log_test(f"Delete contract {contract_id[:8]}", False, f"Status {r.status_code}")
                all_passed = False
        except Exception as e:
            log_test(f"Delete contract {contract_id[:8]}", False, str(e))
            all_passed = False
    
    # Reset counters
    try:
        payload = {
            "enabled": False,
            "total": 0,
            "minors": 0,
            "adults": 0,
            "free": 0
        }
        r = requests.post(f"{BASE_URL}/counters/base", json=payload, timeout=30)
        if r.status_code == 200:
            log_test("Reset counters", True, "enabled=false, all counters=0")
        else:
            log_test("Reset counters", False, f"Status {r.status_code}")
            all_passed = False
    except Exception as e:
        log_test("Reset counters", False, str(e))
        all_passed = False
    
    # Verify GET /api/contracts returns original count
    try:
        r = requests.get(f"{BASE_URL}/contracts", timeout=30)
        if r.status_code == 200:
            contracts = r.json()
            count = len(contracts)
            log_test("Verify cleanup", True, f"GET /api/contracts returns {count} contracts")
        else:
            log_test("Verify cleanup", False, f"Status {r.status_code}")
            all_passed = False
    except Exception as e:
        log_test("Verify cleanup", False, str(e))
        all_passed = False
    
    return all_passed


def main():
    print("=" * 80)
    print("BACKEND TEST: Banetskaya - Cumulative Counters Feature")
    print("=" * 80)
    print(f"Backend URL: {BASE_URL}")
    print()
    
    # Run all tests
    test_1_get_counters_base_default()
    test_2_create_contracts()
    test_3_set_counters_base_and_recompute()
    test_4_verify_counters()
    test_5_freeze_create_04803()
    test_6_not_all_numbered()
    test_7_injection_into_zayavlenie()
    test_8_regression()
    test_9_cleanup()
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"Total: {tests_passed + tests_failed}")
    print(f"Success Rate: {tests_passed / (tests_passed + tests_failed) * 100:.1f}%")
    print("=" * 80)
    
    return 0 if tests_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
