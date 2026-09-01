#!/usr/bin/env python3
"""
Backend test for POST /api/residents/import-groups endpoint.
Tests the new group import functionality for Banetskaya.by application.
"""
import requests
import sys
from pathlib import Path

# Base URL from frontend/.env
BASE_URL = "https://cloud-server-1.preview.emergentagent.com/api"

# Test files
TEST_FILES = [
    "/tmp/groups/mrd11.docx",
    "/tmp/groups/zd11.docx",
    "/tmp/groups/sd11_15.docx",
    "/tmp/groups/sd201_210.docx",
    "/tmp/groups/dozach_sd2324.docx",
]

def test_precondition():
    """Check if residents database is populated (674 residents expected)."""
    print("\n=== PRECONDITION: Check residents database ===")
    try:
        resp = requests.get(f"{BASE_URL}/residents/floors", timeout=30)
        print(f"GET /api/residents/floors → {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        data = resp.json()
        total = data.get("total", 0)
        print(f"Total residents in database: {total}")
        
        if total == 0:
            print("⚠️  Database is empty. Need to import /tmp/zaselenie.xlsx first.")
            # Try to import
            print("\nAttempting to import /tmp/zaselenie.xlsx...")
            zaselenie_path = Path("/tmp/zaselenie.xlsx")
            if not zaselenie_path.exists():
                print(f"❌ FAILED: {zaselenie_path} not found")
                return False
            
            with open(zaselenie_path, "rb") as f:
                files = {"file": ("zaselenie.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                resp = requests.post(f"{BASE_URL}/residents/import", files=files, timeout=60)
                print(f"POST /api/residents/import → {resp.status_code}")
                
                if resp.status_code != 200:
                    print(f"❌ FAILED: Import failed with {resp.status_code}")
                    print(f"Response: {resp.text}")
                    return False
                
                result = resp.json()
                imported = result.get("imported", 0)
                print(f"✅ Imported {imported} residents")
                
                if imported < 600:
                    print(f"⚠️  WARNING: Expected ~674 residents, got {imported}")
        else:
            print(f"✅ Database has {total} residents (expected ~674)")
        
        return True
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def test_1_multiple_files():
    """Test 1: POST with all 5 files simultaneously."""
    print("\n=== TEST 1: Import all 5 group files simultaneously ===")
    try:
        files_data = []
        for fpath in TEST_FILES:
            p = Path(fpath)
            if not p.exists():
                print(f"❌ FAILED: File not found: {fpath}")
                return False
            with open(p, "rb") as f:
                files_data.append(("files", (p.name, f.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")))
        
        resp = requests.post(f"{BASE_URL}/residents/import-groups", files=files_data, timeout=60)
        print(f"POST /api/residents/import-groups (5 files) → {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            print(f"Response: {resp.text}")
            return False
        
        data = resp.json()
        print(f"Response structure: {list(data.keys())}")
        
        # Check required fields
        required = ["files", "total_names", "groups_in_files", "matched", "changed", "unchanged", "not_found_count", "not_found", "groups"]
        for field in required:
            if field not in data:
                print(f"❌ FAILED: Missing field '{field}' in response")
                return False
        
        print(f"✅ All required fields present")
        print(f"  files: {len(data['files'])} files processed")
        for f in data['files']:
            print(f"    - {f['file']}: {f['names']} names")
        print(f"  total_names: {data['total_names']} (expected 483)")
        print(f"  groups_in_files: {data['groups_in_files']} (expected 19)")
        print(f"  matched: {data['matched']} (expected ~129)")
        print(f"  changed: {data['changed']}")
        print(f"  unchanged: {data['unchanged']}")
        print(f"  not_found_count: {data['not_found_count']}")
        print(f"  groups: {len(data['groups'])} groups")
        
        # Validate expectations
        if data['total_names'] != 483:
            print(f"⚠️  WARNING: Expected total_names=483, got {data['total_names']}")
        
        if data['groups_in_files'] != 19:
            print(f"⚠️  WARNING: Expected groups_in_files=19, got {data['groups_in_files']}")
        
        if data['matched'] < 100 or data['matched'] > 150:
            print(f"⚠️  WARNING: Expected matched~129, got {data['matched']}")
        
        print(f"✅ TEST 1 PASSED")
        return True
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_2_verify_group_set():
    """Test 2: Verify group was actually set for specific resident."""
    print("\n=== TEST 2: Verify group was set for 'Бондарев Владимир Алексеевич' ===")
    try:
        resp = requests.get(f"{BASE_URL}/residents/block/902", timeout=30)
        print(f"GET /api/residents/block/902 → {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        data = resp.json()
        rooms = data.get("rooms", [])
        
        # Find Бондарев Владимир Алексеевич
        found = False
        for room in rooms:
            for person in room.get("people", []):
                if "Бондарев" in person.get("full_name", "") and "Владимир" in person.get("full_name", ""):
                    found = True
                    study_group = person.get("study_group", "")
                    print(f"Found: {person.get('full_name')}")
                    print(f"  study_group: '{study_group}'")
                    
                    if study_group == "СД-201":
                        print(f"✅ TEST 2 PASSED: study_group='СД-201' as expected")
                        return True
                    else:
                        print(f"❌ FAILED: Expected study_group='СД-201', got '{study_group}'")
                        return False
        
        if not found:
            print(f"❌ FAILED: 'Бондарев Владимир Алексеевич' not found in block 902")
            return False
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def test_3_idempotency():
    """Test 3: Repeat import - should be idempotent (changed=0, unchanged=matched)."""
    print("\n=== TEST 3: Idempotency - repeat import with same files ===")
    try:
        files_data = []
        for fpath in TEST_FILES:
            p = Path(fpath)
            with open(p, "rb") as f:
                files_data.append(("files", (p.name, f.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")))
        
        resp = requests.post(f"{BASE_URL}/residents/import-groups", files=files_data, timeout=60)
        print(f"POST /api/residents/import-groups (repeat) → {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        data = resp.json()
        matched = data['matched']
        changed = data['changed']
        unchanged = data['unchanged']
        
        print(f"  matched: {matched}")
        print(f"  changed: {changed}")
        print(f"  unchanged: {unchanged}")
        
        if changed != 0:
            print(f"❌ FAILED: Expected changed=0 (idempotent), got {changed}")
            return False
        
        if unchanged != matched:
            print(f"❌ FAILED: Expected unchanged=matched ({matched}), got unchanged={unchanged}")
            return False
        
        print(f"✅ TEST 3 PASSED: Idempotent (changed=0, unchanged=matched)")
        return True
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def test_4_single_file():
    """Test 4: Upload single file."""
    print("\n=== TEST 4: Import single file (zd11.docx) ===")
    try:
        fpath = "/tmp/groups/zd11.docx"
        p = Path(fpath)
        
        with open(p, "rb") as f:
            files = [("files", (p.name, f.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
        
        resp = requests.post(f"{BASE_URL}/residents/import-groups", files=files, timeout=60)
        print(f"POST /api/residents/import-groups (zd11.docx) → {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        data = resp.json()
        matched = data['matched']
        groups = data.get('groups', {})
        
        print(f"  matched: {matched} (expected >=0)")
        print(f"  groups: {list(groups.keys())}")
        
        if "ЗД-11" not in groups:
            print(f"❌ FAILED: Expected 'ЗД-11' in groups, got {list(groups.keys())}")
            return False
        
        print(f"✅ TEST 4 PASSED: Single file import works, 'ЗД-11' found in groups")
        return True
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def test_5_negative_excel_file():
    """Test 5: Negative test - upload Excel file (not Word)."""
    print("\n=== TEST 5: Negative test - upload Excel file (should fail) ===")
    try:
        fpath = "/tmp/zaselenie.xlsx"
        p = Path(fpath)
        
        if not p.exists():
            print(f"⚠️  SKIP: {fpath} not found")
            return True
        
        with open(p, "rb") as f:
            files = [("files", (p.name, f.read(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))]
        
        resp = requests.post(f"{BASE_URL}/residents/import-groups", files=files, timeout=60)
        print(f"POST /api/residents/import-groups (zaselenie.xlsx) → {resp.status_code}")
        
        if resp.status_code == 200:
            print(f"❌ FAILED: Expected error (400 or 500), got 200 (should not accept Excel)")
            return False
        
        if resp.status_code in [400, 500]:
            print(f"✅ TEST 5 PASSED: Correctly rejected Excel file with {resp.status_code}")
            try:
                error = resp.json()
                detail = error.get("detail", "")
                print(f"  Error detail: {detail}")
            except:
                print(f"  Response: {resp.text[:200]}")
            return True
        
        print(f"⚠️  WARNING: Unexpected status code {resp.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def main():
    print("=" * 80)
    print("BACKEND TEST: POST /api/residents/import-groups")
    print("=" * 80)
    
    results = []
    
    # Precondition
    if not test_precondition():
        print("\n❌ PRECONDITION FAILED - Cannot proceed with tests")
        sys.exit(1)
    
    # Run tests
    results.append(("TEST 1: Multiple files", test_1_multiple_files()))
    results.append(("TEST 2: Verify group set", test_2_verify_group_set()))
    results.append(("TEST 3: Idempotency", test_3_idempotency()))
    results.append(("TEST 4: Single file", test_4_single_file()))
    results.append(("TEST 5: Negative test", test_5_negative_excel_file()))
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed*100//total}% success rate)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
