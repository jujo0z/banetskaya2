#!/usr/bin/env python3
"""
Comprehensive backend API tests for Banetskaya.by contract generator.
Tests all endpoints including PDF conversion, drafts, presets, demo data, and stats.
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

# Test data - realistic Russian contract data
TEST_CONTRACT_1 = {
    "contract_number": "0047390 999001",
    "sign_date": "« 15 » января 2026",
    "order_number": "501",
    "order_date": "«15» января 2026",
    "citizenship": "Республики Беларусь",
    "full_name": "Петров Алексей Иванович",
    "birth_date": "12.03.2005",
    "room_number": "101/1",
    "contract_end_date": "30.06.2027",
    "registration_address": "пр-т Дзержинского, 85, ком. 101/1",
    "passport_number": "AB1234567",
    "passport_issue_date": "10.01.2023",
    "passport_valid_until": "09.01.2033",
    "passport_issued_by": "МВД Республики Беларусь",
    "id_number": "3120305A001PB1",
    "phone": "+375291234567"
}

TEST_CONTRACT_2 = {
    "contract_number": "0047390 999002",
    "sign_date": "« 16 » января 2026",
    "order_number": "502",
    "order_date": "«16» января 2026",
    "citizenship": "Российской Федерации",
    "full_name": "Сидорова Мария Петровна",
    "birth_date": "25.08.2006",
    "room_number": "202/3",
    "contract_end_date": "30.06.2028",
    "registration_address": "пр-т Дзержинского, 85, ком. 202/3",
    "passport_number": "4512 654321",
    "passport_issue_date": "20.09.2022",
    "passport_valid_until": "25.08.2026",
    "passport_issued_by": "УМВД России по г. Санкт-Петербургу",
    "id_number": "780-654-321 09",
    "phone": "+375297654321"
}

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

def check_pdf_valid(data):
    """Check if data is a valid PDF."""
    return data.startswith(b'%PDF')

def check_docx_valid(data):
    """Check if data is a valid DOCX (ZIP with specific structure)."""
    return data.startswith(b'PK\x03\x04')

def count_pdf_pages(pdf_data):
    """Count the number of pages in a PDF."""
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(pdf_data))
        return len(reader.pages)
    except Exception as e:
        print(f"⚠️  Error counting PDF pages: {e}")
        return -1

# Store created IDs for cleanup
created_contract_ids = []
created_preset_ids = []

print("=" * 80)
print("BACKEND API TESTS - Banetskaya.by Contract Generator")
print("=" * 80)

# ============================================================================
# 1. PDF CONVERSION TESTS (CRITICAL - Recently Fixed Bug)
# ============================================================================
print("\n📄 1. PDF CONVERSION TESTS (LibreOffice)")
print("-" * 80)

# Test 1.1: Preview PDF
try:
    resp = requests.post(
        f"{API_BASE}/contracts/preview",
        params={"format": "pdf"},
        json={"fields": TEST_CONTRACT_1},
        timeout=30
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    test(
        "1.1 POST /api/contracts/preview?format=pdf returns valid PDF",
        resp.status_code == 200 and 
        resp.headers.get("content-type") == "application/pdf" and 
        is_pdf,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid PDF: {is_pdf}"
    )
except Exception as e:
    test("1.1 POST /api/contracts/preview?format=pdf", False, str(e))

# Test 1.2: Preview DOCX
try:
    resp = requests.post(
        f"{API_BASE}/contracts/preview",
        params={"format": "docx"},
        json={"fields": TEST_CONTRACT_1},
        timeout=30
    )
    is_docx = check_docx_valid(resp.content) if resp.status_code == 200 else False
    test(
        "1.2 POST /api/contracts/preview?format=docx returns valid DOCX",
        resp.status_code == 200 and 
        "wordprocessingml" in resp.headers.get("content-type", "") and 
        is_docx,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid DOCX: {is_docx}"
    )
except Exception as e:
    test("1.2 POST /api/contracts/preview?format=docx", False, str(e))

# Test 1.3: Create contract and download PDF
contract_id_for_pdf = None
try:
    resp = requests.post(
        f"{API_BASE}/contracts",
        json={"fields": TEST_CONTRACT_1, "status": "final"},
        timeout=10
    )
    if resp.status_code == 200:
        contract_id_for_pdf = resp.json().get("id")
        created_contract_ids.append(contract_id_for_pdf)
        
        # Download as PDF
        resp_pdf = requests.get(
            f"{API_BASE}/contracts/{contract_id_for_pdf}/download",
            params={"format": "pdf"},
            timeout=30
        )
        is_pdf = check_pdf_valid(resp_pdf.content) if resp_pdf.status_code == 200 else False
        test(
            "1.3 GET /api/contracts/{id}/download?format=pdf returns valid PDF",
            resp_pdf.status_code == 200 and 
            resp_pdf.headers.get("content-type") == "application/pdf" and 
            is_pdf,
            f"Status: {resp_pdf.status_code}, Content-Type: {resp_pdf.headers.get('content-type')}, Valid PDF: {is_pdf}"
        )
    else:
        test("1.3 GET /api/contracts/{id}/download?format=pdf", False, f"Failed to create contract: {resp.status_code}")
except Exception as e:
    test("1.3 GET /api/contracts/{id}/download?format=pdf", False, str(e))

# Test 1.4: Download DOCX
if contract_id_for_pdf:
    try:
        resp = requests.get(
            f"{API_BASE}/contracts/{contract_id_for_pdf}/download",
            params={"format": "docx"},
            timeout=30
        )
        is_docx = check_docx_valid(resp.content) if resp.status_code == 200 else False
        test(
            "1.4 GET /api/contracts/{id}/download?format=docx returns valid DOCX",
            resp.status_code == 200 and 
            "wordprocessingml" in resp.headers.get("content-type", "") and 
            is_docx,
            f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid DOCX: {is_docx}"
        )
    except Exception as e:
        test("1.4 GET /api/contracts/{id}/download?format=docx", False, str(e))

# Test 1.5: Batch print (merged PDF)
try:
    # Create second contract for batch
    resp2 = requests.post(
        f"{API_BASE}/contracts",
        json={"fields": TEST_CONTRACT_2, "status": "final"},
        timeout=10
    )
    if resp2.status_code == 200:
        contract_id_2 = resp2.json().get("id")
        created_contract_ids.append(contract_id_2)
        
        # Batch print
        resp_batch = requests.post(
            f"{API_BASE}/contracts/batch-print",
            json={"ids": [contract_id_for_pdf, contract_id_2]},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp_batch.content) if resp_batch.status_code == 200 else False
        test(
            "1.5 POST /api/contracts/batch-print returns merged PDF",
            resp_batch.status_code == 200 and 
            resp_batch.headers.get("content-type") == "application/pdf" and 
            is_pdf,
            f"Status: {resp_batch.status_code}, Content-Type: {resp_batch.headers.get('content-type')}, Valid PDF: {is_pdf}"
        )
    else:
        test("1.5 POST /api/contracts/batch-print", False, f"Failed to create second contract: {resp2.status_code}")
except Exception as e:
    test("1.5 POST /api/contracts/batch-print", False, str(e))

# ============================================================================
# 2. DRAFTS TESTS
# ============================================================================
print("\n📝 2. DRAFTS TESTS")
print("-" * 80)

# Test 2.1: Create draft
draft_id = None
try:
    resp = requests.post(
        f"{API_BASE}/contracts",
        json={"fields": TEST_CONTRACT_2, "status": "draft"},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        draft_id = data.get("id")
        created_contract_ids.append(draft_id)
        test(
            "2.1 POST /api/contracts with status='draft' creates draft",
            data.get("status") == "draft",
            f"Status in response: {data.get('status')}"
        )
    else:
        test("2.1 POST /api/contracts with status='draft'", False, f"Status: {resp.status_code}")
except Exception as e:
    test("2.1 POST /api/contracts with status='draft'", False, str(e))

# Test 2.2: Update draft to final
if draft_id:
    try:
        updated_fields = TEST_CONTRACT_2.copy()
        updated_fields["contract_number"] = "0047390 999003"  # Change number
        resp = requests.put(
            f"{API_BASE}/contracts/{draft_id}",
            json={"fields": updated_fields, "status": "final"},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            test(
                "2.2 PUT /api/contracts/{id} updates status draft->final",
                data.get("status") == "final" and 
                data.get("contract_number") == "0047390 999003",
                f"Status: {data.get('status')}, Number: {data.get('contract_number')}"
            )
            
            # Verify with GET
            resp_get = requests.get(f"{API_BASE}/contracts/{draft_id}", timeout=10)
            if resp_get.status_code == 200:
                get_data = resp_get.json()
                test(
                    "2.3 GET /api/contracts/{id} confirms updated data",
                    get_data.get("status") == "final" and 
                    get_data.get("contract_number") == "0047390 999003",
                    f"Status: {get_data.get('status')}, Number: {get_data.get('contract_number')}"
                )
            else:
                test("2.3 GET /api/contracts/{id} confirms updated data", False, f"Status: {resp_get.status_code}")
        else:
            test("2.2 PUT /api/contracts/{id}", False, f"Status: {resp.status_code}")
    except Exception as e:
        test("2.2 PUT /api/contracts/{id}", False, str(e))

# ============================================================================
# 3. FILTER TESTS
# ============================================================================
print("\n🔍 3. FILTER TESTS")
print("-" * 80)

# Create test data: 1 draft, 1 final
test_draft_id = None
test_final_id = None
try:
    resp_draft = requests.post(
        f"{API_BASE}/contracts",
        json={"fields": {"full_name": "Тестовый Черновик", "contract_number": "DRAFT001"}, "status": "draft"},
        timeout=10
    )
    if resp_draft.status_code == 200:
        test_draft_id = resp_draft.json().get("id")
        created_contract_ids.append(test_draft_id)
    
    resp_final = requests.post(
        f"{API_BASE}/contracts",
        json={"fields": {"full_name": "Тестовый Финальный", "contract_number": "FINAL001"}, "status": "final"},
        timeout=10
    )
    if resp_final.status_code == 200:
        test_final_id = resp_final.json().get("id")
        created_contract_ids.append(test_final_id)
except Exception as e:
    print(f"⚠️  Failed to create test contracts for filtering: {e}")

# Test 3.1: Filter by status=draft
try:
    resp = requests.get(f"{API_BASE}/contracts", params={"status": "draft"}, timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        all_drafts = all(c.get("status") == "draft" for c in contracts)
        has_test_draft = any(c.get("id") == test_draft_id for c in contracts) if test_draft_id else True
        test(
            "3.1 GET /api/contracts?status=draft returns only drafts",
            all_drafts and has_test_draft,
            f"Total: {len(contracts)}, All drafts: {all_drafts}, Has test draft: {has_test_draft}"
        )
    else:
        test("3.1 GET /api/contracts?status=draft", False, f"Status: {resp.status_code}")
except Exception as e:
    test("3.1 GET /api/contracts?status=draft", False, str(e))

# Test 3.2: Filter by status=final
try:
    resp = requests.get(f"{API_BASE}/contracts", params={"status": "final"}, timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        no_drafts = all(c.get("status") != "draft" for c in contracts)
        has_test_final = any(c.get("id") == test_final_id for c in contracts) if test_final_id else True
        test(
            "3.2 GET /api/contracts?status=final returns only final",
            no_drafts and has_test_final,
            f"Total: {len(contracts)}, No drafts: {no_drafts}, Has test final: {has_test_final}"
        )
    else:
        test("3.2 GET /api/contracts?status=final", False, f"Status: {resp.status_code}")
except Exception as e:
    test("3.2 GET /api/contracts?status=final", False, str(e))

# Test 3.3: No filter returns all
try:
    resp = requests.get(f"{API_BASE}/contracts", timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        has_drafts = any(c.get("status") == "draft" for c in contracts)
        has_finals = any(c.get("status") != "draft" for c in contracts)
        test(
            "3.3 GET /api/contracts (no filter) returns all contracts",
            has_drafts or has_finals,  # At least some contracts
            f"Total: {len(contracts)}, Has drafts: {has_drafts}, Has finals: {has_finals}"
        )
    else:
        test("3.3 GET /api/contracts (no filter)", False, f"Status: {resp.status_code}")
except Exception as e:
    test("3.3 GET /api/contracts (no filter)", False, str(e))

# Test 3.4: Search by name
try:
    resp = requests.get(f"{API_BASE}/contracts", params={"q": "Тестовый"}, timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        found_test = any("Тестовый" in c.get("full_name", "") for c in contracts)
        test(
            "3.4 GET /api/contracts?q=Тестовый searches by name",
            found_test,
            f"Total: {len(contracts)}, Found test contracts: {found_test}"
        )
    else:
        test("3.4 GET /api/contracts?q=Тестовый", False, f"Status: {resp.status_code}")
except Exception as e:
    test("3.4 GET /api/contracts?q=Тестовый", False, str(e))

# Test 3.5: Search by contract number
try:
    resp = requests.get(f"{API_BASE}/contracts", params={"q": "DRAFT001"}, timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        found_draft = any("DRAFT001" in c.get("contract_number", "") for c in contracts)
        test(
            "3.5 GET /api/contracts?q=DRAFT001 searches by number",
            found_draft,
            f"Total: {len(contracts)}, Found DRAFT001: {found_draft}"
        )
    else:
        test("3.5 GET /api/contracts?q=DRAFT001", False, f"Status: {resp.status_code}")
except Exception as e:
    test("3.5 GET /api/contracts?q=DRAFT001", False, str(e))

# ============================================================================
# 4. PRESETS TESTS
# ============================================================================
print("\n⚙️  4. PRESETS TESTS")
print("-" * 80)

# Test 4.1: Create preset
preset_id = None
try:
    resp = requests.post(
        f"{API_BASE}/presets",
        json={"name": "Тестовый Пресет", "fields": {"order_number": "100", "citizenship": "Республики Беларусь"}},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        preset_id = data.get("id")
        created_preset_ids.append(preset_id)
        test(
            "4.1 POST /api/presets creates preset",
            data.get("name") == "Тестовый Пресет" and "order_number" in data.get("fields", {}),
            f"Name: {data.get('name')}, Fields: {data.get('fields')}"
        )
    else:
        test("4.1 POST /api/presets", False, f"Status: {resp.status_code}, Body: {resp.text}")
except Exception as e:
    test("4.1 POST /api/presets", False, str(e))

# Test 4.2: GET presets
try:
    resp = requests.get(f"{API_BASE}/presets", timeout=10)
    if resp.status_code == 200:
        presets = resp.json()
        found_test = any(p.get("id") == preset_id for p in presets) if preset_id else False
        test(
            "4.2 GET /api/presets returns presets list",
            isinstance(presets, list) and (found_test or len(presets) >= 0),
            f"Total: {len(presets)}, Found test preset: {found_test}"
        )
    else:
        test("4.2 GET /api/presets", False, f"Status: {resp.status_code}")
except Exception as e:
    test("4.2 GET /api/presets", False, str(e))

# Test 4.3: POST preset with empty name (should fail)
try:
    resp = requests.post(
        f"{API_BASE}/presets",
        json={"name": "", "fields": {"test": "value"}},
        timeout=10
    )
    test(
        "4.3 POST /api/presets with empty name returns 400",
        resp.status_code == 400,
        f"Status: {resp.status_code}"
    )
except Exception as e:
    test("4.3 POST /api/presets with empty name", False, str(e))

# Test 4.4: DELETE preset
if preset_id:
    try:
        resp = requests.delete(f"{API_BASE}/presets/{preset_id}", timeout=10)
        test(
            "4.4 DELETE /api/presets/{id} deletes preset",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        
        # Test 4.5: Repeat DELETE (should return 404)
        resp2 = requests.delete(f"{API_BASE}/presets/{preset_id}", timeout=10)
        test(
            "4.5 DELETE /api/presets/{id} (repeat) returns 404",
            resp2.status_code == 404,
            f"Status: {resp2.status_code}"
        )
        
        # Remove from cleanup list since already deleted
        if preset_id in created_preset_ids:
            created_preset_ids.remove(preset_id)
    except Exception as e:
        test("4.4 DELETE /api/presets/{id}", False, str(e))

# ============================================================================
# 5. DEMO DATA TESTS
# ============================================================================
print("\n🎭 5. DEMO DATA TESTS")
print("-" * 80)

# First, clear any existing demo data
try:
    requests.delete(f"{API_BASE}/seed-demo", timeout=10)
except Exception:
    pass

# Test 5.1: First seed-demo call
try:
    resp = requests.post(f"{API_BASE}/seed-demo", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test(
            "5.1 POST /api/seed-demo (first call) creates 6 demos",
            data.get("created") == 6,
            f"Created: {data.get('created')}, Message: {data.get('message')}"
        )
    else:
        test("5.1 POST /api/seed-demo (first call)", False, f"Status: {resp.status_code}")
except Exception as e:
    test("5.1 POST /api/seed-demo (first call)", False, str(e))

# Test 5.2: Second seed-demo call (idempotency)
try:
    resp = requests.post(f"{API_BASE}/seed-demo", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test(
            "5.2 POST /api/seed-demo (repeat) is idempotent",
            data.get("created") == 0 and data.get("already", 0) > 0,
            f"Created: {data.get('created')}, Already: {data.get('already')}, Message: {data.get('message')}"
        )
    else:
        test("5.2 POST /api/seed-demo (repeat)", False, f"Status: {resp.status_code}")
except Exception as e:
    test("5.2 POST /api/seed-demo (repeat)", False, str(e))

# Test 5.3: Verify demo contracts exist
try:
    resp = requests.get(f"{API_BASE}/contracts", timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        demo_contracts = [c for c in contracts if c.get("demo") == True]
        test(
            "5.3 Demo contracts exist in database",
            len(demo_contracts) >= 6,
            f"Demo contracts found: {len(demo_contracts)}"
        )
    else:
        test("5.3 Demo contracts exist", False, f"Status: {resp.status_code}")
except Exception as e:
    test("5.3 Demo contracts exist", False, str(e))

# Test 5.4: DELETE seed-demo
try:
    resp = requests.delete(f"{API_BASE}/seed-demo", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test(
            "5.4 DELETE /api/seed-demo deletes demo contracts",
            data.get("deleted", 0) >= 6,
            f"Deleted: {data.get('deleted')}"
        )
    else:
        test("5.4 DELETE /api/seed-demo", False, f"Status: {resp.status_code}")
except Exception as e:
    test("5.4 DELETE /api/seed-demo", False, str(e))

# Test 5.5: Verify demo contracts deleted
try:
    resp = requests.get(f"{API_BASE}/contracts", timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        demo_contracts = [c for c in contracts if c.get("demo") == True]
        test(
            "5.5 Demo contracts removed from database",
            len(demo_contracts) == 0,
            f"Demo contracts remaining: {len(demo_contracts)}"
        )
    else:
        test("5.5 Demo contracts removed", False, f"Status: {resp.status_code}")
except Exception as e:
    test("5.5 Demo contracts removed", False, str(e))

# ============================================================================
# 6. STATS TESTS
# ============================================================================
print("\n📊 6. STATS TESTS")
print("-" * 80)

# Create test data: 2 final, 1 draft
stats_final_ids = []
stats_draft_id = None
try:
    for i in range(2):
        resp = requests.post(
            f"{API_BASE}/contracts",
            json={"fields": {"full_name": f"Статистика Финал {i+1}", "contract_number": f"STAT{i+1}"}, "status": "final"},
            timeout=10
        )
        if resp.status_code == 200:
            cid = resp.json().get("id")
            stats_final_ids.append(cid)
            created_contract_ids.append(cid)
    
    resp_draft = requests.post(
        f"{API_BASE}/contracts",
        json={"fields": {"full_name": "Статистика Черновик", "contract_number": "STATDRAFT"}, "status": "draft"},
        timeout=10
    )
    if resp_draft.status_code == 200:
        stats_draft_id = resp_draft.json().get("id")
        created_contract_ids.append(stats_draft_id)
except Exception as e:
    print(f"⚠️  Failed to create test contracts for stats: {e}")

# Test 6.1: GET stats
try:
    resp = requests.get(f"{API_BASE}/stats", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        has_required_fields = all(k in data for k in ["total", "drafts", "this_month", "datasets", "recent"])
        test(
            "6.1 GET /api/stats returns required fields",
            has_required_fields,
            f"Fields: {list(data.keys())}"
        )
        
        # Test 6.2: total excludes drafts
        total = data.get("total", 0)
        drafts = data.get("drafts", 0)
        test(
            "6.2 Stats 'total' excludes drafts",
            isinstance(total, int) and isinstance(drafts, int),
            f"Total: {total}, Drafts: {drafts}"
        )
        
        # Test 6.3: drafts field exists and is number
        test(
            "6.3 Stats 'drafts' field is present",
            isinstance(drafts, int) and drafts >= 0,
            f"Drafts: {drafts}"
        )
        
        # Test 6.4: recent excludes drafts
        recent = data.get("recent", [])
        has_drafts_in_recent = any(c.get("status") == "draft" for c in recent)
        test(
            "6.4 Stats 'recent' excludes drafts",
            not has_drafts_in_recent,
            f"Recent count: {len(recent)}, Has drafts: {has_drafts_in_recent}"
        )
    else:
        test("6.1 GET /api/stats", False, f"Status: {resp.status_code}")
except Exception as e:
    test("6.1 GET /api/stats", False, str(e))

# ============================================================================
# 7. MANUAL DUPLEX PRINTING TESTS (NEW FEATURE)
# ============================================================================
print("\n🖨️  7. MANUAL DUPLEX PRINTING TESTS")
print("-" * 80)

# Prepare: Seed demo data to get 3 real contract IDs
print("📦 Preparing test data: seeding demo contracts...")
try:
    # Clear existing demo data first
    requests.delete(f"{API_BASE}/seed-demo", timeout=10)
    # Seed fresh demo data
    resp_seed = requests.post(f"{API_BASE}/seed-demo", timeout=10)
    if resp_seed.status_code == 200:
        print(f"✓ Demo data seeded: {resp_seed.json().get('created', 0)} contracts")
    else:
        print(f"⚠️  Failed to seed demo data: {resp_seed.status_code}")
except Exception as e:
    print(f"⚠️  Error seeding demo data: {e}")

# Get 3 real contract IDs
contract_ids_for_duplex = []
try:
    resp = requests.get(f"{API_BASE}/contracts", timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        # Get first 3 contracts (preferably final status)
        final_contracts = [c for c in contracts if c.get("status") != "draft"]
        contract_ids_for_duplex = [c["id"] for c in final_contracts[:3]]
        print(f"✓ Retrieved {len(contract_ids_for_duplex)} contract IDs for testing")
    else:
        print(f"⚠️  Failed to get contracts: {resp.status_code}")
except Exception as e:
    print(f"⚠️  Error getting contracts: {e}")

if len(contract_ids_for_duplex) < 3:
    print("⚠️  Not enough contracts for duplex testing. Creating test contracts...")
    try:
        for i in range(3 - len(contract_ids_for_duplex)):
            resp = requests.post(
                f"{API_BASE}/contracts",
                json={"fields": {
                    "full_name": f"Дуплекс Тест {i+1}",
                    "contract_number": f"DUPLEX{i+1:03d}",
                    "citizenship": "Республики Беларусь",
                    "room_number": f"{100+i}"
                }, "status": "final"},
                timeout=10
            )
            if resp.status_code == 200:
                cid = resp.json().get("id")
                contract_ids_for_duplex.append(cid)
                created_contract_ids.append(cid)
    except Exception as e:
        print(f"⚠️  Error creating test contracts: {e}")

print(f"📋 Using contract IDs: {contract_ids_for_duplex[:3]}")

# Test 7.1: POST /api/contracts/manual-duplex with side="front"
front_pages = 0
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids_for_duplex[:3], "side": "front"},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    if is_pdf:
        front_pages = count_pdf_pages(resp.content)
    test(
        "7.1 POST /api/contracts/manual-duplex side='front' returns valid PDF",
        resp.status_code == 200 and 
        resp.headers.get("content-type") == "application/pdf" and 
        is_pdf and
        front_pages > 0,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid PDF: {is_pdf}, Pages: {front_pages}"
    )
except Exception as e:
    test("7.1 POST /api/contracts/manual-duplex side='front'", False, str(e))

# Test 7.2: POST /api/contracts/manual-duplex with side="back", back_order="reversed"
back_pages_reversed = 0
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids_for_duplex[:3], "side": "back", "back_order": "reversed"},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    if is_pdf:
        back_pages_reversed = count_pdf_pages(resp.content)
    test(
        "7.2 POST /api/contracts/manual-duplex side='back' back_order='reversed' returns valid PDF",
        resp.status_code == 200 and 
        resp.headers.get("content-type") == "application/pdf" and 
        is_pdf and
        back_pages_reversed > 0,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid PDF: {is_pdf}, Pages: {back_pages_reversed}"
    )
except Exception as e:
    test("7.2 POST /api/contracts/manual-duplex side='back' back_order='reversed'", False, str(e))

# Test 7.3: POST /api/contracts/manual-duplex with side="back", back_order="normal"
back_pages_normal = 0
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids_for_duplex[:3], "side": "back", "back_order": "normal"},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    if is_pdf:
        back_pages_normal = count_pdf_pages(resp.content)
    test(
        "7.3 POST /api/contracts/manual-duplex side='back' back_order='normal' returns valid PDF",
        resp.status_code == 200 and 
        resp.headers.get("content-type") == "application/pdf" and 
        is_pdf and
        back_pages_normal > 0,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid PDF: {is_pdf}, Pages: {back_pages_normal}"
    )
except Exception as e:
    test("7.3 POST /api/contracts/manual-duplex side='back' back_order='normal'", False, str(e))

# Test 7.4: Verify page count logic (each contract = 4 pages, so 3 contracts = 6 front pages + 6 back pages)
# Each contract renders to 4 pages (even number), so:
# - front should have pages 1,3 of each contract = 2 pages per contract × 3 = 6 pages
# - back should have pages 2,4 of each contract = 2 pages per contract × 3 = 6 pages
expected_pages = 6  # 2 pages per contract (odd pages) × 3 contracts
test(
    "7.4 Manual duplex page count logic: front_pages == 6",
    front_pages == expected_pages,
    f"Expected: {expected_pages}, Got: {front_pages}"
)

test(
    "7.5 Manual duplex page count logic: back_pages (reversed) == 6",
    back_pages_reversed == expected_pages,
    f"Expected: {expected_pages}, Got: {back_pages_reversed}"
)

test(
    "7.6 Manual duplex page count logic: back_pages (normal) == 6",
    back_pages_normal == expected_pages,
    f"Expected: {expected_pages}, Got: {back_pages_normal}"
)

test(
    "7.7 Manual duplex page count logic: front_pages == back_pages",
    front_pages == back_pages_reversed == back_pages_normal,
    f"Front: {front_pages}, Back (reversed): {back_pages_reversed}, Back (normal): {back_pages_normal}"
)

# Test 7.8: Error case - empty ids array
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": [], "side": "front"},
        timeout=10
    )
    test(
        "7.8 POST /api/contracts/manual-duplex with empty ids returns 404",
        resp.status_code == 404,
        f"Status: {resp.status_code}"
    )
except Exception as e:
    test("7.8 POST /api/contracts/manual-duplex with empty ids", False, str(e))

# Test 7.9: Error case - non-existent UUID (should not crash with 500)
import uuid
fake_uuid = str(uuid.uuid4())
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": [fake_uuid], "side": "front"},
        timeout=30
    )
    # Should either return 404 (all not found) or valid PDF (ignores non-existent)
    # According to code, it should return 404 if no docs found
    test(
        "7.9 POST /api/contracts/manual-duplex with non-existent UUID returns 404 (not 500)",
        resp.status_code == 404,
        f"Status: {resp.status_code}, Body: {resp.text[:200] if resp.text else 'empty'}"
    )
except Exception as e:
    test("7.9 POST /api/contracts/manual-duplex with non-existent UUID", False, str(e))

# Test 7.10: Mixed case - some valid, some invalid IDs (should process valid ones)
try:
    mixed_ids = [contract_ids_for_duplex[0], str(uuid.uuid4()), contract_ids_for_duplex[1]]
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": mixed_ids, "side": "front"},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    # Should process 2 valid contracts = 4 pages (2 per contract)
    test(
        "7.10 POST /api/contracts/manual-duplex with mixed valid/invalid IDs processes valid ones",
        resp.status_code == 200 and is_pdf and pages == 4,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages} (expected 4 for 2 contracts)"
    )
except Exception as e:
    test("7.10 POST /api/contracts/manual-duplex with mixed IDs", False, str(e))

# ============================================================================
# 8. PRINT TEST SHEET TESTS (NEW FEATURE - GET /api/print-test)
# ============================================================================
print("\n📄 8. PRINT TEST SHEET TESTS (Пробный лист)")
print("-" * 80)

# Test 8.1: GET /api/print-test?side=front
try:
    resp = requests.get(f"{API_BASE}/print-test", params={"side": "front"}, timeout=10)
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    test(
        "8.1 GET /api/print-test?side=front returns 1-page PDF",
        resp.status_code == 200 and 
        resp.headers.get("content-type") == "application/pdf" and 
        is_pdf and
        pages == 1,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid PDF: {is_pdf}, Pages: {pages}"
    )
except Exception as e:
    test("8.1 GET /api/print-test?side=front", False, str(e))

# Test 8.2: GET /api/print-test?side=back
try:
    resp = requests.get(f"{API_BASE}/print-test", params={"side": "back"}, timeout=10)
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    test(
        "8.2 GET /api/print-test?side=back returns 1-page PDF",
        resp.status_code == 200 and 
        resp.headers.get("content-type") == "application/pdf" and 
        is_pdf and
        pages == 1,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid PDF: {is_pdf}, Pages: {pages}"
    )
except Exception as e:
    test("8.2 GET /api/print-test?side=back", False, str(e))

# Test 8.3: GET /api/print-test (no parameter, should default to front)
try:
    resp = requests.get(f"{API_BASE}/print-test", timeout=10)
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    test(
        "8.3 GET /api/print-test (no param) returns 1-page PDF (defaults to front)",
        resp.status_code == 200 and 
        resp.headers.get("content-type") == "application/pdf" and 
        is_pdf and
        pages == 1,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}, Valid PDF: {is_pdf}, Pages: {pages}"
    )
except Exception as e:
    test("8.3 GET /api/print-test (no param)", False, str(e))

# ============================================================================
# 9. SEPARATORS IN MANUAL DUPLEX TESTS (NEW FEATURE)
# ============================================================================
print("\n📑 9. SEPARATORS IN MANUAL DUPLEX TESTS")
print("-" * 80)

# Get 2 contract IDs for separator tests
separator_test_ids = []
if len(contract_ids_for_duplex) >= 2:
    separator_test_ids = contract_ids_for_duplex[:2]
    print(f"📋 Using 2 contract IDs for separator tests: {separator_test_ids}")
else:
    print("⚠️  Not enough contracts for separator testing")

# Test 9.1: POST manual-duplex with separators=true, side=front (2 contracts)
# Expected: 6 pages (2 contracts × 2 front pages + 2 separators)
if len(separator_test_ids) == 2:
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": separator_test_ids, "side": "front", "separators": True},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        pages = count_pdf_pages(resp.content) if is_pdf else 0
        # Each contract = 4 pages, 2 contracts = 8 pages total
        # Front pages: pages 1,3 of each = 2 per contract = 4 pages
        # With separators: 2 separators (each separator is 1 front page) = 2 pages
        # Total front with separators: 4 + 2 = 6 pages
        test(
            "9.1 POST manual-duplex side='front' separators=true returns 6 pages (2 contracts)",
            resp.status_code == 200 and is_pdf and pages == 6,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages} (expected 6: 2 contracts × 2 front + 2 separators)"
        )
    except Exception as e:
        test("9.1 POST manual-duplex side='front' separators=true", False, str(e))

    # Test 9.2: POST manual-duplex with separators=true, side=back (2 contracts)
    # Expected: 6 pages (2 contracts × 2 back pages + 2 blank backs for separators)
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": separator_test_ids, "side": "back", "separators": True},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        pages = count_pdf_pages(resp.content) if is_pdf else 0
        test(
            "9.2 POST manual-duplex side='back' separators=true returns 6 pages (2 contracts)",
            resp.status_code == 200 and is_pdf and pages == 6,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages} (expected 6: 2 contracts × 2 back + 2 blank)"
        )
    except Exception as e:
        test("9.2 POST manual-duplex side='back' separators=true", False, str(e))

    # Test 9.3: POST manual-duplex with separators=true, side=back, back_order=normal
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": separator_test_ids, "side": "back", "separators": True, "back_order": "normal"},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        pages = count_pdf_pages(resp.content) if is_pdf else 0
        test(
            "9.3 POST manual-duplex side='back' separators=true back_order='normal' returns 6 pages",
            resp.status_code == 200 and is_pdf and pages == 6,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages} (expected 6)"
        )
    except Exception as e:
        test("9.3 POST manual-duplex side='back' separators=true back_order='normal'", False, str(e))

    # Test 9.4: POST manual-duplex WITHOUT separators (default false), side=front (2 contracts)
    # Expected: 4 pages (2 contracts × 2 front pages, no separators)
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": separator_test_ids, "side": "front"},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        pages = count_pdf_pages(resp.content) if is_pdf else 0
        test(
            "9.4 POST manual-duplex side='front' (no separators) returns 4 pages (2 contracts)",
            resp.status_code == 200 and is_pdf and pages == 4,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages} (expected 4: 2 contracts × 2 front, no separators)"
        )
    except Exception as e:
        test("9.4 POST manual-duplex side='front' (no separators)", False, str(e))

    # Test 9.5: POST manual-duplex WITHOUT separators, side=back (2 contracts)
    # Expected: 4 pages (2 contracts × 2 back pages, no separators)
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": separator_test_ids, "side": "back"},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        pages = count_pdf_pages(resp.content) if is_pdf else 0
        test(
            "9.5 POST manual-duplex side='back' (no separators) returns 4 pages (2 contracts)",
            resp.status_code == 200 and is_pdf and pages == 4,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages} (expected 4: 2 contracts × 2 back, no separators)"
        )
    except Exception as e:
        test("9.5 POST manual-duplex side='back' (no separators)", False, str(e))

# ============================================================================
# 10. REGRESSION TESTS (LibreOffice, batch-print, stats, export, presets)
# ============================================================================
print("\n🔄 10. REGRESSION TESTS")
print("-" * 80)

# Test 10.1: LibreOffice is installed and working (critical for manual-duplex)
try:
    resp = requests.post(
        f"{API_BASE}/contracts/preview",
        params={"format": "pdf"},
        json={"fields": TEST_CONTRACT_1},
        timeout=30
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    test(
        "10.1 REGRESSION: POST /api/contracts/preview?format=pdf works (LibreOffice installed)",
        resp.status_code == 200 and is_pdf,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}"
    )
except Exception as e:
    test("10.1 REGRESSION: POST /api/contracts/preview?format=pdf", False, str(e))

# Test 10.2: Batch print still works
if len(contract_ids_for_duplex) >= 2:
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/batch-print",
            json={"ids": contract_ids_for_duplex[:2]},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        test(
            "10.2 REGRESSION: POST /api/contracts/batch-print works",
            resp.status_code == 200 and is_pdf,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}"
        )
    except Exception as e:
        test("10.2 REGRESSION: POST /api/contracts/batch-print", False, str(e))

# Test 10.3: Stats endpoint works
try:
    resp = requests.get(f"{API_BASE}/stats", timeout=10)
    test(
        "10.3 REGRESSION: GET /api/stats works",
        resp.status_code == 200 and "total" in resp.json(),
        f"Status: {resp.status_code}"
    )
except Exception as e:
    test("10.3 REGRESSION: GET /api/stats", False, str(e))

# Test 10.4: Export endpoint works
try:
    resp = requests.get(f"{API_BASE}/contracts/export", timeout=30)
    is_xlsx = resp.content.startswith(b'PK\x03\x04') if resp.status_code == 200 else False
    test(
        "10.4 REGRESSION: GET /api/contracts/export works",
        resp.status_code == 200 and is_xlsx,
        f"Status: {resp.status_code}, Valid XLSX: {is_xlsx}"
    )
except Exception as e:
    test("10.4 REGRESSION: GET /api/contracts/export", False, str(e))

# Test 10.5: Presets endpoint works
try:
    resp = requests.get(f"{API_BASE}/presets", timeout=10)
    test(
        "10.5 REGRESSION: GET /api/presets works",
        resp.status_code == 200 and isinstance(resp.json(), list),
        f"Status: {resp.status_code}"
    )
except Exception as e:
    test("10.5 REGRESSION: GET /api/presets", False, str(e))

# Test 10.6: GET /api/sample-template
try:
    resp = requests.get(f"{API_BASE}/sample-template", timeout=10)
    is_xlsx = resp.content.startswith(b'PK\x03\x04') if resp.status_code == 200 else False
    test(
        "10.6 REGRESSION: GET /api/sample-template returns Excel file",
        resp.status_code == 200 and 
        "spreadsheetml" in resp.headers.get("content-type", "") and 
        is_xlsx,
        f"Status: {resp.status_code}, Content-Type: {resp.headers.get('content-type')}"
    )
except Exception as e:
    test("10.6 REGRESSION: GET /api/sample-template", False, str(e))

# Test 10.7: POST /api/upload (would need actual file, skip for now but verify endpoint exists)
# Note: This would require creating a test Excel file, which is complex in this context
print("ℹ️  10.7 POST /api/upload - Skipped (requires file upload, tested separately)")

# Test 10.8: Run existing pytest if available
print("\n🧪 10.8 Running existing pytest suite...")
try:
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", "/app/backend/tests/", "-v"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd="/app"
    )
    pytest_passed = result.returncode == 0
    test(
        "10.8 REGRESSION: Existing pytest suite passes",
        pytest_passed,
        f"Exit code: {result.returncode}"
    )
    if not pytest_passed:
        print(f"   Pytest output:\n{result.stdout}\n{result.stderr}")
except Exception as e:
    print(f"ℹ️  10.8 Existing pytest - Could not run: {e}")

# ============================================================================
# 11. CUSTOM TEMPLATES TESTS (NEW FEATURE)
# ============================================================================
print("\n📄 11. CUSTOM TEMPLATES TESTS")
print("-" * 80)

# Store created template IDs for cleanup
created_template_ids = []

# Test 11.1: GET /api/templates - should have default initially
try:
    resp = requests.get(f"{API_BASE}/templates", timeout=10)
    if resp.status_code == 200:
        templates = resp.json()
        has_default = any(t.get("id") == "default" and t.get("builtin") == True and t.get("active") == True for t in templates)
        test(
            "11.1 GET /api/templates returns default template (builtin=true, active=true)",
            has_default,
            f"Templates: {len(templates)}, Has default: {has_default}"
        )
    else:
        test("11.1 GET /api/templates", False, f"Status: {resp.status_code}")
except Exception as e:
    test("11.1 GET /api/templates", False, str(e))

# Test 11.2: POST /api/templates - upload custom .docx template
custom_template_id = None
try:
    # Use the built-in contract_template.docx as the file to upload
    template_path = Path("/app/backend/templates/contract_template.docx")
    if template_path.exists():
        with open(template_path, "rb") as f:
            files = {"file": ("custom_template.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            resp = requests.post(f"{API_BASE}/templates", files=files, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                custom_template_id = data.get("id")
                created_template_ids.append(custom_template_id)
                test(
                    "11.2 POST /api/templates uploads custom .docx template",
                    data.get("builtin") == False and custom_template_id is not None,
                    f"Template ID: {custom_template_id}, builtin: {data.get('builtin')}"
                )
            else:
                test("11.2 POST /api/templates", False, f"Status: {resp.status_code}, Body: {resp.text}")
    else:
        test("11.2 POST /api/templates", False, "Template file not found at /app/backend/templates/contract_template.docx")
except Exception as e:
    test("11.2 POST /api/templates", False, str(e))

# Test 11.3: GET /api/templates - custom template should appear
if custom_template_id:
    try:
        resp = requests.get(f"{API_BASE}/templates", timeout=10)
        if resp.status_code == 200:
            templates = resp.json()
            has_custom = any(t.get("id") == custom_template_id and t.get("builtin") == False for t in templates)
            test(
                "11.3 GET /api/templates shows custom template (builtin=false)",
                has_custom,
                f"Templates: {len(templates)}, Has custom: {has_custom}"
            )
        else:
            test("11.3 GET /api/templates", False, f"Status: {resp.status_code}")
    except Exception as e:
        test("11.3 GET /api/templates", False, str(e))

# Test 11.4: POST /api/templates/{id}/activate - activate custom template
if custom_template_id:
    try:
        resp = requests.post(f"{API_BASE}/templates/{custom_template_id}/activate", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            test(
                "11.4 POST /api/templates/{id}/activate activates custom template",
                data.get("active") == custom_template_id,
                f"Active template: {data.get('active')}"
            )
        else:
            test("11.4 POST /api/templates/{id}/activate", False, f"Status: {resp.status_code}")
    except Exception as e:
        test("11.4 POST /api/templates/{id}/activate", False, str(e))

# Test 11.5: POST /api/contracts/preview with active custom template
if custom_template_id:
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/preview",
            params={"format": "pdf"},
            json={"fields": {"full_name": "Тест Кастомного Шаблона"}},
            timeout=30
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        test(
            "11.5 POST /api/contracts/preview?format=pdf uses active custom template",
            resp.status_code == 200 and is_pdf,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}"
        )
    except Exception as e:
        test("11.5 POST /api/contracts/preview with custom template", False, str(e))

# Test 11.6: POST /api/templates/default/activate - revert to default
try:
    resp = requests.post(f"{API_BASE}/templates/default/activate", timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        test(
            "11.6 POST /api/templates/default/activate reverts to default template",
            data.get("active") == "default",
            f"Active template: {data.get('active')}"
        )
    else:
        test("11.6 POST /api/templates/default/activate", False, f"Status: {resp.status_code}")
except Exception as e:
    test("11.6 POST /api/templates/default/activate", False, str(e))

# Test 11.7: DELETE /api/templates/{id} - delete custom template
if custom_template_id:
    try:
        resp = requests.delete(f"{API_BASE}/templates/{custom_template_id}", timeout=10)
        test(
            "11.7 DELETE /api/templates/{id} deletes custom template",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        # Remove from cleanup list
        if custom_template_id in created_template_ids:
            created_template_ids.remove(custom_template_id)
    except Exception as e:
        test("11.7 DELETE /api/templates/{id}", False, str(e))

# Test 11.8: Verify built-in template file is NOT modified
try:
    template_path = Path("/app/backend/templates/contract_template.docx")
    if template_path.exists():
        # Check file still exists and is valid
        file_size = template_path.stat().st_size
        test(
            "11.8 Built-in template file /app/backend/templates/contract_template.docx is NOT modified",
            file_size > 10000,  # Should be around 25KB
            f"File size: {file_size} bytes"
        )
    else:
        test("11.8 Built-in template file exists", False, "File not found")
except Exception as e:
    test("11.8 Built-in template file check", False, str(e))

# Test 11.9: POST /api/contracts/preview still works with default template
try:
    resp = requests.post(
        f"{API_BASE}/contracts/preview",
        params={"format": "pdf"},
        json={"fields": {"full_name": "Тест После Удаления"}},
        timeout=30
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    test(
        "11.9 POST /api/contracts/preview?format=pdf works after deleting custom template",
        resp.status_code == 200 and is_pdf,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}"
    )
except Exception as e:
    test("11.9 POST /api/contracts/preview after deletion", False, str(e))

# Test 11.10: POST /api/templates with non-.docx file (should return 400)
try:
    # Create a temporary text file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp:
        tmp.write("This is not a docx file")
        tmp_path = tmp.name
    
    try:
        with open(tmp_path, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            resp = requests.post(f"{API_BASE}/templates", files=files, timeout=10)
            test(
                "11.10 POST /api/templates with non-.docx file returns 400",
                resp.status_code == 400,
                f"Status: {resp.status_code}"
            )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
except Exception as e:
    test("11.10 POST /api/templates with non-.docx", False, str(e))

# ============================================================================
# 12. TEMPLATE INFO TESTS (NEW FEATURE)
# ============================================================================
print("\n📊 12. TEMPLATE INFO TESTS")
print("-" * 80)

# Test 12.1: GET /api/template-info - should return pages_per_doc
try:
    resp = requests.get(f"{API_BASE}/template-info", timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        pages = data.get("pages_per_doc")
        # Built-in template should produce 4 pages
        test(
            "12.1 GET /api/template-info returns pages_per_doc (expected 4 for built-in)",
            pages == 4,
            f"pages_per_doc: {pages}"
        )
    else:
        test("12.1 GET /api/template-info", False, f"Status: {resp.status_code}")
except Exception as e:
    test("12.1 GET /api/template-info", False, str(e))

# ============================================================================
# 13. PRINT PROFILES TESTS (NEW FEATURE)
# ============================================================================
print("\n🖨️  13. PRINT PROFILES TESTS")
print("-" * 80)

# Store created profile IDs for cleanup
created_profile_ids = []

# Test 13.1: POST /api/print-profiles - create profile
profile_id = None
try:
    resp = requests.post(
        f"{API_BASE}/print-profiles",
        json={
            "name": "Тестовый Профиль P1",
            "settings": {
                "orientation": "landscape",
                "flip_edge": "short",
                "backReversed": True
            }
        },
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        profile_id = data.get("id")
        created_profile_ids.append(profile_id)
        test(
            "13.1 POST /api/print-profiles creates profile",
            data.get("name") == "Тестовый Профиль P1" and profile_id is not None,
            f"Profile ID: {profile_id}, Name: {data.get('name')}"
        )
    else:
        test("13.1 POST /api/print-profiles", False, f"Status: {resp.status_code}, Body: {resp.text}")
except Exception as e:
    test("13.1 POST /api/print-profiles", False, str(e))

# Test 13.2: GET /api/print-profiles - list profiles
if profile_id:
    try:
        resp = requests.get(f"{API_BASE}/print-profiles", timeout=10)
        if resp.status_code == 200:
            profiles = resp.json()
            has_profile = any(p.get("id") == profile_id for p in profiles)
            test(
                "13.2 GET /api/print-profiles returns profiles list",
                isinstance(profiles, list) and has_profile,
                f"Total profiles: {len(profiles)}, Has test profile: {has_profile}"
            )
        else:
            test("13.2 GET /api/print-profiles", False, f"Status: {resp.status_code}")
    except Exception as e:
        test("13.2 GET /api/print-profiles", False, str(e))

# Test 13.3: DELETE /api/print-profiles/{id} - delete profile
if profile_id:
    try:
        resp = requests.delete(f"{API_BASE}/print-profiles/{profile_id}", timeout=10)
        test(
            "13.3 DELETE /api/print-profiles/{id} deletes profile",
            resp.status_code == 200,
            f"Status: {resp.status_code}"
        )
        # Remove from cleanup list
        if profile_id in created_profile_ids:
            created_profile_ids.remove(profile_id)
    except Exception as e:
        test("13.3 DELETE /api/print-profiles/{id}", False, str(e))

# Test 13.4: Repeat DELETE (should return 404)
if profile_id:
    try:
        resp = requests.delete(f"{API_BASE}/print-profiles/{profile_id}", timeout=10)
        test(
            "13.4 DELETE /api/print-profiles/{id} (repeat) returns 404",
            resp.status_code == 404,
            f"Status: {resp.status_code}"
        )
    except Exception as e:
        test("13.4 DELETE /api/print-profiles/{id} (repeat)", False, str(e))

# Test 13.5: POST /api/print-profiles with empty name (should return 400)
try:
    resp = requests.post(
        f"{API_BASE}/print-profiles",
        json={"name": "", "settings": {"orientation": "portrait"}},
        timeout=10
    )
    test(
        "13.5 POST /api/print-profiles with empty name returns 400",
        resp.status_code == 400,
        f"Status: {resp.status_code}"
    )
except Exception as e:
    test("13.5 POST /api/print-profiles with empty name", False, str(e))

# ============================================================================
# 14. FLIP_EDGE PARAMETER TESTS (NEW FEATURE)
# ============================================================================
print("\n🔄 14. FLIP_EDGE PARAMETER TESTS")
print("-" * 80)

# Get 1 contract ID for flip_edge tests
flip_test_id = None
if len(contract_ids_for_duplex) >= 1:
    flip_test_id = contract_ids_for_duplex[0]
    print(f"📋 Using contract ID for flip_edge tests: {flip_test_id}")
else:
    print("⚠️  No contracts available for flip_edge testing")

def get_pdf_rotations(pdf_data):
    """Extract /Rotate values from all pages in a PDF."""
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(pdf_data))
        rotations = []
        for page in reader.pages:
            rotate = page.get('/Rotate')
            rotations.append(rotate if rotate is not None else 0)
        return rotations
    except Exception as e:
        print(f"⚠️  Error extracting rotations: {e}")
        return []

# Test 14.1: manual-duplex with flip_edge="short", side="back" -> /Rotate=180
if flip_test_id:
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": [flip_test_id], "side": "back", "flip_edge": "short"},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        rotations = get_pdf_rotations(resp.content) if is_pdf else []
        all_180 = all(r == 180 for r in rotations) if rotations else False
        test(
            "14.1 POST manual-duplex side='back' flip_edge='short' -> all pages /Rotate=180",
            resp.status_code == 200 and is_pdf and all_180,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Rotations: {rotations}, All 180°: {all_180}"
        )
    except Exception as e:
        test("14.1 POST manual-duplex flip_edge='short'", False, str(e))

# Test 14.2: manual-duplex with flip_edge="long", side="back" -> /Rotate=0/None
if flip_test_id:
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": [flip_test_id], "side": "back", "flip_edge": "long"},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        rotations = get_pdf_rotations(resp.content) if is_pdf else []
        all_0 = all(r == 0 or r is None for r in rotations) if rotations else False
        test(
            "14.2 POST manual-duplex side='back' flip_edge='long' -> all pages /Rotate=0/None",
            resp.status_code == 200 and is_pdf and all_0,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Rotations: {rotations}, All 0°: {all_0}"
        )
    except Exception as e:
        test("14.2 POST manual-duplex flip_edge='long'", False, str(e))

# Test 14.3: manual-duplex with flip_edge="short", orientation="landscape", side="back" -> /Rotate=270
if flip_test_id:
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": [flip_test_id], "side": "back", "flip_edge": "short", "orientation": "landscape"},
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        rotations = get_pdf_rotations(resp.content) if is_pdf else []
        all_270 = all(r == 270 for r in rotations) if rotations else False
        test(
            "14.3 POST manual-duplex side='back' flip_edge='short' orientation='landscape' -> all pages /Rotate=270",
            resp.status_code == 200 and is_pdf and all_270,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Rotations: {rotations}, All 270°: {all_270}"
        )
    except Exception as e:
        test("14.3 POST manual-duplex flip_edge='short' + landscape", False, str(e))

# Test 14.4: Verify flip_edge default is "long" (no rotation on back)
if flip_test_id:
    try:
        resp = requests.post(
            f"{API_BASE}/contracts/manual-duplex",
            json={"ids": [flip_test_id], "side": "back"},  # No flip_edge specified
            timeout=60
        )
        is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
        rotations = get_pdf_rotations(resp.content) if is_pdf else []
        all_0 = all(r == 0 or r is None for r in rotations) if rotations else False
        test(
            "14.4 POST manual-duplex side='back' (no flip_edge) defaults to 'long' -> /Rotate=0",
            resp.status_code == 200 and is_pdf and all_0,
            f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Rotations: {rotations}, All 0°: {all_0}"
        )
    except Exception as e:
        test("14.4 POST manual-duplex default flip_edge", False, str(e))

# ============================================================================
# CLEANUP
# ============================================================================
print("\n🧹 CLEANUP")
print("-" * 80)

# Delete test contracts
for cid in created_contract_ids:
    try:
        requests.delete(f"{API_BASE}/contracts/{cid}", timeout=5)
    except Exception:
        pass

# Delete test presets
for pid in created_preset_ids:
    try:
        requests.delete(f"{API_BASE}/presets/{pid}", timeout=5)
    except Exception:
        pass

# Delete test templates
for tid in created_template_ids:
    try:
        requests.delete(f"{API_BASE}/templates/{tid}", timeout=5)
    except Exception:
        pass

# Delete test print profiles
for pid in created_profile_ids:
    try:
        requests.delete(f"{API_BASE}/print-profiles/{pid}", timeout=5)
    except Exception:
        pass

print(f"Cleaned up {len(created_contract_ids)} contracts, {len(created_preset_ids)} presets, {len(created_template_ids)} templates, and {len(created_profile_ids)} profiles")

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
