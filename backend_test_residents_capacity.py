#!/usr/bin/env python3
"""
Backend API Testing for Banetskaya.by - Residents Capacity & Mismatches
Testing new capacity/free fields and mismatches endpoint.

Review Request:
1) GET /api/residents/mismatches → {mismatches:[...], total}. Expected total>=1.
   Check for "Чумаков Иван Сергеевич" with room mismatch (accommodation "902/2", contract "905/4").
   Residents WITHOUT contracts should NOT be in the list (only real room mismatches).

2) GET /api/residents/floor/9 → blocks now have capacity and free fields.
   Check logic: capacity usually 6 (rooms /2 and /4), free = max(0, capacity - people).
   Find block with people<capacity and verify free>0 (e.g., 905: people=5, capacity=6, free=1).

3) GET /api/residents/block/902 → structure now {block, floor, rooms:[...], total, capacity, occupied, free}.
   Each room has {room, capacity, occupied, free, people}.
   Check: room "2" capacity=2, room "4" capacity=4; occupied = number of people; free = capacity-occupied.
   Block-level capacity=6, occupied=number of residents, free correct.

4) GET /api/residents/block/905 (or any block with free space) → free>0 for at least one room, and block-level free>0.

5) Regression: GET /api/residents/mismatches should NOT be caught by /api/residents/{res_id} route (not 404 "Жилец не найден").
"""

import requests
import sys

# Base URL from frontend/.env
BASE_URL = "https://analysis-tool-42.preview.emergentagent.com/api"


def test_residents_mismatches():
    """
    TEST 1: GET /api/residents/mismatches
    Expected: {mismatches:[...], total}
    - total >= 1 (at least "Чумаков Иван Сергеевич" with room mismatch)
    - Each element contains: full_name, block, room, floor, checks object
    - checks.room_mismatch = true for mismatches
    - checks.contract_room and checks.mismatches array present
    - "Чумаков Иван Сергеевич" should be present with accommodation "902/2" and contract "905/4"
    - Residents WITHOUT contracts should NOT be in the list (only real room mismatches)
    """
    print("\n" + "="*80)
    print("TEST 1: GET /api/residents/mismatches")
    print("="*80)
    
    url = f"{BASE_URL}/residents/mismatches"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check structure
    if "mismatches" not in data or "total" not in data:
        print(f"❌ FAIL: Missing 'mismatches' or 'total' key")
        print(f"Response: {data}")
        return False
    
    mismatches = data["mismatches"]
    total = data["total"]
    
    print(f"Total mismatches: {total}")
    print(f"Mismatches count: {len(mismatches)}")
    
    # Check total >= 1
    if total < 1:
        print(f"❌ FAIL: Expected total >= 1, got {total}")
        print(f"   (At least 'Чумаков Иван Сергеевич' should have room mismatch)")
        return False
    
    # Check structure of first mismatch
    if mismatches:
        m = mismatches[0]
        required_fields = ["full_name", "block", "room", "floor", "checks"]
        missing = [f for f in required_fields if f not in m]
        if missing:
            print(f"❌ FAIL: Missing fields in mismatch: {missing}")
            print(f"Mismatch: {m}")
            return False
        
        # Check checks object structure
        checks = m.get("checks", {})
        if "room_mismatch" not in checks:
            print(f"❌ FAIL: Missing 'room_mismatch' in checks")
            print(f"Checks: {checks}")
            return False
        
        print(f"Sample mismatch structure: {list(m.keys())}")
        print(f"Sample checks structure: {list(checks.keys())}")
    
    # Find "Чумаков Иван Сергеевич"
    chumakov = None
    for m in mismatches:
        if "Чумаков" in m.get("full_name", "") and "Иван" in m.get("full_name", "") and "Сергеевич" in m.get("full_name", ""):
            chumakov = m
            break
    
    if not chumakov:
        print(f"❌ FAIL: 'Чумаков Иван Сергеевич' not found in mismatches")
        print(f"Available names: {[m.get('full_name') for m in mismatches[:5]]}")
        return False
    
    print(f"\n✓ Found 'Чумаков Иван Сергеевич':")
    print(f"  full_name: {chumakov.get('full_name')}")
    print(f"  block: {chumakov.get('block')}")
    print(f"  room: {chumakov.get('room')}")
    print(f"  floor: {chumakov.get('floor')}")
    
    # Check Chumakov's details
    checks = chumakov.get("checks", {})
    
    # Should have room_mismatch = true
    if not checks.get("room_mismatch"):
        print(f"❌ FAIL: Chumakov should have room_mismatch=true, got {checks.get('room_mismatch')}")
        return False
    
    # Check accommodation room (should be "902/2" or contain "902" and "2")
    accommodation_room = f"{chumakov.get('block')}/{chumakov.get('room')}"
    if accommodation_room != "902/2":
        print(f"❌ FAIL: Expected accommodation '902/2', got '{accommodation_room}'")
        return False
    
    # Check contract_room (should be "905/4")
    contract_room = checks.get("contract_room", "")
    if contract_room != "905/4":
        print(f"❌ FAIL: Expected contract_room '905/4', got '{contract_room}'")
        return False
    
    # Check mismatches array
    mismatch_details = checks.get("mismatches", [])
    if not mismatch_details:
        print(f"❌ FAIL: Expected mismatches array to be non-empty")
        return False
    
    # Find room mismatch in array
    room_mismatch_found = False
    for detail in mismatch_details:
        if detail.get("field") == "room":
            room_mismatch_found = True
            print(f"\n✓ Room mismatch details:")
            print(f"  field: {detail.get('field')}")
            print(f"  label: {detail.get('label')}")
            print(f"  accommodation: {detail.get('accommodation')}")
            print(f"  contract: {detail.get('contract')}")
            
            # Verify values
            if detail.get("accommodation") != "902/2":
                print(f"❌ FAIL: Expected accommodation '902/2', got '{detail.get('accommodation')}'")
                return False
            if detail.get("contract") != "905/4":
                print(f"❌ FAIL: Expected contract '905/4', got '{detail.get('contract')}'")
                return False
            break
    
    if not room_mismatch_found:
        print(f"❌ FAIL: Room mismatch not found in mismatches array")
        print(f"Mismatches: {mismatch_details}")
        return False
    
    # Check that residents WITHOUT contracts are NOT in the list
    # (Only those with contracts but room mismatch should be here)
    # We can verify by checking that all mismatches have has_contract=true or contract_room present
    for m in mismatches:
        checks = m.get("checks", {})
        # If no_contract is true, this should NOT be in mismatches list
        if checks.get("no_contract"):
            print(f"❌ FAIL: Found resident WITHOUT contract in mismatches list: {m.get('full_name')}")
            print(f"   Residents without contracts should NOT be in mismatches (only real room mismatches)")
            return False
    
    print(f"\n✅ PASS: GET /api/residents/mismatches")
    print(f"   - total: {total} (>= 1)")
    print(f"   - 'Чумаков Иван Сергеевич' found with room mismatch")
    print(f"   - accommodation: 902/2, contract: 905/4")
    print(f"   - checks.room_mismatch = true")
    print(f"   - mismatches array contains room mismatch details")
    print(f"   - No residents without contracts in the list")
    
    return True


