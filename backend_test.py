#!/usr/bin/env python3
"""
Backend API testing for Banetskaya.by - Alignment fix for duplex printing.
Tests forma24/preview, full package cycle, and border alignment verification.
"""
import os
import sys
import requests
import json
import io
import numpy as np

# Get backend URL from environment
with open('/app/frontend/.env', 'r') as f:
    for line in f:
        if line.startswith('REACT_APP_BACKEND_URL='):
            BACKEND_URL = line.strip().split('=', 1)[1]
            break

API_BASE = f"{BACKEND_URL}/api"

print(f"Backend URL: {BACKEND_URL}")
print(f"API Base: {API_BASE}")

# Global variables to store test data
xlsx_bytes = None
students = None
masters = None
contract_id = None
package_pdf = None


def test_1_forma24_preview():
    """Test 1: POST /api/forma24/preview with duplex_flip="long" → 200, PDF, exactly 2 pages"""
    print("\n" + "="*70)
    print("[TEST 1] POST /api/forma24/preview")
    print("="*70)
    
    url = f"{API_BASE}/forma24/preview"
    
    try:
        payload = {
            "records": [
                {
                    "surname": "Иванов",
                    "first_name": "Иван"
                }
            ],
            "duplex_flip": "long"
        }
        
        resp = requests.post(url, json=payload, timeout=30)
        
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type')}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.headers.get('Content-Type') == 'application/pdf', \
            f"Expected application/pdf, got {resp.headers.get('Content-Type')}"
        
        pdf_bytes = resp.content
        print(f"  PDF size: {len(pdf_bytes)} bytes")
        
        # Verify it's a valid PDF
        assert pdf_bytes.startswith(b'%PDF'), "Response is not a valid PDF"
        
        # Open PDF with pymupdf and check page count
        import pymupdf
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        num_pages = len(doc)
        print(f"  Pages: {num_pages}")
        
        assert num_pages == 2, f"Expected exactly 2 pages, got {num_pages}"
        
        # Check page size (should be A4: 595.28 x 841.89 pt)
        page0 = doc[0]
        width = page0.rect.width
        height = page0.rect.height
        print(f"  Page 0 size: {width:.2f} x {height:.2f} pt")
        
        # A4 size with tolerance
        assert abs(width - 595.28) < 2, f"Expected width ~595.28 pt, got {width:.2f}"
        assert abs(height - 841.89) < 2, f"Expected height ~841.89 pt, got {height:.2f}"
        
        doc.close()
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_2_get_master_template():
    """Test 2: GET /api/master-template → 200, download .xlsx"""
    global xlsx_bytes
    print("\n" + "="*70)
    print("[TEST 2] GET /api/master-template")
    print("="*70)
    
    url = f"{API_BASE}/master-template"
    
    try:
        resp = requests.get(url, timeout=30)
        print(f"  Status: {resp.status_code}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        xlsx_bytes = resp.content
        print(f"  Downloaded: {len(xlsx_bytes)} bytes")
        
        print("  ✅ PASS")
        return xlsx_bytes
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_3_post_generate_upload():
    """Test 3: POST /api/generate/upload → 200, mode="master", students and masters"""
    global students, masters
    print("\n" + "="*70)
    print("[TEST 3] POST /api/generate/upload")
    print("="*70)
    
    url = f"{API_BASE}/generate/upload"
    
    try:
        files = {'file': ('master_template.xlsx', xlsx_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        resp = requests.post(url, files=files, timeout=30)
        
        print(f"  Status: {resp.status_code}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        
        assert data.get('mode') == 'master', f"Expected mode='master', got {data.get('mode')}"
        print(f"  mode: {data.get('mode')} ✓")
        
        students = data.get('students', [])
        assert len(students) >= 1, f"Expected students array with >= 1 items, got {len(students)}"
        print(f"  students: {len(students)} items ✓")
        
        masters = data.get('masters', [])
        assert len(masters) >= 1, f"Expected masters array with >= 1 items, got {len(masters)}"
        print(f"  masters: {len(masters)} items ✓")
        
        print("  ✅ PASS")
        return students, masters
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_4_post_contracts_batch():
    """Test 4: POST /api/contracts/batch → 200, remember created[0].id"""
    global contract_id
    print("\n" + "="*70)
    print("[TEST 4] POST /api/contracts/batch")
    print("="*70)
    
    url = f"{API_BASE}/contracts/batch"
    
    try:
        payload = {
            "contracts": students,
            "masters": masters
        }
        
        resp = requests.post(url, json=payload, timeout=30)
        
        print(f"  Status: {resp.status_code}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        data = resp.json()
        created = data.get('created', [])
        assert len(created) >= 1, f"Expected created array with >= 1 items, got {len(created)}"
        
        contract_id = created[0].get('id')
        print(f"  created[0].id: {contract_id} ✓")
        
        print("  ✅ PASS")
        return contract_id
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_5_post_contract_package():
    """Test 5: POST /api/contracts/{id}/package → 200, PDF, exactly 7 pages, check content"""
    global package_pdf
    print("\n" + "="*70)
    print(f"[TEST 5] POST /api/contracts/{contract_id}/package")
    print("="*70)
    
    url = f"{API_BASE}/contracts/{contract_id}/package"
    
    try:
        payload = {"duplex_flip": "long"}
        
        resp = requests.post(url, json=payload, timeout=60)
        
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('Content-Type')}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        assert resp.headers.get('Content-Type') == 'application/pdf', \
            f"Expected application/pdf, got {resp.headers.get('Content-Type')}"
        
        package_pdf = resp.content
        print(f"  PDF size: {len(package_pdf)} bytes")
        
        # Open PDF with pymupdf
        import pymupdf
        doc = pymupdf.open(stream=package_pdf, filetype="pdf")
        num_pages = len(doc)
        print(f"  Pages: {num_pages}")
        
        assert num_pages == 7, f"Expected exactly 7 pages, got {num_pages}"
        
        # Check page 0 contains "ДОГОВОР"
        page0_text = doc[0].get_text()
        assert "ДОГОВОР" in page0_text, "Page 0 should contain 'ДОГОВОР'"
        print(f"  Page 0: contains 'ДОГОВОР' ✓")
        
        # Check page 4 contains BOTH "Форма № 19" AND "Форма 24"
        page4_text = doc[4].get_text()
        has_forma19 = "Форма № 19" in page4_text or "Форма №19" in page4_text or "АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ" in page4_text
        has_forma24 = "Форма 24" in page4_text or "ТАЛОН МИГРАЦИОННОГО" in page4_text
        
        assert has_forma19, "Page 4 should contain 'Форма № 19' or 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ'"
        assert has_forma24, "Page 4 should contain 'Форма 24' or 'ТАЛОН МИГРАЦИОННОГО'"
        print(f"  Page 4: contains BOTH 'Форма № 19' AND 'Форма 24' ✓")
        
        # Check page 6 contains "СООБЩЕНИЕ"
        page6_text = doc[6].get_text()
        assert "СООБЩЕНИЕ" in page6_text, "Page 6 should contain 'СООБЩЕНИЕ'"
        print(f"  Page 6: contains 'СООБЩЕНИЕ' ✓")
        
        doc.close()
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_6_border_alignment():
    """Test 6: MAIN CHECK - Border alignment and safe margins"""
    print("\n" + "="*70)
    print("[TEST 6] MAIN CHECK - Border alignment and safe margins")
    print("="*70)
    
    try:
        import pymupdf
        
        # Open the 7-page package PDF
        doc = pymupdf.open(stream=package_pdf, filetype="pdf")
        
        # Get pages 4 (front) and 5 (back) - the combined Forma19+Forma24 sheet
        page_front = doc[4]
        page_back = doc[5]
        
        print(f"  Rendering page 4 (front) and page 5 (back)...")
        
        # Render both pages at 1.6x scale in grayscale
        mat = pymupdf.Matrix(1.6, 1.6)
        
        # Render front page
        pix_front = page_front.get_pixmap(matrix=mat, colorspace=pymupdf.csGRAY)
        front_array = np.frombuffer(pix_front.samples, dtype=np.uint8).reshape(pix_front.height, pix_front.width)
        
        # Render back page
        pix_back = page_back.get_pixmap(matrix=mat, colorspace=pymupdf.csGRAY)
        back_array = np.frombuffer(pix_back.samples, dtype=np.uint8).reshape(pix_back.height, pix_back.width)
        
        print(f"  Front page size: {front_array.shape}")
        print(f"  Back page size: {back_array.shape}")
        
        # Ensure both pages have the same size
        assert front_array.shape == back_array.shape, \
            f"Front and back pages have different sizes: {front_array.shape} vs {back_array.shape}"
        
        # Flip back page horizontally (simulate duplex flip on long edge)
        back_flipped = np.fliplr(back_array)
        
        print(f"  Back page flipped horizontally")
        
        # Find vertical border lines
        def find_vertical_borders(img_array, threshold=0.55):
            """Find vertical border lines by detecting columns with >55% dark pixels"""
            height, width = img_array.shape
            dark_threshold = 110  # pixels darker than this are considered "dark"
            
            # For each column, count dark pixels
            vertical_lines = []
            for x in range(width):
                column = img_array[:, x]
                dark_ratio = np.sum(column < dark_threshold) / height
                
                if dark_ratio > threshold:
                    vertical_lines.append(x)
            
            # Group adjacent columns (within 3px) and take center
            if not vertical_lines:
                return []
            
            groups = []
            current_group = [vertical_lines[0]]
            
            for x in vertical_lines[1:]:
                if x - current_group[-1] <= 3:
                    current_group.append(x)
                else:
                    groups.append(current_group)
                    current_group = [x]
            groups.append(current_group)
            
            # Take center of each group
            centers = [int(np.mean(group)) for group in groups]
            return centers
        
        # Find borders on front and back
        front_borders_px = find_vertical_borders(front_array)
        back_borders_px = find_vertical_borders(back_flipped)
        
        print(f"  Front borders (px): {front_borders_px}")
        print(f"  Back borders (px): {back_borders_px}")
        
        # Convert pixels to mm
        # A4 width = 210 mm, page width in pixels
        width_px = front_array.shape[1]
        ppmm = width_px / 210.0  # pixels per mm
        
        front_borders_mm = [x / ppmm for x in front_borders_px]
        back_borders_mm = [x / ppmm for x in back_borders_px]
        
        print(f"\n  Front borders (mm): {[f'{x:.2f}' for x in front_borders_mm]}")
        print(f"  Back borders (mm): {[f'{x:.2f}' for x in back_borders_mm]}")
        
        # Check (a): Leftmost border is NOT at the edge (should be 3..9 mm from left)
        if front_borders_mm:
            leftmost = min(front_borders_mm)
            print(f"\n  (a) Leftmost border: {leftmost:.2f} mm")
            
            if 3.0 <= leftmost <= 9.0:
                print(f"      ✓ PASS: Leftmost border is in safe margin range (3..9 mm)")
                check_a = True
            else:
                print(f"      ✗ FAIL: Leftmost border is outside safe margin range (expected 3..9 mm, got {leftmost:.2f} mm)")
                check_a = False
        else:
            print(f"  (a) ✗ FAIL: No borders found on front page")
            check_a = False
        
        # Check (b): Front and back borders match (within 1.0 mm)
        print(f"\n  (b) Border alignment check:")
        
        if not front_borders_mm or not back_borders_mm:
            print(f"      ✗ FAIL: No borders found on one or both pages")
            check_b = False
        else:
            # For each front border, find closest back border
            max_diff = 0.0
            all_matched = True
            
            for front_x in front_borders_mm:
                # Find closest back border
                diffs = [abs(front_x - back_x) for back_x in back_borders_mm]
                min_diff = min(diffs)
                closest_back_x = back_borders_mm[diffs.index(min_diff)]
                
                print(f"      Front {front_x:.2f} mm → Back {closest_back_x:.2f} mm (diff: {min_diff:.2f} mm)")
                
                if min_diff > 1.0:
                    all_matched = False
                
                max_diff = max(max_diff, min_diff)
            
            if all_matched:
                print(f"      ✓ PASS: All borders match within 1.0 mm (max diff: {max_diff:.2f} mm)")
                check_b = True
            else:
                print(f"      ✗ FAIL: Some borders do not match within 1.0 mm (max diff: {max_diff:.2f} mm)")
                check_b = False
        
        doc.close()
        
        # Final verdict
        print(f"\n  FINAL VERDICT:")
        print(f"    (a) Safe margins: {'PASS' if check_a else 'FAIL'}")
        print(f"    (b) Border alignment: {'PASS' if check_b else 'FAIL'}")
        
        if check_a and check_b:
            print(f"\n  ✅ PASS - Border alignment is correct!")
        else:
            print(f"\n  ❌ FAIL - Border alignment issues detected")
            sys.exit(1)
        
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_7_delete_contract():
    """Test 7: DELETE /api/contracts/{id} → 200 (cleanup)"""
    print("\n" + "="*70)
    print(f"[TEST 7] DELETE /api/contracts/{contract_id}")
    print("="*70)
    
    url = f"{API_BASE}/contracts/{contract_id}"
    
    try:
        resp = requests.delete(url, timeout=10)
        
        print(f"  Status: {resp.status_code}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_8_regression_contracts():
    """Test 8: Regression - GET /api/contracts → 200"""
    print("\n" + "="*70)
    print("[REGRESSION] GET /api/contracts")
    print("="*70)
    
    url = f"{API_BASE}/contracts"
    
    try:
        resp = requests.get(url, timeout=10)
        print(f"  Status: {resp.status_code}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), f"Expected array, got {type(data)}"
        print(f"  Contracts count: {len(data)}")
        
        print("  ✅ PASS")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    print("\n" + "="*70)
    print("BACKEND TESTING: BANETSKAYA.BY - DUPLEX BORDER ALIGNMENT FIX")
    print("="*70)
    
    # Run all tests in sequence
    test_1_forma24_preview()
    test_2_get_master_template()
    test_3_post_generate_upload()
    test_4_post_contracts_batch()
    test_5_post_contract_package()
    test_6_border_alignment()
    test_7_delete_contract()
    test_8_regression_contracts()
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED (8/8)")
    print("="*70)
    print("\nSUMMARY:")
    print("  ✓ POST /api/forma24/preview returns 2-page PDF")
    print("  ✓ GET /api/master-template returns valid .xlsx")
    print("  ✓ POST /api/generate/upload parses Excel and returns students/masters")
    print("  ✓ POST /api/contracts/batch creates contracts with master data")
    print("  ✓ POST /api/contracts/{id}/package generates 7-page PDF package")
    print("  ✓ Border alignment check: safe margins and symmetry PASS")
    print("  ✓ DELETE /api/contracts/{id} cleanup successful")
    print("  ✓ Regression: GET /api/contracts works")
    print("\n🎉 DUPLEX BORDER ALIGNMENT FIX VERIFIED!")


if __name__ == "__main__":
    main()
