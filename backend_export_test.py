#!/usr/bin/env python3
"""
Backend API tests for Banetskaya.by - Focus on Excel Export endpoint and regression tests.
Tests the new GET /api/contracts/export endpoint with various filters and ensures existing endpoints still work.
"""
import requests
import sys
import json
from pathlib import Path

# Load backend URL from frontend/.env
env_file = Path("/app/frontend/.env")
BACKEND_URL = None
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BACKEND_URL = line.split("=", 1)[1].strip()
            break

if not BACKEND_URL:
    print("❌ REACT_APP_BACKEND_URL not found in /app/frontend/.env")
    sys.exit(1)

API_BASE = f"{BACKEND_URL}/api"
print(f"🔗 Testing API at: {API_BASE}\n")

# Track test results
passed = 0
failed = 0
test_results = []

def test(name, condition, details=""):
    """Record test result."""
    global passed, failed
    if condition:
        passed += 1
        print(f"✅ {name}")
        test_results.append({"name": name, "status": "PASS", "details": details})
        return True
    else:
        failed += 1
        print(f"❌ {name}")
        if details:
            print(f"   Details: {details}")
        test_results.append({"name": name, "status": "FAIL", "details": details})
        return False

def check_xlsx_valid(data):
    """Check if data is a valid XLSX file (ZIP format starting with 'PK')."""
    return data.startswith(b'PK')

def check_pdf_valid(data):
    """Check if data is a valid PDF."""
    return data.startswith(b'%PDF')

print("=" * 80)
print("BACKEND API TESTS - Excel Export & Regression Tests")
print("=" * 80)

