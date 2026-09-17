#!/usr/bin/env python3
"""
Backend testing for Banetskaya.by NEW FEATURE:
Встроенная Excel-таблица данных + свои столбцы + зависимости
"""
import requests
import json
import sys

# Backend URL from frontend/.env
BASE_URL = "https://analysis-tool-42.preview.emergentagent.com/api"

def test_master_schema():
    """TEST 1: GET /api/master-schema -> 200 with builtin + custom columns"""
    print("\n=== TEST 1: GET /api/master-schema ===")
    resp = requests.get(f"{BASE_URL}/master-schema")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    if "columns" not in data:
        print("❌ FAILED: Missing 'columns' key")
        return False
    
    columns = data["columns"]
    builtin = [c for c in columns if c.get("builtin") == True]
    custom = [c for c in columns if c.get("builtin") == False]
    
    print(f"✅ Total columns: {len(columns)}")
    print(f"✅ Builtin columns: {len(builtin)} (expected ~50)")
    print(f"✅ Custom columns: {len(custom)}")
    
    # Check for required builtin columns
    keys = [c["key"] for c in columns]
    required = ["fio", "contract_number", "phone", "room_number"]
    for req in required:
        if req in keys:
            print(f"✅ Required key '{req}' present")
        else:
            print(f"❌ FAILED: Required key '{req}' missing")
            return False
    
    # Check structure
    if builtin:
        sample = builtin[0]
        required_fields = ["key", "label", "section", "builtin"]
        for field in required_fields:
            if field not in sample:
                print(f"❌ FAILED: Column missing field '{field}'")
                return False
        print(f"✅ Column structure valid: {required_fields}")
    
    print("✅ TEST 1 PASSED")
    return True


def test_contracts_grid():
    """TEST 2: GET /api/contracts/grid -> 200 with rows containing master data"""
    print("\n=== TEST 2: GET /api/contracts/grid ===")
    resp = requests.get(f"{BASE_URL}/contracts/grid")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    if "rows" not in data:
        print("❌ FAILED: Missing 'rows' key")
        return False
    
    rows = data["rows"]
    print(f"✅ Total rows: {len(rows)}")
    
    if len(rows) == 0:
        print("⚠️  WARNING: No rows in grid (expected 6 demo contracts)")
        return True
    
    # Check structure of first row
    row = rows[0]
    required_fields = ["id", "status", "created_at", "contract_number", "full_name", "master"]
    for field in required_fields:
        if field not in row:
            print(f"❌ FAILED: Row missing field '{field}'")
            return False
    
    print(f"✅ Row structure valid: {required_fields}")
    
    # Check master data
    master = row.get("master", {})
    if not master or not any(str(v).strip() for v in master.values()):
        print("⚠️  WARNING: First row has empty master data")
    else:
        print(f"✅ Master data present: {len(master)} fields")
        # Show sample keys
        sample_keys = list(master.keys())[:5]
        print(f"   Sample keys: {sample_keys}")
    
    print("✅ TEST 2 PASSED")
    return True


