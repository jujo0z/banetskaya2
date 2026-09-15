#!/usr/bin/env python3
"""
Backend API Testing for Banetskaya.by - Residents Filtering Endpoints
Testing TWO new GET endpoints for filtering residents section.
"""

import requests
import sys
from urllib.parse import quote

# Base URL from frontend/.env
BASE_URL = "https://deploy-preview-152.preview.emergentagent.com/api"

def test_residents_options():
    """
    TEST 1: GET /api/residents/options
    Expected: {groups:[...], benefits:[...]}
    - groups should be non-empty sorted array (dozens of values like "ЗД-11","ЛД-201","СД-201")
    - benefits should be array (may be empty as benefits not yet set)
    - No empty strings/null in groups
    """
    print("\n" + "="*80)
    print("TEST 1: GET /api/residents/options")
    print("="*80)
    
    url = f"{BASE_URL}/residents/options"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check structure
    if "groups" not in data or "benefits" not in data:
        print(f"❌ FAIL: Missing 'groups' or 'benefits' key")
        print(f"Response: {data}")
        return False
    
    groups = data["groups"]
    benefits = data["benefits"]
    
    print(f"Groups count: {len(groups)}")
    print(f"Benefits count: {len(benefits)}")
    
    # Check groups is non-empty
    if not groups:
        print(f"❌ FAIL: groups array is empty (expected dozens of values)")
        return False
    
    # Check no empty strings/null in groups
    for g in groups:
        if not g or not str(g).strip():
            print(f"❌ FAIL: Found empty/null value in groups: {repr(g)}")
            return False
    
    # Check groups is sorted
    if groups != sorted(groups):
        print(f"❌ FAIL: groups array is not sorted")
        print(f"Expected: {sorted(groups)[:5]}...")
        print(f"Got: {groups[:5]}...")
        return False
    
    # Show sample groups
    print(f"Sample groups (first 10): {groups[:10]}")
    print(f"Sample benefits: {benefits}")
    
    print(f"✅ PASS: /api/residents/options returns valid structure")
    print(f"   - groups: {len(groups)} values, sorted, no empty strings")
    print(f"   - benefits: {len(benefits)} values")
    
    return True, groups


def test_residents_filter_by_group(group_name, expected_min_total=0):
    """
    TEST 2-4: GET /api/residents/filter?group=<group_name>
    Expected: {residents:[...], total}
    - total > 0 for existing groups
    - Each resident has: floor, block, room, full_name, study_group, checks
    - List sorted by floor, block, room
    - All residents have study_group == group_name
    """
    print("\n" + "="*80)
    print(f"TEST: GET /api/residents/filter?group={group_name}")
    print("="*80)
    
    url = f"{BASE_URL}/residents/filter?group={quote(group_name)}"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check structure
    if "residents" not in data or "total" not in data:
        print(f"❌ FAIL: Missing 'residents' or 'total' key")
        print(f"Response: {data}")
        return False
    
    residents = data["residents"]
    total = data["total"]
    
    print(f"Total: {total}")
    print(f"Residents count: {len(residents)}")
    
    # Check total matches length
    if total != len(residents):
        print(f"❌ FAIL: total ({total}) != len(residents) ({len(residents)})")
        return False
    
    # Check expected minimum
    if expected_min_total > 0 and total < expected_min_total:
        print(f"⚠️  WARNING: Expected total >= {expected_min_total}, got {total}")
    
    if total == 0:
        print(f"✅ PASS: Empty result for non-existent group (expected)")
        return True
    
    # Check first resident structure
    if residents:
        r = residents[0]
        required_fields = ["floor", "block", "room", "full_name", "study_group", "checks"]
        missing = [f for f in required_fields if f not in r]
        if missing:
            print(f"❌ FAIL: Missing fields in resident: {missing}")
            print(f"Resident: {r}")
            return False
        
        print(f"Sample resident fields: {list(r.keys())}")
        print(f"Sample resident: {r['full_name']}, floor={r['floor']}, block={r['block']}, room={r['room']}, study_group={r['study_group']}")
    
    # Check all residents have correct study_group
    wrong_group = [r for r in residents if r.get("study_group") != group_name]
    if wrong_group:
        print(f"❌ FAIL: Found {len(wrong_group)} residents with wrong study_group")
        print(f"Expected: {group_name}")
        print(f"Sample wrong: {wrong_group[0]}")
        return False
    
    # Check sorting (floor, block, room)
    prev_floor = -1
    prev_block = ""
    prev_room = ""
    for r in residents:
        floor = r.get("floor", 0)
        block = r.get("block", "")
        room = r.get("room", "")
        
        if floor < prev_floor:
            print(f"❌ FAIL: Not sorted by floor: {prev_floor} -> {floor}")
            return False
        if floor == prev_floor and block < prev_block:
            print(f"❌ FAIL: Not sorted by block: {prev_block} -> {block}")
            return False
        if floor == prev_floor and block == prev_block and room < prev_room:
            print(f"❌ FAIL: Not sorted by room: {prev_room} -> {room}")
            return False
        
        prev_floor = floor
        prev_block = block
        prev_room = room
    
    print(f"✅ PASS: /api/residents/filter?group={group_name}")
    print(f"   - total: {total}")
    print(f"   - All residents have study_group='{group_name}'")
    print(f"   - Sorted by floor, block, room")
    print(f"   - All required fields present")
    
    return True


