#!/usr/bin/env python3
"""
Backend API Testing for Overlay Profiles CRUD
Tests the /api/overlay/profiles endpoints
"""

import requests
import sys
import json

# Base URL from frontend/.env
BASE_URL = "https://df5d1aab-d151-43c7-81f6-15cafa62422e.preview.emergentagent.com/api"

def test_1_get_profiles_initial():
    """Test 1: GET /api/overlay/profiles - должен вернуть минимум 1 профиль (авто-сид)"""
    print("\n=== TEST 1: GET /api/overlay/profiles (initial) ===")
    
    resp = requests.get(f"{BASE_URL}/overlay/profiles")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # Проверка структуры
    if "profiles" not in data or "active_id" not in data:
        print("❌ FAILED: Missing 'profiles' or 'active_id' in response")
        return False
    
    profiles = data["profiles"]
    active_id = data["active_id"]
    
    # Должен быть минимум 1 профиль (авто-сид)
    if len(profiles) < 1:
        print("❌ FAILED: Expected at least 1 profile (auto-seed)")
        return False
    
    # active_id не должен быть пустым
    if not active_id:
        print("❌ FAILED: active_id is empty")
        return False
    
    # Проверка полей первого профиля
    first_profile = profiles[0]
    required_fields = ["id", "name", "layout", "dx_mm", "dy_mm", "rotate", "constants"]
    
    for field in required_fields:
        if field not in first_profile:
            print(f"❌ FAILED: Missing field '{field}' in first profile")
            return False
    
    # layout должен быть непустым массивом
    if not isinstance(first_profile["layout"], list) or len(first_profile["layout"]) == 0:
        print("❌ FAILED: layout is not a non-empty array")
        return False
    
    # constants должен быть объектом
    if not isinstance(first_profile["constants"], dict):
        print("❌ FAILED: constants is not an object")
        return False
    
    print(f"✅ PASSED: Found {len(profiles)} profile(s), active_id={active_id}")
    print(f"   First profile has {len(first_profile['layout'])} layout fields")
    return True, data