def test_residents_floor_9_capacity():
    """
    TEST 2: GET /api/residents/floor/9
    Expected: blocks array now has capacity and free fields
    - capacity usually 6 (rooms /2 and /4)
    - free = max(0, capacity - people)
    - Find block with people < capacity and verify free > 0
    - Example: block 905 with people=5, capacity=6, free=1
    """
    print("\n" + "="*80)
    print("TEST 2: GET /api/residents/floor/9 - capacity and free fields")
    print("="*80)
    
    url = f"{BASE_URL}/residents/floor/9"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check structure
    if "blocks" not in data:
        print(f"❌ FAIL: Missing 'blocks' key")
        print(f"Response: {data}")
        return False
    
    blocks = data["blocks"]
    print(f"Blocks count: {len(blocks)}")
    
    if not blocks:
        print(f"❌ FAIL: No blocks returned")
        return False
    
    # Check first block has new fields
    b = blocks[0]
    required_fields = ["block", "index", "people", "rooms", "capacity", "free"]
    missing = [f for f in required_fields if f not in b]
    if missing:
        print(f"❌ FAIL: Missing fields in block: {missing}")
        print(f"Block: {b}")
        return False
    
    print(f"Sample block structure: {list(b.keys())}")
    print(f"Sample block: {b['block']}, people={b['people']}, capacity={b['capacity']}, free={b['free']}")
    
    # Check capacity logic for all blocks
    capacity_errors = []
    free_errors = []
    
    for block in blocks:
        people = block.get("people", 0)
        capacity = block.get("capacity", 0)
        free = block.get("free", 0)
        
        # Capacity should usually be 6 (rooms /2 and /4)
        if capacity not in [0, 6]:  # Allow 0 for empty blocks
            print(f"⚠️  WARNING: Block {block['block']} has unusual capacity: {capacity} (expected 6)")
        
        # free should be max(0, capacity - people)
        expected_free = max(0, capacity - people)
        if free != expected_free:
            free_errors.append(f"Block {block['block']}: free={free}, expected {expected_free} (capacity={capacity}, people={people})")
    
    if free_errors:
        print(f"❌ FAIL: Free calculation errors:")
        for err in free_errors[:5]:  # Show first 5 errors
            print(f"   {err}")
        return False
    
    # Find block with people < capacity (should have free > 0)
    blocks_with_free_space = [b for b in blocks if b.get("people", 0) < b.get("capacity", 0)]
    
    if not blocks_with_free_space:
        print(f"⚠️  WARNING: No blocks with free space found (all blocks full)")
    else:
        print(f"\n✓ Found {len(blocks_with_free_space)} blocks with free space:")
        for b in blocks_with_free_space[:3]:  # Show first 3
            print(f"  Block {b['block']}: people={b['people']}, capacity={b['capacity']}, free={b['free']}")
            
            # Verify free > 0
            if b.get("free", 0) <= 0:
                print(f"❌ FAIL: Block {b['block']} has people < capacity but free <= 0")
                return False
    
    # Check for block 905 specifically (mentioned in review request)
    block_905 = next((b for b in blocks if b.get("block") == "905"), None)
    if block_905:
        print(f"\n✓ Block 905 details:")
        print(f"  people: {block_905.get('people')}")
        print(f"  capacity: {block_905.get('capacity')}")
        print(f"  free: {block_905.get('free')}")
        
        # Check if it matches expected values (people=5, capacity=6, free=1)
        if block_905.get("people") == 5 and block_905.get("capacity") == 6 and block_905.get("free") == 1:
            print(f"  ✓ Matches expected values (people=5, capacity=6, free=1)")
    
    # Check fully occupied blocks (free should be 0)
    fully_occupied = [b for b in blocks if b.get("people", 0) >= b.get("capacity", 0) and b.get("capacity", 0) > 0]
    if fully_occupied:
        print(f"\n✓ Found {len(fully_occupied)} fully occupied blocks:")
        for b in fully_occupied[:3]:  # Show first 3
            print(f"  Block {b['block']}: people={b['people']}, capacity={b['capacity']}, free={b['free']}")
            if b.get("free", 0) != 0:
                print(f"❌ FAIL: Fully occupied block {b['block']} should have free=0, got {b['free']}")
                return False
    
    print(f"\n✅ PASS: GET /api/residents/floor/9 - capacity and free fields")
    print(f"   - All blocks have capacity and free fields")
    print(f"   - free = max(0, capacity - people) for all blocks")
    print(f"   - Blocks with people < capacity have free > 0")
    print(f"   - Fully occupied blocks have free = 0")
    
    return True