# ============================================================================
# SETUP: Ensure demo data exists for testing
# ============================================================================
print("\n📋 SETUP: Ensuring demo data exists...")
try:
    resp = requests.post(f"{API_BASE}/seed-demo", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print(f"   Demo data ready (created: {data.get('created', 0)}, existing: {data.get('already', 0)})")
    else:
        print(f"   ⚠️  Warning: seed-demo returned {resp.status_code}")
except Exception as e:
    print(f"   ⚠️  Warning: Could not seed demo data: {e}")

# Get list of contracts to use for testing
try:
    resp = requests.get(f"{API_BASE}/contracts", timeout=10)
    all_contracts = resp.json() if resp.status_code == 200 else []
    print(f"   Total contracts in DB: {len(all_contracts)}")
except Exception as e:
    print(f"   ⚠️  Warning: Could not fetch contracts: {e}")
    all_contracts = []

print("-" * 80)

# ============================================================================
# TEST 1: GET /api/contracts/export (no filters)
# ============================================================================
print("\n🧪 TEST 1: GET /api/contracts/export (no filters)")
print("-" * 80)
try:
    resp = requests.get(f"{API_BASE}/contracts/export", timeout=30)
    
    # Check status code
    test(
        "Export endpoint returns 200",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
    
    # Check Content-Type
    content_type = resp.headers.get("Content-Type", "")
    test(
        "Content-Type is application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in content_type,
        f"Content-Type: {content_type}"
    )
    
    # Check Content-Disposition header
    content_disp = resp.headers.get("Content-Disposition", "")
    test(
        "Content-Disposition header contains filename",
        "filename" in content_disp.lower() and "реестр_договоров" in content_disp.lower(),
        f"Content-Disposition: {content_disp}"
    )
    
    # Check file content starts with 'PK' (valid XLSX/ZIP)
    body = resp.content
    test(
        "Response body is valid XLSX (starts with 'PK')",
        check_xlsx_valid(body),
        f"First 4 bytes: {body[:4]}"
    )
    
    # Check file size is reasonable (not empty)
    test(
        "File size is reasonable (>1KB)",
        len(body) > 1024,
        f"File size: {len(body)} bytes"
    )
    
except Exception as e:
    test("Export endpoint (no filters)", False, f"Exception: {e}")

print("-" * 80)

# ============================================================================
# TEST 2: GET /api/contracts/export?status=draft
# ============================================================================
print("\n🧪 TEST 2: GET /api/contracts/export?status=draft")
print("-" * 80)
try:
    resp = requests.get(f"{API_BASE}/contracts/export?status=draft", timeout=30)
    
    test(
        "Export with status=draft returns 200",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
    
    test(
        "Export draft: Content-Type is XLSX",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in resp.headers.get("Content-Type", ""),
        f"Content-Type: {resp.headers.get('Content-Type')}"
    )
    
    test(
        "Export draft: Body is valid XLSX",
        check_xlsx_valid(resp.content),
        f"First 4 bytes: {resp.content[:4]}"
    )
    
except Exception as e:
    test("Export with status=draft", False, f"Exception: {e}")

print("-" * 80)

# ============================================================================
# TEST 3: GET /api/contracts/export?status=final
# ============================================================================
print("\n🧪 TEST 3: GET /api/contracts/export?status=final")
print("-" * 80)
try:
    resp = requests.get(f"{API_BASE}/contracts/export?status=final", timeout=30)
    
    test(
        "Export with status=final returns 200",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
    
    test(
        "Export final: Content-Type is XLSX",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in resp.headers.get("Content-Type", ""),
        f"Content-Type: {resp.headers.get('Content-Type')}"
    )
    
    test(
        "Export final: Body is valid XLSX",
        check_xlsx_valid(resp.content),
        f"First 4 bytes: {resp.content[:4]}"
    )
    
except Exception as e:
    test("Export with status=final", False, f"Exception: {e}")

print("-" * 80)

# ============================================================================
# TEST 4: GET /api/contracts/export?q=<search term>
# ============================================================================
print("\n🧪 TEST 4: GET /api/contracts/export?q=<search term>")
print("-" * 80)

# Find a contract with a name to search for
search_term = None
if all_contracts:
    for contract in all_contracts:
        full_name = contract.get("full_name", "")
        if full_name and len(full_name) > 3:
            # Use first word of the name
            search_term = full_name.split()[0]
            print(f"   Using search term: '{search_term}' (from contract: {full_name})")
            break

if search_term:
    try:
        resp = requests.get(f"{API_BASE}/contracts/export?q={search_term}", timeout=30)
        
        test(
            f"Export with q='{search_term}' returns 200",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        test(
            "Export with search: Content-Type is XLSX",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in resp.headers.get("Content-Type", ""),
            f"Content-Type: {resp.headers.get('Content-Type')}"
        )
        
        test(
            "Export with search: Body is valid XLSX",
            check_xlsx_valid(resp.content),
            f"First 4 bytes: {resp.content[:4]}"
        )
        
    except Exception as e:
        test(f"Export with q='{search_term}'", False, f"Exception: {e}")
else:
    print("   ⚠️  Skipping search test: no contracts with names found")

print("-" * 80)

# ============================================================================
# TEST 5: REGRESSION - GET /api/contracts/{id} (ensure export doesn't intercept)
# ============================================================================
print("\n🧪 TEST 5: REGRESSION - GET /api/contracts/{id}")
print("-" * 80)

# Get a real contract ID
real_contract_id = None
if all_contracts:
    real_contract_id = all_contracts[0].get("id")
    print(f"   Using contract ID: {real_contract_id}")

if real_contract_id:
    try:
        resp = requests.get(f"{API_BASE}/contracts/{real_contract_id}", timeout=10)
        
        test(
            f"GET /api/contracts/{{id}} returns 200 (not intercepted by /export)",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        if resp.status_code == 200:
            data = resp.json()
            test(
                "GET /api/contracts/{id} returns contract object with 'id' field",
                "id" in data and data["id"] == real_contract_id,
                f"Response has id: {'id' in data}, matches: {data.get('id') == real_contract_id}"
            )
            
            test(
                "GET /api/contracts/{id} returns contract with 'fields' object",
                "fields" in data and isinstance(data["fields"], dict),
                f"Has fields: {'fields' in data}, is dict: {isinstance(data.get('fields'), dict)}"
            )
        
    except Exception as e:
        test(f"GET /api/contracts/{real_contract_id}", False, f"Exception: {e}")
else:
    print("   ⚠️  Skipping: no contracts found in DB")

print("-" * 80)

# ============================================================================
# TEST 6: REGRESSION - GET /api/contracts (list)
# ============================================================================
print("\n🧪 TEST 6: REGRESSION - GET /api/contracts (list)")
print("-" * 80)
try:
    resp = requests.get(f"{API_BASE}/contracts", timeout=10)
    
    test(
        "GET /api/contracts returns 200",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
    
    if resp.status_code == 200:
        data = resp.json()
        test(
            "GET /api/contracts returns array",
            isinstance(data, list),
            f"Type: {type(data)}"
        )
        
        test(
            "GET /api/contracts returns non-empty list",
            len(data) > 0,
            f"Count: {len(data)}"
        )
        
except Exception as e:
    test("GET /api/contracts", False, f"Exception: {e}")

print("-" * 80)

# ============================================================================
# TEST 7: Quick regression checks for other endpoints
# ============================================================================
print("\n🧪 TEST 7: Quick regression checks")
print("-" * 80)

# 7a. GET /api/stats
try:
    resp = requests.get(f"{API_BASE}/stats", timeout=10)
    test(
        "GET /api/stats returns 200",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
    
    if resp.status_code == 200:
        data = resp.json()
        test(
            "GET /api/stats has 'total' and 'drafts' fields",
            "total" in data and "drafts" in data,
            f"Fields: {list(data.keys())}"
        )
except Exception as e:
    test("GET /api/stats", False, f"Exception: {e}")

# 7b. POST /api/contracts/preview?format=pdf
try:
    payload = {
        "fields": {
            "full_name": "Тестовый Пользователь",
            "contract_number": "TEST001",
            "sign_date": "« 01 » января 2026"
        }
    }
    resp = requests.post(f"{API_BASE}/contracts/preview?format=pdf", json=payload, timeout=30)
    
    test(
        "POST /api/contracts/preview?format=pdf returns 200",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
    
    if resp.status_code == 200:
        test(
            "Preview PDF: Content-Type is application/pdf",
            "application/pdf" in resp.headers.get("Content-Type", ""),
            f"Content-Type: {resp.headers.get('Content-Type')}"
        )
        
        test(
            "Preview PDF: Body is valid PDF (starts with %PDF)",
            check_pdf_valid(resp.content),
            f"First 4 bytes: {resp.content[:4]}"
        )
        
except Exception as e:
    test("POST /api/contracts/preview?format=pdf", False, f"Exception: {e}")

# 7c. GET /api/presets
try:
    resp = requests.get(f"{API_BASE}/presets", timeout=10)
    test(
        "GET /api/presets returns 200",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
    
    if resp.status_code == 200:
        data = resp.json()
        test(
            "GET /api/presets returns array",
            isinstance(data, list),
            f"Type: {type(data)}"
        )
except Exception as e:
    test("GET /api/presets", False, f"Exception: {e}")

# 7d. POST /api/seed-demo (idempotency check)
try:
    resp = requests.post(f"{API_BASE}/seed-demo", timeout=10)
    test(
        "POST /api/seed-demo returns 200 (idempotent)",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
    
    if resp.status_code == 200:
        data = resp.json()
        test(
            "POST /api/seed-demo is idempotent (created=0 on second call)",
            data.get("created", -1) == 0,
            f"Created: {data.get('created')}, Already: {data.get('already')}"
        )
except Exception as e:
    test("POST /api/seed-demo", False, f"Exception: {e}")

print("-" * 80)

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"📊 Total:  {passed + failed}")
print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%" if (passed + failed) > 0 else "N/A")

if failed > 0:
    print("\n❌ FAILED TESTS:")
    for result in test_results:
        if result["status"] == "FAIL":
            print(f"  - {result['name']}")
            if result["details"]:
                print(f"    {result['details']}")

print("=" * 80)

# Exit with appropriate code
sys.exit(0 if failed == 0 else 1)