def test_2_create_profile():
    """Test 2: POST /api/overlay/profiles - создать новый профиль"""
    print("\n=== TEST 2: POST /api/overlay/profiles (create) ===")
    
    payload = {
        "name": "Kyocera",
        "dx_mm": 1,
        "dy_mm": 2,
        "rotate": 90,
        "constants": {
            "reg_organ": {
                "value": "ОГиМ",
                "locked": True
            }
        }
    }
    
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    resp = requests.post(f"{BASE_URL}/overlay/profiles", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        return False
    
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # Проверка что вернулся объект с id (uuid)
    if "id" not in data:
        print("❌ FAILED: Missing 'id' in response")
        return False
    
    created_id = data["id"]
    
    # Проверка что id выглядит как UUID
    if len(created_id) < 32:
        print(f"❌ FAILED: id '{created_id}' doesn't look like a UUID")
        return False
    
    # Проверка что вернулись те же значения
    if data.get("name") != "Kyocera":
        print(f"❌ FAILED: Expected name='Kyocera', got '{data.get('name')}'")
        return False
    
    if data.get("dx_mm") != 1:
        print(f"❌ FAILED: Expected dx_mm=1, got {data.get('dx_mm')}")
        return False
    
    if data.get("dy_mm") != 2:
        print(f"❌ FAILED: Expected dy_mm=2, got {data.get('dy_mm')}")
        return False
    
    if data.get("rotate") != 90:
        print(f"❌ FAILED: Expected rotate=90, got {data.get('rotate')}")
        return False
    
    constants = data.get("constants", {})
    if "reg_organ" not in constants:
        print("❌ FAILED: Missing 'reg_organ' in constants")
        return False
    
    reg_organ = constants["reg_organ"]
    if reg_organ.get("value") != "ОГиМ" or reg_organ.get("locked") != True:
        print(f"❌ FAILED: constants.reg_organ incorrect: {reg_organ}")
        return False
    
    # layout должен быть непустым (по умолчанию)
    if not isinstance(data.get("layout"), list) or len(data.get("layout", [])) == 0:
        print("❌ FAILED: layout is not a non-empty array")
        return False
    
    print(f"✅ PASSED: Created profile with id={created_id}")
    print(f"   layout has {len(data['layout'])} fields (default)")
    return True, created_id


def test_3_get_profiles_after_create(created_id):
    """Test 3: GET /api/overlay/profiles - созданный профиль присутствует и активен"""
    print("\n=== TEST 3: GET /api/overlay/profiles (after create) ===")
    
    resp = requests.get(f"{BASE_URL}/overlay/profiles")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    profiles = data["profiles"]
    active_id = data["active_id"]
    
    print(f"Found {len(profiles)} profiles, active_id={active_id}")
    
    # Найти созданный профиль
    found = False
    for p in profiles:
        if p["id"] == created_id:
            found = True
            print(f"   Found created profile: name='{p['name']}'")
            break
    
    if not found:
        print(f"❌ FAILED: Created profile with id={created_id} not found in list")
        return False
    
    # active_id должен быть равен созданному (create делает профиль активным)
    if active_id != created_id:
        print(f"❌ FAILED: Expected active_id={created_id}, got {active_id}")
        return False
    
    print(f"✅ PASSED: Created profile is present and active")
    return True, profiles


def test_4_update_profile(created_id):
    """Test 4: PUT /api/overlay/profiles/{id} - обновить профиль"""
    print(f"\n=== TEST 4: PUT /api/overlay/profiles/{created_id} (update) ===")
    
    payload = {
        "name": "Kyocera-2",
        "layout": [
            {
                "key": "fio",
                "label": "ФИО",
                "x_pct": 10,
                "y_pct": 20,
                "font_pt": 9,
                "group": "Г"
            }
        ],
        "dx_mm": 3,
        "dy_mm": 0,
        "rotate": 270,
        "constants": {}
    }
    
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    resp = requests.put(f"{BASE_URL}/overlay/profiles/{created_id}", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        return False
    
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # Проверка что значения обновились
    if data.get("name") != "Kyocera-2":
        print(f"❌ FAILED: Expected name='Kyocera-2', got '{data.get('name')}'")
        return False
    
    if data.get("dx_mm") != 3:
        print(f"❌ FAILED: Expected dx_mm=3, got {data.get('dx_mm')}")
        return False
    
    if data.get("dy_mm") != 0:
        print(f"❌ FAILED: Expected dy_mm=0, got {data.get('dy_mm')}")
        return False
    
    if data.get("rotate") != 270:
        print(f"❌ FAILED: Expected rotate=270, got {data.get('rotate')}")
        return False
    
    # layout должен содержать 1 поле
    layout = data.get("layout", [])
    if len(layout) != 1:
        print(f"❌ FAILED: Expected layout with 1 field, got {len(layout)}")
        return False
    
    if layout[0].get("key") != "fio":
        print(f"❌ FAILED: Expected layout[0].key='fio', got '{layout[0].get('key')}'")
        return False
    
    # constants должен быть пустым объектом
    if data.get("constants") != {}:
        print(f"❌ FAILED: Expected empty constants, got {data.get('constants')}")
        return False
    
    print(f"✅ PASSED: Profile updated successfully")
    return True


def test_5_set_active_profile(first_profile_id):
    """Test 5: POST /api/overlay/active-profile - установить активный профиль"""
    print(f"\n=== TEST 5: POST /api/overlay/active-profile (set to first profile) ===")
    
    payload = {"id": first_profile_id}
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    resp = requests.post(f"{BASE_URL}/overlay/active-profile", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        return False
    
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # Проверка что вернулся active_id
    if "active_id" not in data:
        print("❌ FAILED: Missing 'active_id' in response")
        return False
    
    if data["active_id"] != first_profile_id:
        print(f"❌ FAILED: Expected active_id={first_profile_id}, got {data['active_id']}")
        return False
    
    # Проверка через GET /api/overlay/profiles
    resp2 = requests.get(f"{BASE_URL}/overlay/profiles")
    if resp2.status_code != 200:
        print(f"❌ FAILED: GET profiles returned {resp2.status_code}")
        return False
    
    data2 = resp2.json()
    if data2["active_id"] != first_profile_id:
        print(f"❌ FAILED: GET profiles shows active_id={data2['active_id']}, expected {first_profile_id}")
        return False
    
    print(f"✅ PASSED: Active profile set to {first_profile_id}")
    return True


def test_6_delete_profile(created_id):
    """Test 6: DELETE /api/overlay/profiles/{id} - удалить профиль"""
    print(f"\n=== TEST 6: DELETE /api/overlay/profiles/{created_id} ===")
    
    resp = requests.delete(f"{BASE_URL}/overlay/profiles/{created_id}")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        return False
    
    data = resp.json()
    print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # Проверка что вернулся {deleted: true}
    if data.get("deleted") != True:
        print(f"❌ FAILED: Expected deleted=true, got {data}")
        return False
    
    # Проверка что профиля больше нет в списке
    resp2 = requests.get(f"{BASE_URL}/overlay/profiles")
    if resp2.status_code != 200:
        print(f"❌ FAILED: GET profiles returned {resp2.status_code}")
        return False
    
    data2 = resp2.json()
    profiles = data2["profiles"]
    
    for p in profiles:
        if p["id"] == created_id:
            print(f"❌ FAILED: Deleted profile still exists in list")
            return False
    
    print(f"✅ PASSED: Profile deleted successfully")
    print(f"   Remaining profiles: {len(profiles)}")
    return True, len(profiles)


def test_7_boundary_nonexistent_id():
    """Test 7: PUT/DELETE несуществующего id -> 404"""
    print("\n=== TEST 7: Boundary - nonexistent ID ===")
    
    # Сначала создать дополнительный профиль, чтобы избежать защиты "нельзя удалить последний"
    print("  Creating temporary profile to avoid 'cannot delete last' protection...")
    temp_resp = requests.post(f"{BASE_URL}/overlay/profiles", json={
        "name": "Temp Profile for Test 7",
        "dx_mm": 0,
        "dy_mm": 0,
        "rotate": 0,
        "constants": {}
    })
    if temp_resp.status_code != 200:
        print(f"❌ FAILED: Could not create temporary profile: {temp_resp.status_code}")
        return False
    
    temp_id = temp_resp.json()["id"]
    print(f"  Created temporary profile: {temp_id}")
    
    fake_id = "no-such-id"
    
    # PUT несуществующего
    print(f"  Testing PUT /api/overlay/profiles/{fake_id}")
    resp = requests.put(f"{BASE_URL}/overlay/profiles/{fake_id}", json={
        "name": "Test",
        "layout": [],
        "dx_mm": 0,
        "dy_mm": 0,
        "rotate": 0,
        "constants": {}
    })
    print(f"  Status: {resp.status_code}")
    
    if resp.status_code != 404:
        print(f"❌ FAILED: Expected 404 for PUT nonexistent, got {resp.status_code}")
        # Cleanup
        requests.delete(f"{BASE_URL}/overlay/profiles/{temp_id}")
        return False
    
    # DELETE несуществующего
    print(f"  Testing DELETE /api/overlay/profiles/{fake_id}")
    resp2 = requests.delete(f"{BASE_URL}/overlay/profiles/{fake_id}")
    print(f"  Status: {resp2.status_code}")
    
    if resp2.status_code != 404:
        print(f"❌ FAILED: Expected 404 for DELETE nonexistent, got {resp2.status_code}")
        # Cleanup
        requests.delete(f"{BASE_URL}/overlay/profiles/{temp_id}")
        return False
    
    # Cleanup: удалить временный профиль
    print(f"  Cleaning up temporary profile...")
    cleanup_resp = requests.delete(f"{BASE_URL}/overlay/profiles/{temp_id}")
    if cleanup_resp.status_code != 200:
        print(f"  Warning: Could not delete temporary profile: {cleanup_resp.status_code}")
    
    print(f"✅ PASSED: Both PUT and DELETE return 404 for nonexistent ID")
    return True


def test_8_boundary_cannot_delete_last():
    """Test 8: Нельзя удалить последний профиль -> 400"""
    print("\n=== TEST 8: Boundary - cannot delete last profile ===")
    
    # Получить список профилей
    resp = requests.get(f"{BASE_URL}/overlay/profiles")
    if resp.status_code != 200:
        print(f"❌ FAILED: GET profiles returned {resp.status_code}")
        return False
    
    data = resp.json()
    profiles = data["profiles"]
    
    print(f"  Current profiles count: {len(profiles)}")
    
    # Если профилей больше 1, удалить все кроме последнего
    if len(profiles) > 1:
        print(f"  Deleting {len(profiles) - 1} profile(s) to leave only 1...")
        for i in range(len(profiles) - 1):
            profile_id = profiles[i]["id"]
            resp_del = requests.delete(f"{BASE_URL}/overlay/profiles/{profile_id}")
            if resp_del.status_code != 200:
                print(f"❌ FAILED: Could not delete profile {profile_id}: {resp_del.status_code}")
                return False
            print(f"    Deleted profile {i+1}/{len(profiles)-1}: {profile_id}")
    
    # Теперь должен остаться ровно 1 профиль
    resp2 = requests.get(f"{BASE_URL}/overlay/profiles")
    if resp2.status_code != 200:
        print(f"❌ FAILED: GET profiles returned {resp2.status_code}")
        return False
    
    data2 = resp2.json()
    remaining_profiles = data2["profiles"]
    
    if len(remaining_profiles) != 1:
        print(f"❌ FAILED: Expected 1 remaining profile, got {len(remaining_profiles)}")
        return False
    
    last_profile_id = remaining_profiles[0]["id"]
    print(f"  Last remaining profile: {last_profile_id}")
    
    # Попытка удалить последний профиль должна вернуть 400
    print(f"  Attempting to delete last profile...")
    resp3 = requests.delete(f"{BASE_URL}/overlay/profiles/{last_profile_id}")
    print(f"  Status: {resp3.status_code}")
    
    if resp3.status_code != 400:
        print(f"❌ FAILED: Expected 400 when deleting last profile, got {resp3.status_code}")
        return False
    
    # Проверка сообщения об ошибке
    error_data = resp3.json()
    detail = error_data.get("detail", "")
    print(f"  Error detail: {detail}")
    
    if "последний профиль" not in detail.lower():
        print(f"❌ FAILED: Expected error message about 'последний профиль', got: {detail}")
        return False
    
    print(f"✅ PASSED: Cannot delete last profile (400 with correct error message)")
    return True


def main():
    print("=" * 80)
    print("BACKEND TESTING: Overlay Profiles CRUD")
    print("=" * 80)
    
    results = []
    
    # Test 1: GET initial profiles
    result = test_1_get_profiles_initial()
    if not result:
        print("\n❌ Test 1 failed, stopping tests")
        sys.exit(1)
    
    success, initial_data = result
    results.append(("Test 1: GET profiles (initial)", success))
    
    # Сохранить id первого профиля для теста 5
    first_profile_id = initial_data["profiles"][0]["id"]
    
    # Test 2: POST create profile
    result = test_2_create_profile()
    if not result:
        print("\n❌ Test 2 failed, stopping tests")
        sys.exit(1)
    
    success, created_id = result
    results.append(("Test 2: POST create profile", success))
    
    # Test 3: GET profiles after create
    result = test_3_get_profiles_after_create(created_id)
    if not result:
        print("\n❌ Test 3 failed, stopping tests")
        sys.exit(1)
    
    success, profiles = result
    results.append(("Test 3: GET profiles (after create)", success))
    
    # Test 4: PUT update profile
    success = test_4_update_profile(created_id)
    results.append(("Test 4: PUT update profile", success))
    if not success:
        print("\n❌ Test 4 failed, continuing with remaining tests...")
    
    # Test 5: POST set active profile
    success = test_5_set_active_profile(first_profile_id)
    results.append(("Test 5: POST set active profile", success))
    if not success:
        print("\n❌ Test 5 failed, continuing with remaining tests...")
    
    # Test 6: DELETE profile
    result = test_6_delete_profile(created_id)
    if not result:
        print("\n❌ Test 6 failed, continuing with remaining tests...")
        results.append(("Test 6: DELETE profile", False))
    else:
        success, remaining_count = result
        results.append(("Test 6: DELETE profile", success))
    
    # Test 7: Boundary - nonexistent ID
    success = test_7_boundary_nonexistent_id()
    results.append(("Test 7: Boundary (404 for nonexistent)", success))
    if not success:
        print("\n❌ Test 7 failed, continuing with remaining tests...")
    
    # Test 8: Boundary - cannot delete last profile
    success = test_8_boundary_cannot_delete_last()
    results.append(("Test 8: Boundary (cannot delete last)", success))
    if not success:
        print("\n❌ Test 8 failed")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success rate: {passed}/{len(results)} ({100*passed//len(results)}%)")
    print("=" * 80)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)


if __name__ == "__main__":
    main()