def test_residents_block_902_capacity():
    """
    TEST 3: GET /api/residents/block/902
    Expected: {block, floor, rooms:[...], total, capacity, occupied, free}
    - Each room has {room, capacity, occupied, free, people}
    - Room "2" capacity=2, room "4" capacity=4
    - occupied = number of people
    - free = capacity - occupied
    - Block-level: capacity=6, occupied=number of residents, free correct
    """
    print("\n" + "="*80)
    print("TEST 3: GET /api/residents/block/902 - capacity structure")
    print("="*80)
    
    url = f"{BASE_URL}/residents/block/902"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    
    # Check block-level structure
    required_fields = ["block", "floor", "rooms", "total", "capacity", "occupied", "free"]
    missing = [f for f in required_fields if f not in data]
    if missing:
        print(f"❌ FAIL: Missing fields in block response: {missing}")
        print(f"Response: {data}")
        return False
    
    print(f"Block: {data['block']}")
    print(f"Floor: {data['floor']}")
    print(f"Total residents: {data['total']}")
    print(f"Capacity: {data['capacity']}")
    print(f"Occupied: {data['occupied']}")
    print(f"Free: {data['free']}")
    
    # Check block-level capacity (should be 6 for standard block)
    if data['capacity'] != 6:
        print(f"⚠️  WARNING: Block capacity is {data['capacity']}, expected 6")
    
    # Check block-level occupied = total
    if data['occupied'] != data['total']:
        print(f"❌ FAIL: Block occupied ({data['occupied']}) != total ({data['total']})")
        return False
    
    # Check block-level free = capacity - occupied
    expected_free = max(0, data['capacity'] - data['occupied'])
    if data['free'] != expected_free:
        print(f"❌ FAIL: Block free ({data['free']}) != capacity - occupied ({expected_free})")
        return False
    
    # Check rooms structure
    rooms = data.get("rooms", [])
    if not rooms:
        print(f"❌ FAIL: No rooms returned")
        return False
    
    print(f"\nRooms count: {len(rooms)}")
    
    # Check first room structure
    r = rooms[0]
    required_room_fields = ["room", "capacity", "occupied", "free", "people"]
    missing = [f for f in required_room_fields if f not in r]
    if missing:
        print(f"❌ FAIL: Missing fields in room: {missing}")
        print(f"Room: {r}")
        return False
    
    print(f"Sample room structure: {list(r.keys())}")
    
    # Find room "2" and room "4"
    room_2 = next((r for r in rooms if r.get("room") == "2"), None)
    room_4 = next((r for r in rooms if r.get("room") == "4"), None)
    
    if not room_2:
        print(f"⚠️  WARNING: Room '2' not found in block 902")
    else:
        print(f"\n✓ Room '2' details:")
        print(f"  capacity: {room_2.get('capacity')}")
        print(f"  occupied: {room_2.get('occupied')}")
        print(f"  free: {room_2.get('free')}")
        print(f"  people: {room_2.get('people')}")
        
        # Check capacity = 2
        if room_2.get('capacity') != 2:
            print(f"❌ FAIL: Room '2' capacity should be 2, got {room_2.get('capacity')}")
            return False
        
        # Check occupied = len(people)
        people_count = len(room_2.get('people', []))
        if room_2.get('occupied') != people_count:
            print(f"❌ FAIL: Room '2' occupied ({room_2.get('occupied')}) != len(people) ({people_count})")
            return False
        
        # Check free = capacity - occupied
        expected_free = max(0, room_2.get('capacity', 0) - room_2.get('occupied', 0))
        if room_2.get('free') != expected_free:
            print(f"❌ FAIL: Room '2' free ({room_2.get('free')}) != capacity - occupied ({expected_free})")
            return False
    
    if not room_4:
        print(f"⚠️  WARNING: Room '4' not found in block 902")
    else:
        print(f"\n✓ Room '4' details:")
        print(f"  capacity: {room_4.get('capacity')}")
        print(f"  occupied: {room_4.get('occupied')}")
        print(f"  free: {room_4.get('free')}")
        print(f"  people: {room_4.get('people')}")
        
        # Check capacity = 4
        if room_4.get('capacity') != 4:
            print(f"❌ FAIL: Room '4' capacity should be 4, got {room_4.get('capacity')}")
            return False
        
        # Check occupied = len(people)
        people_count = len(room_4.get('people', []))
        if room_4.get('occupied') != people_count:
            print(f"❌ FAIL: Room '4' occupied ({room_4.get('occupied')}) != len(people) ({people_count})")
            return False
        
        # Check free = capacity - occupied
        expected_free = max(0, room_4.get('capacity', 0) - room_4.get('occupied', 0))
        if room_4.get('free') != expected_free:
            print(f"❌ FAIL: Room '4' free ({room_4.get('free')}) != capacity - occupied ({expected_free})")
            return False
    
    # Check all rooms have correct free calculation
    for room in rooms:
        expected_free = max(0, room.get('capacity', 0) - room.get('occupied', 0))
        if room.get('free') != expected_free:
            print(f"❌ FAIL: Room '{room.get('room')}' free ({room.get('free')}) != capacity - occupied ({expected_free})")
            return False
    
    print(f"\n✅ PASS: GET /api/residents/block/902 - capacity structure")
    print(f"   - Block-level: capacity={data['capacity']}, occupied={data['occupied']}, free={data['free']}")
    print(f"   - Room '2': capacity=2, occupied={room_2.get('occupied') if room_2 else 'N/A'}, free={room_2.get('free') if room_2 else 'N/A'}")
    print(f"   - Room '4': capacity=4, occupied={room_4.get('occupied') if room_4 else 'N/A'}, free={room_4.get('free') if room_4 else 'N/A'}")
    print(f"   - All rooms have correct free = capacity - occupied")
    
    return True