def test_custom_columns_create():
    """TEST 3: POST /api/custom-columns -> 200, creates custom column"""
    print("\n=== TEST 3: POST /api/custom-columns (create) ===")
    
    # Create a custom column
    payload = {
        "label": "Курс обучения",
        "section": "Дополнительно",
        "dropdown": ["1 курс", "2 курс", "3 курс", "4 курс"]
    }
    
    resp = requests.post(f"{BASE_URL}/custom-columns", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        if resp.status_code == 400:
            print(f"   Detail: {resp.json().get('detail')}")
        return False
    
    data = resp.json()
    required_fields = ["key", "label", "section"]
    for field in required_fields:
        if field not in data:
            print(f"❌ FAILED: Response missing field '{field}'")
            return False
    
    key = data["key"]
    if not key.startswith("cc_"):
        print(f"❌ FAILED: Key should start with 'cc_', got '{key}'")
        return False
    
    print(f"✅ Custom column created: key={key}, label={data['label']}")
    print(f"✅ Section: {data.get('section')}")
    print(f"✅ Dropdown: {data.get('dropdown')}")
    
    # Verify it appears in master-schema
    print("\n   Verifying in master-schema...")
    resp2 = requests.get(f"{BASE_URL}/master-schema")
    if resp2.status_code == 200:
        columns = resp2.json().get("columns", [])
        found = any(c.get("key") == key for c in columns)
        if found:
            print(f"✅ Custom column appears in master-schema")
        else:
            print(f"❌ FAILED: Custom column NOT in master-schema")
            return False
    
    # Verify it appears in custom-columns list
    print("   Verifying in custom-columns list...")
    resp3 = requests.get(f"{BASE_URL}/custom-columns")
    if resp3.status_code == 200:
        custom_cols = resp3.json().get("columns", [])
        found = any(c.get("key") == key for c in custom_cols)
        if found:
            print(f"✅ Custom column appears in custom-columns list")
        else:
            print(f"❌ FAILED: Custom column NOT in custom-columns list")
            return False
    
    print("✅ TEST 3 PASSED")
    return True, key  # Return the key for later tests


def test_custom_columns_duplicate():
    """TEST 3b: POST /api/custom-columns with duplicate label -> 400"""
    print("\n=== TEST 3b: POST /api/custom-columns (duplicate) ===")
    
    payload = {"label": "Курс обучения"}  # Same as TEST 3
    resp = requests.post(f"{BASE_URL}/custom-columns", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 400:
        print(f"❌ FAILED: Expected 400 for duplicate, got {resp.status_code}")
        return False
    
    print(f"✅ Correctly rejected duplicate label")
    print(f"   Detail: {resp.json().get('detail')}")
    print("✅ TEST 3b PASSED")
    return True


def test_custom_columns_empty_label():
    """TEST 3c: POST /api/custom-columns with empty label -> 400"""
    print("\n=== TEST 3c: POST /api/custom-columns (empty label) ===")
    
    payload = {"label": ""}
    resp = requests.post(f"{BASE_URL}/custom-columns", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 400:
        print(f"❌ FAILED: Expected 400 for empty label, got {resp.status_code}")
        return False
    
    print(f"✅ Correctly rejected empty label")
    print(f"   Detail: {resp.json().get('detail')}")
    print("✅ TEST 3c PASSED")
    return True


def test_master_bulk_update(custom_key):
    """TEST 4: PUT /api/contracts/master-bulk -> 200, updates master data"""
    print("\n=== TEST 4: PUT /api/contracts/master-bulk ===")
    
    # First, get a contract from grid
    resp = requests.get(f"{BASE_URL}/contracts/grid")
    if resp.status_code != 200:
        print("❌ FAILED: Cannot get contracts grid")
        return False
    
    rows = resp.json().get("rows", [])
    if not rows:
        print("❌ FAILED: No contracts to update")
        return False
    
    contract_id = rows[0]["id"]
    master = dict(rows[0].get("master", {}))
    
    print(f"   Updating contract: {contract_id}")
    print(f"   Original phone: {master.get('phone', 'N/A')}")
    
    # Update phone and add custom column value
    master["phone"] = "+375291234567"
    master[custom_key] = "2 курс"
    
    payload = {
        "rows": [
            {
                "id": contract_id,
                "master": master
            }
        ]
    }
    
    resp = requests.put(f"{BASE_URL}/contracts/master-bulk", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    if data.get("updated") != 1:
        print(f"❌ FAILED: Expected updated=1, got {data.get('updated')}")
        return False
    
    print(f"✅ Updated {data['updated']} contract(s)")
    
    # Verify the update
    print("\n   Verifying update in grid...")
    resp2 = requests.get(f"{BASE_URL}/contracts/grid")
    if resp2.status_code == 200:
        rows2 = resp2.json().get("rows", [])
        updated_row = next((r for r in rows2 if r["id"] == contract_id), None)
        if updated_row:
            new_master = updated_row.get("master", {})
            new_phone = new_master.get("phone")
            new_custom = new_master.get(custom_key)
            
            if new_phone == "+375291234567":
                print(f"✅ Phone updated correctly: {new_phone}")
            else:
                print(f"❌ FAILED: Phone not updated, got {new_phone}")
                return False
            
            if new_custom == "2 курс":
                print(f"✅ Custom column value saved: {custom_key}={new_custom}")
            else:
                print(f"⚠️  WARNING: Custom column value: {new_custom}")
            
            # Check that full_name and contract_number are preserved
            if updated_row.get("full_name"):
                print(f"✅ full_name preserved: {updated_row['full_name']}")
            if updated_row.get("contract_number"):
                print(f"✅ contract_number preserved: {updated_row['contract_number']}")
        else:
            print("❌ FAILED: Updated contract not found in grid")
            return False
    
    print("✅ TEST 4 PASSED")
    return True


def test_document_targets():
    """TEST 5: GET /api/document-targets/{document} -> 200 with targets"""
    print("\n=== TEST 5: GET /api/document-targets/{document} ===")
    
    documents = ["zayavlenie", "forma19", "forma24", "soobshenie", "contract"]
    
    for doc in documents:
        print(f"\n   Testing document: {doc}")
        resp = requests.get(f"{BASE_URL}/document-targets/{doc}")
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"   ❌ FAILED: Expected 200, got {resp.status_code}")
            return False
        
        data = resp.json()
        if "targets" not in data:
            print(f"   ❌ FAILED: Missing 'targets' key")
            return False
        
        targets = data["targets"]
        print(f"   ✅ Found {len(targets)} target fields")
        
        # Check structure
        if targets:
            sample = targets[0]
            if "field" not in sample or "label" not in sample:
                print(f"   ❌ FAILED: Target missing 'field' or 'label'")
                return False
            print(f"   ✅ Sample target: {sample['field']} - {sample['label']}")
        
        # Check for specific field in zayavlenie
        if doc == "zayavlenie":
            fields = [t["field"] for t in targets]
            if "stay_term" in fields:
                print(f"   ✅ 'stay_term' field present in zayavlenie")
            else:
                print(f"   ❌ FAILED: 'stay_term' field missing in zayavlenie")
                return False
    
    # Test invalid document
    print(f"\n   Testing invalid document: badname")
    resp = requests.get(f"{BASE_URL}/document-targets/badname")
    print(f"   Status: {resp.status_code}")
    if resp.status_code != 404:
        print(f"   ❌ FAILED: Expected 404 for invalid document, got {resp.status_code}")
        return False
    print(f"   ✅ Correctly rejected invalid document")
    
    print("\n✅ TEST 5 PASSED")
    return True


def test_dependencies_create(custom_key):
    """TEST 6: POST /api/dependencies -> 200, creates dependency"""
    print("\n=== TEST 6: POST /api/dependencies ===")
    
    # Create a dependency: zayavlenie.stay_term <- custom column
    payload = {
        "document": "zayavlenie",
        "target_field": "stay_term",
        "source": custom_key
    }
    
    resp = requests.post(f"{BASE_URL}/dependencies", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        if resp.status_code == 400:
            print(f"   Detail: {resp.json().get('detail')}")
        return False
    
    data = resp.json()
    required_fields = ["id", "document", "target_field", "source"]
    for field in required_fields:
        if field not in data:
            print(f"❌ FAILED: Response missing field '{field}'")
            return False
    
    dep_id = data["id"]
    print(f"✅ Dependency created: id={dep_id}")
    print(f"   document={data['document']}, target_field={data['target_field']}, source={data['source']}")
    
    # Test replacing dependency (same target_field)
    print("\n   Testing replacement (same target_field)...")
    payload2 = {
        "document": "zayavlenie",
        "target_field": "stay_term",
        "source": "phone"  # Different source
    }
    resp2 = requests.post(f"{BASE_URL}/dependencies", json=payload2)
    if resp2.status_code == 200:
        print(f"✅ Dependency replaced (one per target_field)")
        dep_id = resp2.json()["id"]  # Update dep_id for cleanup
    
    # Test invalid document
    print("\n   Testing invalid document...")
    payload3 = {"document": "badname", "target_field": "stay_term", "source": custom_key}
    resp3 = requests.post(f"{BASE_URL}/dependencies", json=payload3)
    if resp3.status_code != 400:
        print(f"   ❌ FAILED: Expected 400 for invalid document, got {resp3.status_code}")
        return False
    print(f"   ✅ Correctly rejected invalid document")
    
    # Test invalid target_field
    print("   Testing invalid target_field...")
    payload4 = {"document": "zayavlenie", "target_field": "nope", "source": custom_key}
    resp4 = requests.post(f"{BASE_URL}/dependencies", json=payload4)
    if resp4.status_code != 400:
        print(f"   ❌ FAILED: Expected 400 for invalid target_field, got {resp4.status_code}")
        return False
    print(f"   ✅ Correctly rejected invalid target_field")
    
    # Test empty source
    print("   Testing empty source...")
    payload5 = {"document": "zayavlenie", "target_field": "stay_term", "source": ""}
    resp5 = requests.post(f"{BASE_URL}/dependencies", json=payload5)
    if resp5.status_code != 400:
        print(f"   ❌ FAILED: Expected 400 for empty source, got {resp5.status_code}")
        return False
    print(f"   ✅ Correctly rejected empty source")
    
    print("\n✅ TEST 6 PASSED")
    return True, dep_id


def test_dependencies_list():
    """TEST 7: GET /api/dependencies?document=... -> 200 with source_label and target_label"""
    print("\n=== TEST 7: GET /api/dependencies ===")
    
    # Get all dependencies
    resp = requests.get(f"{BASE_URL}/dependencies")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    if "dependencies" not in data:
        print("❌ FAILED: Missing 'dependencies' key")
        return False
    
    deps = data["dependencies"]
    print(f"✅ Total dependencies: {len(deps)}")
    
    if deps:
        sample = deps[0]
        required_fields = ["id", "document", "target_field", "source", "source_label", "target_label"]
        for field in required_fields:
            if field not in sample:
                print(f"❌ FAILED: Dependency missing field '{field}'")
                return False
        
        print(f"✅ Dependency structure valid")
        print(f"   Sample: {sample['document']}.{sample['target_field']} <- {sample['source']}")
        print(f"   Labels: '{sample['target_label']}' <- '{sample['source_label']}'")
    
    # Filter by document
    print("\n   Testing filter by document=zayavlenie...")
    resp2 = requests.get(f"{BASE_URL}/dependencies?document=zayavlenie")
    if resp2.status_code == 200:
        deps2 = resp2.json().get("dependencies", [])
        print(f"   ✅ Found {len(deps2)} dependencies for zayavlenie")
        if deps2:
            all_zayav = all(d.get("document") == "zayavlenie" for d in deps2)
            if all_zayav:
                print(f"   ✅ All dependencies are for zayavlenie")
            else:
                print(f"   ❌ FAILED: Some dependencies are not for zayavlenie")
                return False
    
    print("\n✅ TEST 7 PASSED")
    return True


def test_package_generation():
    """TEST 8: POST /api/contracts/{id}/package -> 200 PDF (dependency doesn't break generation)"""
    print("\n=== TEST 8: POST /api/contracts/{id}/package ===")
    
    # Get a contract with master data
    resp = requests.get(f"{BASE_URL}/contracts/grid")
    if resp.status_code != 200:
        print("❌ FAILED: Cannot get contracts grid")
        return False
    
    rows = resp.json().get("rows", [])
    if not rows:
        print("❌ FAILED: No contracts available")
        return False
    
    # Find a contract with master data
    contract_id = None
    for row in rows:
        master = row.get("master", {})
        if master and any(str(v).strip() for v in master.values()):
            contract_id = row["id"]
            print(f"   Using contract: {contract_id}")
            print(f"   Name: {row.get('full_name', 'N/A')}")
            break
    
    if not contract_id:
        print("⚠️  WARNING: No contracts with master data, using first contract")
        contract_id = rows[0]["id"]
    
    # Generate package
    resp = requests.post(f"{BASE_URL}/contracts/{contract_id}/package", json={})
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        if resp.status_code == 500:
            print(f"   Detail: {resp.json().get('detail')}")
        return False
    
    content_type = resp.headers.get("Content-Type", "")
    if "application/pdf" not in content_type:
        print(f"❌ FAILED: Expected PDF, got Content-Type: {content_type}")
        return False
    
    pdf_size = len(resp.content)
    print(f"✅ PDF generated successfully")
    print(f"   Content-Type: {content_type}")
    print(f"   Size: {pdf_size} bytes")
    
    # Check PDF signature
    if resp.content[:4] == b'%PDF':
        print(f"✅ Valid PDF signature")
    else:
        print(f"❌ FAILED: Invalid PDF signature")
        return False
    
    print("✅ TEST 8 PASSED")
    return True


def test_delete_custom_column(custom_key):
    """TEST 9: DELETE /api/custom-columns/{key} -> 200, cleans dependencies"""
    print("\n=== TEST 9: DELETE /api/custom-columns/{key} ===")
    
    # First, check current dependencies
    resp = requests.get(f"{BASE_URL}/dependencies")
    if resp.status_code == 200:
        deps_before = resp.json().get("dependencies", [])
        deps_with_key = [d for d in deps_before if d.get("source") == custom_key]
        print(f"   Dependencies with source={custom_key}: {len(deps_with_key)}")
    
    # Delete the custom column
    resp = requests.delete(f"{BASE_URL}/custom-columns/{custom_key}")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    if not data.get("deleted"):
        print(f"❌ FAILED: Expected deleted=true")
        return False
    
    print(f"✅ Custom column deleted")
    
    # Verify it's removed from master-schema
    print("\n   Verifying removal from master-schema...")
    resp2 = requests.get(f"{BASE_URL}/master-schema")
    if resp2.status_code == 200:
        columns = resp2.json().get("columns", [])
        found = any(c.get("key") == custom_key for c in columns)
        if not found:
            print(f"✅ Custom column removed from master-schema")
        else:
            print(f"❌ FAILED: Custom column still in master-schema")
            return False
    
    # Verify dependencies are cleaned
    print("   Verifying dependencies cleanup...")
    resp3 = requests.get(f"{BASE_URL}/dependencies")
    if resp3.status_code == 200:
        deps_after = resp3.json().get("dependencies", [])
        deps_with_key_after = [d for d in deps_after if d.get("source") == custom_key]
        if len(deps_with_key_after) == 0:
            print(f"✅ Dependencies with source={custom_key} cleaned (0 remaining)")
        else:
            print(f"❌ FAILED: {len(deps_with_key_after)} dependencies still reference deleted column")
            return False
    
    print("\n✅ TEST 9 PASSED")
    return True


def test_delete_dependency(dep_id):
    """TEST 10: DELETE /api/dependencies/{id} -> 200"""
    print("\n=== TEST 10: DELETE /api/dependencies/{id} ===")
    
    resp = requests.delete(f"{BASE_URL}/dependencies/{dep_id}")
    print(f"Status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        return False
    
    data = resp.json()
    if not data.get("deleted"):
        print(f"❌ FAILED: Expected deleted=true")
        return False
    
    print(f"✅ Dependency deleted: {dep_id}")
    
    # Verify it's removed
    print("\n   Verifying removal...")
    resp2 = requests.get(f"{BASE_URL}/dependencies")
    if resp2.status_code == 200:
        deps = resp2.json().get("dependencies", [])
        found = any(d.get("id") == dep_id for d in deps)
        if not found:
            print(f"✅ Dependency removed from list")
        else:
            print(f"❌ FAILED: Dependency still in list")
            return False
    
    print("✅ TEST 10 PASSED")
    return True


def main():
    print("=" * 70)
    print("BACKEND TESTING: Banetskaya.by NEW FEATURE")
    print("Встроенная Excel-таблица данных + свои столбцы + зависимости")
    print("=" * 70)
    
    results = []
    custom_key = None
    dep_id = None
    
    # TEST 1: master-schema
    try:
        result = test_master_schema()
        results.append(("TEST 1: master-schema", result))
    except Exception as e:
        print(f"❌ TEST 1 EXCEPTION: {e}")
        results.append(("TEST 1: master-schema", False))
    
    # TEST 2: contracts/grid
    try:
        result = test_contracts_grid()
        results.append(("TEST 2: contracts/grid", result))
    except Exception as e:
        print(f"❌ TEST 2 EXCEPTION: {e}")
        results.append(("TEST 2: contracts/grid", False))
    
    # TEST 3: custom-columns create
    try:
        result = test_custom_columns_create()
        if isinstance(result, tuple):
            success, custom_key = result
            results.append(("TEST 3: custom-columns create", success))
        else:
            results.append(("TEST 3: custom-columns create", result))
    except Exception as e:
        print(f"❌ TEST 3 EXCEPTION: {e}")
        results.append(("TEST 3: custom-columns create", False))
    
    # TEST 3b: custom-columns duplicate
    try:
        result = test_custom_columns_duplicate()
        results.append(("TEST 3b: custom-columns duplicate", result))
    except Exception as e:
        print(f"❌ TEST 3b EXCEPTION: {e}")
        results.append(("TEST 3b: custom-columns duplicate", False))
    
    # TEST 3c: custom-columns empty label
    try:
        result = test_custom_columns_empty_label()
        results.append(("TEST 3c: custom-columns empty label", result))
    except Exception as e:
        print(f"❌ TEST 3c EXCEPTION: {e}")
        results.append(("TEST 3c: custom-columns empty label", False))
    
    # TEST 4: master-bulk update (requires custom_key)
    if custom_key:
        try:
            result = test_master_bulk_update(custom_key)
            results.append(("TEST 4: master-bulk update", result))
        except Exception as e:
            print(f"❌ TEST 4 EXCEPTION: {e}")
            results.append(("TEST 4: master-bulk update", False))
    else:
        print("\n⚠️  SKIPPING TEST 4: No custom_key available")
        results.append(("TEST 4: master-bulk update", None))
    
    # TEST 5: document-targets
    try:
        result = test_document_targets()
        results.append(("TEST 5: document-targets", result))
    except Exception as e:
        print(f"❌ TEST 5 EXCEPTION: {e}")
        results.append(("TEST 5: document-targets", False))
    
    # TEST 6: dependencies create (requires custom_key)
    if custom_key:
        try:
            result = test_dependencies_create(custom_key)
            if isinstance(result, tuple):
                success, dep_id = result
                results.append(("TEST 6: dependencies create", success))
            else:
                results.append(("TEST 6: dependencies create", result))
        except Exception as e:
            print(f"❌ TEST 6 EXCEPTION: {e}")
            results.append(("TEST 6: dependencies create", False))
    else:
        print("\n⚠️  SKIPPING TEST 6: No custom_key available")
        results.append(("TEST 6: dependencies create", None))
    
    # TEST 7: dependencies list
    try:
        result = test_dependencies_list()
        results.append(("TEST 7: dependencies list", result))
    except Exception as e:
        print(f"❌ TEST 7 EXCEPTION: {e}")
        results.append(("TEST 7: dependencies list", False))
    
    # TEST 8: package generation
    try:
        result = test_package_generation()
        results.append(("TEST 8: package generation", result))
    except Exception as e:
        print(f"❌ TEST 8 EXCEPTION: {e}")
        results.append(("TEST 8: package generation", False))
    
    # TEST 9: delete custom column (requires custom_key)
    if custom_key:
        try:
            result = test_delete_custom_column(custom_key)
            results.append(("TEST 9: delete custom-column", result))
        except Exception as e:
            print(f"❌ TEST 9 EXCEPTION: {e}")
            results.append(("TEST 9: delete custom-column", False))
    else:
        print("\n⚠️  SKIPPING TEST 9: No custom_key available")
        results.append(("TEST 9: delete custom-column", None))
    
    # TEST 10: delete dependency (requires dep_id)
    if dep_id:
        try:
            result = test_delete_dependency(dep_id)
            results.append(("TEST 10: delete dependency", result))
        except Exception as e:
            print(f"❌ TEST 10 EXCEPTION: {e}")
            results.append(("TEST 10: delete dependency", False))
    else:
        print("\n⚠️  SKIPPING TEST 10: No dep_id available")
        results.append(("TEST 10: delete dependency", None))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r is True)
    failed = sum(1 for _, r in results if r is False)
    skipped = sum(1 for _, r in results if r is None)
    total = len(results)
    
    for name, result in results:
        if result is True:
            print(f"✅ {name}")
        elif result is False:
            print(f"❌ {name}")
        else:
            print(f"⚠️  {name} (SKIPPED)")
    
    print(f"\nTotal: {total} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    
    if failed > 0:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)
    elif passed == total:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS SKIPPED")
        sys.exit(0)


if __name__ == "__main__":
    main()
