#!/usr/bin/env python3
"""
Backend API tests for orientation parameter in duplex printing (Banetskaya.by).
Tests the /Rotate field in PDF pages using pypdf.
"""
import requests
import sys
import io
from pathlib import Path
from pypdf import PdfReader

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

def check_pdf_valid(data):
    """Check if data is a valid PDF."""
    return data.startswith(b'%PDF')

def get_pdf_page_rotations(pdf_data):
    """Get /Rotate values for all pages in a PDF."""
    try:
        reader = PdfReader(io.BytesIO(pdf_data))
        rotations = []
        for page in reader.pages:
            rotate = page.get('/Rotate')
            rotations.append(rotate)
        return rotations
    except Exception as e:
        print(f"⚠️  Error reading PDF rotations: {e}")
        return None

def count_pdf_pages(pdf_data):
    """Count the number of pages in a PDF."""
    try:
        reader = PdfReader(io.BytesIO(pdf_data))
        return len(reader.pages)
    except Exception as e:
        print(f"⚠️  Error counting PDF pages: {e}")
        return -1

print("=" * 80)
print("ORIENTATION TESTS - Banetskaya.by Duplex Printing")
print("=" * 80)

# ============================================================================
# PREPARATION: Get 2 real contract IDs
# ============================================================================
print("\n📦 PREPARATION: Getting contract IDs")
print("-" * 80)

# Seed demo data if needed
try:
    resp = requests.get(f"{API_BASE}/contracts", timeout=10)
    if resp.status_code == 200:
        contracts = resp.json()
        if len(contracts) < 2:
            print("⚠️  Not enough contracts, seeding demo data...")
            requests.post(f"{API_BASE}/seed-demo", timeout=10)
            resp = requests.get(f"{API_BASE}/contracts", timeout=10)
            contracts = resp.json() if resp.status_code == 200 else []
except Exception as e:
    print(f"⚠️  Error getting contracts: {e}")
    contracts = []

# Get 2 contract IDs
contract_ids = []
if contracts:
    final_contracts = [c for c in contracts if c.get("status") != "draft"]
    contract_ids = [c["id"] for c in final_contracts[:2]]
    print(f"✓ Retrieved {len(contract_ids)} contract IDs: {contract_ids}")
else:
    print("❌ Failed to get contract IDs")
    sys.exit(1)

if len(contract_ids) < 2:
    print("❌ Not enough contracts for testing")
    sys.exit(1)

# ============================================================================
# 1. MANUAL DUPLEX ORIENTATION TESTS
# ============================================================================
print("\n🔄 1. MANUAL DUPLEX ORIENTATION TESTS")
print("-" * 80)

# Test 1.1: POST manual-duplex with orientation="landscape", side="front"
# Expected: All pages should have /Rotate == 90
print("\n1.1 Testing manual-duplex with orientation='landscape', side='front'...")
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids, "side": "front", "orientation": "landscape"},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    # Check that all pages have /Rotate == 90
    all_rotated = all(r == 90 for r in rotations) if rotations else False
    
    test(
        "1.1 POST manual-duplex orientation='landscape' side='front' - all pages /Rotate == 90",
        resp.status_code == 200 and is_pdf and pages == 4 and all_rotated,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotations: {rotations}, All 90°: {all_rotated}"
    )
except Exception as e:
    test("1.1 POST manual-duplex orientation='landscape' side='front'", False, str(e))

# Test 1.2: POST manual-duplex with orientation="portrait", side="front"
# Expected: All pages should have /Rotate == None or 0
print("\n1.2 Testing manual-duplex with orientation='portrait', side='front'...")
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids, "side": "front", "orientation": "portrait"},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    # Check that all pages have /Rotate == None or 0
    all_portrait = all(r is None or r == 0 for r in rotations) if rotations else False
    
    test(
        "1.2 POST manual-duplex orientation='portrait' side='front' - all pages /Rotate == None/0",
        resp.status_code == 200 and is_pdf and pages == 4 and all_portrait,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotations: {rotations}, All None/0: {all_portrait}"
    )
except Exception as e:
    test("1.2 POST manual-duplex orientation='portrait' side='front'", False, str(e))

# Test 1.3: POST manual-duplex with orientation="landscape", side="back"
# Expected: All pages should have /Rotate == 90
print("\n1.3 Testing manual-duplex with orientation='landscape', side='back'...")
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids, "side": "back", "orientation": "landscape"},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    all_rotated = all(r == 90 for r in rotations) if rotations else False
    
    test(
        "1.3 POST manual-duplex orientation='landscape' side='back' - all pages /Rotate == 90",
        resp.status_code == 200 and is_pdf and pages == 4 and all_rotated,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotations: {rotations}, All 90°: {all_rotated}"
    )
except Exception as e:
    test("1.3 POST manual-duplex orientation='landscape' side='back'", False, str(e))