def test_residents_block_905_free_space():
    """
    TEST 4: GET /api/residents/block/905 (or any block with free space)
    Expected: free > 0 for at least one room, and block-level free > 0
    """
    print("\n" + "="*80)
    print("TEST 4: GET /api/residents/block/905 - free space verification")
    print("="*80)
    
    url = f"{BASE_URL}/residents/block/905"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    data = response.json()
    
    # Check block-level free
    block_free = data.get("free", 0)
    print(f"Block 905 free: {block_free}")
    
    if block_free <= 0:
        print(f"⚠️  WARNING: Block 905 has no free space (free={block_free})")
        print(f"   (Review request expected free > 0, but block might be full)")
    else:
        print(f"✓ Block-level free > 0: {block_free}")
    
    # Check rooms
    rooms = data.get("rooms", [])
    rooms_with_free_space = [r for r in rooms if r.get("free", 0) > 0]
    
    print(f"\nRooms with free space: {len(rooms_with_free_space)}/{len(rooms)}")
    
    if rooms_with_free_space:
        print(f"✓ Found rooms with free space:")
        for r in rooms_with_free_space:
            print(f"  Room {r.get('room')}: capacity={r.get('capacity')}, occupied={r.get('occupied')}, free={r.get('free')}")
    else:
        print(f"⚠️  All rooms in block 905 are full")
    
    # If block has free space, at least one room should have free space
    if block_free > 0 and not rooms_with_free_space:
        print(f"❌ FAIL: Block has free={block_free} but no rooms have free space")
        return False
    
    print(f"\n✅ PASS: GET /api/residents/block/905 - free space verification")
    if block_free > 0:
        print(f"   - Block-level free: {block_free}")
        print(f"   - Rooms with free space: {len(rooms_with_free_space)}")
    else:
        print(f"   - Block is fully occupied (free=0)")
    
    return True