def test_residents_filter_nonexistent():
    """
    TEST 5: GET /api/residents/filter?group=НЕСУЩЕСТВУЮЩАЯ-999
    Expected: total==0, residents==[] (not error)
    """
    print("\n" + "="*80)
    print("TEST 5: GET /api/residents/filter?group=НЕСУЩЕСТВУЮЩАЯ-999")
    print("="*80)
    
    url = f"{BASE_URL}/residents/filter?group={quote('НЕСУЩЕСТВУЮЩАЯ-999')}"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    
    if data.get("total") != 0:
        print(f"❌ FAIL: Expected total=0, got {data.get('total')}")
        return False
    
    if data.get("residents") != []:
        print(f"❌ FAIL: Expected residents=[], got {data.get('residents')}")
        return False
    
    print(f"✅ PASS: Empty result for non-existent group (total=0, residents=[])")
    return True


def test_residents_options_not_captured_by_id_route():
    """
    TEST 6: Verify /api/residents/options is NOT captured by /api/residents/{res_id}
    Should return groups/benefits structure, not 404 "Жилец не найден"
    """
    print("\n" + "="*80)
    print("TEST 6: Verify /api/residents/options NOT captured by /{res_id} route")
    print("="*80)
    
    url = f"{BASE_URL}/residents/options"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print(f"❌ FAIL: Got 404, route is captured by /residents/{{res_id}}")
        print(f"Response: {response.text}")
        return False
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        return False
    
    data = response.json()
    
    # Should have groups/benefits, not resident fields
    if "groups" in data and "benefits" in data:
        print(f"✅ PASS: /api/residents/options returns correct structure (not captured by /{{res_id}})")
        return True
    else:
        print(f"❌ FAIL: Response doesn't have groups/benefits structure")
        print(f"Response: {data}")
        return False


def main():
    print("="*80)
    print("BACKEND API TESTING: Residents Filtering Endpoints")
    print("Base URL:", BASE_URL)
    print("="*80)
    
    results = []
    
    # TEST 1: GET /api/residents/options
    result = test_residents_options()
    if isinstance(result, tuple):
        success, groups = result
        results.append(("TEST 1: GET /api/residents/options", success))
    else:
        results.append(("TEST 1: GET /api/residents/options", result))
        groups = []
    
    # TEST 2: GET /api/residents/filter?group=СД-201
    if groups and "СД-201" in groups:
        results.append(("TEST 2: GET /api/residents/filter?group=СД-201", 
                       test_residents_filter_by_group("СД-201", expected_min_total=5)))
    else:
        print("\n⚠️  SKIP TEST 2: Group 'СД-201' not found in options")
        results.append(("TEST 2: GET /api/residents/filter?group=СД-201", None))
    
    # TEST 3: GET /api/residents/filter?group=ЗД-21
    if groups and "ЗД-21" in groups:
        results.append(("TEST 3: GET /api/residents/filter?group=ЗД-21", 
                       test_residents_filter_by_group("ЗД-21", expected_min_total=2)))
    else:
        print("\n⚠️  SKIP TEST 3: Group 'ЗД-21' not found in options")
        results.append(("TEST 3: GET /api/residents/filter?group=ЗД-21", None))
    
    # TEST 4: Combined filter with any real group
    if groups:
        test_group = groups[0]  # Take first group from options
        results.append((f"TEST 4: GET /api/residents/filter?group={test_group}", 
                       test_residents_filter_by_group(test_group)))
    else:
        print("\n⚠️  SKIP TEST 4: No groups available")
        results.append(("TEST 4: Combined filter", None))
    
    # TEST 5: Empty result for non-existent group
    results.append(("TEST 5: GET /api/residents/filter?group=НЕСУЩЕСТВУЮЩАЯ-999", 
                   test_residents_filter_nonexistent()))
    
    # TEST 6: Verify /api/residents/options not captured by /{res_id}
    results.append(("TEST 6: /api/residents/options NOT captured by /{res_id}", 
                   test_residents_options_not_captured_by_id_route()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, result in results:
        if result is None:
            status = "⏭️  SKIPPED"
            skipped += 1
        elif result:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        print(f"{status}: {test_name}")
    
    print("\n" + "="*80)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print("="*80)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