# Test 1.4: POST manual-duplex with orientation="portrait", side="back"
# Expected: All pages should have /Rotate == None or 0
print("\n1.4 Testing manual-duplex with orientation='portrait', side='back'...")
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids, "side": "back", "orientation": "portrait"},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    all_portrait = all(r is None or r == 0 for r in rotations) if rotations else False
    
    test(
        "1.4 POST manual-duplex orientation='portrait' side='back' - all pages /Rotate == None/0",
        resp.status_code == 200 and is_pdf and pages == 4 and all_portrait,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotations: {rotations}, All None/0: {all_portrait}"
    )
except Exception as e:
    test("1.4 POST manual-duplex orientation='portrait' side='back'", False, str(e))

# ============================================================================
# 2. PRINT-TEST ORIENTATION TESTS
# ============================================================================
print("\n📄 2. PRINT-TEST ORIENTATION TESTS")
print("-" * 80)

# Test 2.1: GET /api/print-test?side=front&orientation=landscape
# Expected: 1 page with /Rotate == 90
print("\n2.1 Testing print-test with side='front', orientation='landscape'...")
try:
    resp = requests.get(
        f"{API_BASE}/print-test",
        params={"side": "front", "orientation": "landscape"},
        timeout=10
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    has_rotation = rotations and len(rotations) == 1 and rotations[0] == 90
    
    test(
        "2.1 GET print-test side='front' orientation='landscape' - /Rotate == 90",
        resp.status_code == 200 and is_pdf and pages == 1 and has_rotation,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotation: {rotations[0] if rotations else None}"
    )
except Exception as e:
    test("2.1 GET print-test side='front' orientation='landscape'", False, str(e))

# Test 2.2: GET /api/print-test?side=back&orientation=portrait
# Expected: 1 page with /Rotate == None or 0
print("\n2.2 Testing print-test with side='back', orientation='portrait'...")
try:
    resp = requests.get(
        f"{API_BASE}/print-test",
        params={"side": "back", "orientation": "portrait"},
        timeout=10
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    has_no_rotation = rotations and len(rotations) == 1 and (rotations[0] is None or rotations[0] == 0)
    
    test(
        "2.2 GET print-test side='back' orientation='portrait' - /Rotate == None/0",
        resp.status_code == 200 and is_pdf and pages == 1 and has_no_rotation,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotation: {rotations[0] if rotations else None}"
    )
except Exception as e:
    test("2.2 GET print-test side='back' orientation='portrait'", False, str(e))

# Test 2.3: GET /api/print-test?side=front&orientation=portrait
# Expected: 1 page with /Rotate == None or 0
print("\n2.3 Testing print-test with side='front', orientation='portrait'...")
try:
    resp = requests.get(
        f"{API_BASE}/print-test",
        params={"side": "front", "orientation": "portrait"},
        timeout=10
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    has_no_rotation = rotations and len(rotations) == 1 and (rotations[0] is None or rotations[0] == 0)
    
    test(
        "2.3 GET print-test side='front' orientation='portrait' - /Rotate == None/0",
        resp.status_code == 200 and is_pdf and pages == 1 and has_no_rotation,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotation: {rotations[0] if rotations else None}"
    )
except Exception as e:
    test("2.3 GET print-test side='front' orientation='portrait'", False, str(e))

# Test 2.4: GET /api/print-test?side=back&orientation=landscape
# Expected: 1 page with /Rotate == 90
print("\n2.4 Testing print-test with side='back', orientation='landscape'...")
try:
    resp = requests.get(
        f"{API_BASE}/print-test",
        params={"side": "back", "orientation": "landscape"},
        timeout=10
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    has_rotation = rotations and len(rotations) == 1 and rotations[0] == 90
    
    test(
        "2.4 GET print-test side='back' orientation='landscape' - /Rotate == 90",
        resp.status_code == 200 and is_pdf and pages == 1 and has_rotation,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotation: {rotations[0] if rotations else None}"
    )
except Exception as e:
    test("2.4 GET print-test side='back' orientation='landscape'", False, str(e))

# ============================================================================
# 3. SEPARATORS + ORIENTATION TESTS
# ============================================================================
print("\n📑 3. SEPARATORS + ORIENTATION TESTS")
print("-" * 80)

# Test 3.1: POST manual-duplex with separators=true, orientation="landscape", side="front"
# Expected: 6 pages (2 contracts × 2 front + 2 separators), all with /Rotate == 90
print("\n3.1 Testing manual-duplex with separators=true, orientation='landscape', side='front'...")
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids, "side": "front", "orientation": "landscape", "separators": True},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    all_rotated = all(r == 90 for r in rotations) if rotations else False
    
    test(
        "3.1 POST manual-duplex separators=true orientation='landscape' - 6 pages, all /Rotate == 90",
        resp.status_code == 200 and is_pdf and pages == 6 and all_rotated,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotations: {rotations}, All 90°: {all_rotated}"
    )
except Exception as e:
    test("3.1 POST manual-duplex separators=true orientation='landscape'", False, str(e))

# Test 3.2: POST manual-duplex with separators=true, orientation="portrait", side="front"
# Expected: 6 pages, all with /Rotate == None or 0
print("\n3.2 Testing manual-duplex with separators=true, orientation='portrait', side='front'...")
try:
    resp = requests.post(
        f"{API_BASE}/contracts/manual-duplex",
        json={"ids": contract_ids, "side": "front", "orientation": "portrait", "separators": True},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    pages = count_pdf_pages(resp.content) if is_pdf else 0
    rotations = get_pdf_page_rotations(resp.content) if is_pdf else None
    
    all_portrait = all(r is None or r == 0 for r in rotations) if rotations else False
    
    test(
        "3.2 POST manual-duplex separators=true orientation='portrait' - 6 pages, all /Rotate == None/0",
        resp.status_code == 200 and is_pdf and pages == 6 and all_portrait,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}, Pages: {pages}, Rotations: {rotations}, All None/0: {all_portrait}"
    )
except Exception as e:
    test("3.2 POST manual-duplex separators=true orientation='portrait'", False, str(e))

# ============================================================================
# 4. REGRESSION TESTS
# ============================================================================
print("\n🔄 4. REGRESSION TESTS")
print("-" * 80)

# Test 4.1: POST /api/contracts/preview?format=pdf (LibreOffice working)
print("\n4.1 Testing preview PDF (LibreOffice)...")
try:
    resp = requests.post(
        f"{API_BASE}/contracts/preview",
        params={"format": "pdf"},
        json={"fields": {"full_name": "Тест"}},
        timeout=30
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    test(
        "4.1 REGRESSION: POST /api/contracts/preview?format=pdf works",
        resp.status_code == 200 and is_pdf,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}"
    )
except Exception as e:
    test("4.1 REGRESSION: POST /api/contracts/preview?format=pdf", False, str(e))

# Test 4.2: POST /api/contracts/batch-print
print("\n4.2 Testing batch-print...")
try:
    resp = requests.post(
        f"{API_BASE}/contracts/batch-print",
        json={"ids": contract_ids},
        timeout=60
    )
    is_pdf = check_pdf_valid(resp.content) if resp.status_code == 200 else False
    test(
        "4.2 REGRESSION: POST /api/contracts/batch-print works",
        resp.status_code == 200 and is_pdf,
        f"Status: {resp.status_code}, Valid PDF: {is_pdf}"
    )
except Exception as e:
    test("4.2 REGRESSION: POST /api/contracts/batch-print", False, str(e))

# Test 4.3: GET /api/contracts/export
print("\n4.3 Testing contracts export...")
try:
    resp = requests.get(f"{API_BASE}/contracts/export", timeout=30)
    is_xlsx = resp.content.startswith(b'PK\x03\x04') if resp.status_code == 200 else False
    test(
        "4.3 REGRESSION: GET /api/contracts/export returns XLSX",
        resp.status_code == 200 and is_xlsx,
        f"Status: {resp.status_code}, Valid XLSX: {is_xlsx}"
    )
except Exception as e:
    test("4.3 REGRESSION: GET /api/contracts/export", False, str(e))

# Test 4.4: GET /api/stats
print("\n4.4 Testing stats...")
try:
    resp = requests.get(f"{API_BASE}/stats", timeout=10)
    test(
        "4.4 REGRESSION: GET /api/stats works",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
except Exception as e:
    test("4.4 REGRESSION: GET /api/stats", False, str(e))

# Test 4.5: GET /api/presets
print("\n4.5 Testing presets...")
try:
    resp = requests.get(f"{API_BASE}/presets", timeout=10)
    test(
        "4.5 REGRESSION: GET /api/presets works",
        resp.status_code == 200,
        f"Status: {resp.status_code}"
    )
except Exception as e:
    test("4.5 REGRESSION: GET /api/presets", False, str(e))

# Test 4.6: POST /api/seed-demo (idempotency)
print("\n4.6 Testing seed-demo idempotency...")
try:
    resp = requests.post(f"{API_BASE}/seed-demo", timeout=10)
    data = resp.json() if resp.status_code == 200 else {}
    # Should be idempotent (created=0 if already exists)
    test(
        "4.6 REGRESSION: POST /api/seed-demo is idempotent",
        resp.status_code == 200 and (data.get("created") == 0 or data.get("created") == 6),
        f"Status: {resp.status_code}, Created: {data.get('created')}, Already: {data.get('already')}"
    )
except Exception as e:
    test("4.6 REGRESSION: POST /api/seed-demo", False, str(e))

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