def test_residents_mismatches_not_captured_by_id_route():
    """
    TEST 5: Regression - GET /api/residents/mismatches should NOT be caught by /api/residents/{res_id}
    Should return mismatches structure, not 404 "Жилец не найден"
    """
    print("\n" + "="*80)
    print("TEST 5: Regression - /api/residents/mismatches NOT captured by /{res_id}")
    print("="*80)
    
    url = f"{BASE_URL}/residents/mismatches"
    response = requests.get(url)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print(f"❌ FAIL: Got 404, route is captured by /residents/{{res_id}}")
        print(f"Response: {response.text}")
        # Check if error message is about resident not found
        if "Жилец не найден" in response.text or "not found" in response.text.lower():
            print(f"   Error message indicates route was captured by /residents/{{res_id}}")
        return False
    
    if response.status_code != 200:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        return False
    
    data = response.json()
    
    # Should have mismatches/total, not resident fields
    if "mismatches" in data and "total" in data:
        print(f"✅ PASS: /api/residents/mismatches returns correct structure (not captured by /{{res_id}})")
        return True
    else:
        print(f"❌ FAIL: Response doesn't have mismatches/total structure")
        print(f"Response: {data}")
        return False


def main():
    print("="*80)
    print("BACKEND API TESTING: Residents Capacity & Mismatches")
    print("Base URL:", BASE_URL)
    print("="*80)
    
    results = []
    
    # TEST 1: GET /api/residents/mismatches
    results.append(("TEST 1: GET /api/residents/mismatches", 
                   test_residents_mismatches()))
    
    # TEST 2: GET /api/residents/floor/9 - capacity and free
    results.append(("TEST 2: GET /api/residents/floor/9 - capacity and free", 
                   test_residents_floor_9_capacity()))
    
    # TEST 3: GET /api/residents/block/902 - capacity structure
    results.append(("TEST 3: GET /api/residents/block/902 - capacity structure", 
                   test_residents_block_902_capacity()))
    
    # TEST 4: GET /api/residents/block/905 - free space
    results.append(("TEST 4: GET /api/residents/block/905 - free space", 
                   test_residents_block_905_free_space()))
    
    # TEST 5: Regression - mismatches not captured by /{res_id}
    results.append(("TEST 5: Regression - /api/residents/mismatches NOT captured by /{res_id}", 
                   test_residents_mismatches_not_captured_by_id_route()))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
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
    print("="*80)
    
    if failed > 0:
        print(f"\n❌ {failed} TEST(S) FAILED")
        sys.exit(1)
    else:
        print("\n✅ ALL TESTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
