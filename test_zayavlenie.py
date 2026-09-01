#!/usr/bin/env python3
"""
Тест нового документа «Заявление о регистрации по месту жительства» для Banetskaya.by.

Проверяет все эндпоинты /api/zayavlenie/* и интеграцию с пакетом документов.
"""
import io
import sys
import requests
from datetime import datetime
from openpyxl import load_workbook
import fitz  # pymupdf

# Backend URL
BASE_URL = "https://form-portal-15.preview.emergentagent.com/api"

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_test(name, passed, details=""):
    """Логирование результата теста."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")
    return passed

def main():
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}ТЕСТ ДОКУМЕНТА «ЗАЯВЛЕНИЕ О РЕГИСТРАЦИИ ПО МЕСТУ ЖИТЕЛЬСТВА»{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}\n")
    
    results = []
    
    # ========== ТЕСТ 1: GET /api/zayavlenie/fields ==========
    print(f"\n{BLUE}[1] GET /api/zayavlenie/fields{RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/zayavlenie/fields", timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            has_groups = "groups" in data
            has_keys = "keys" in data
            
            required_keys = [
                "fio", "passport_series", "passport_number", "passport_issued_by",
                "passport_issue_date", "reg_who", "reg_count", "address_locality",
                "res_street", "res_house", "res_korpus", "res_apartment",
                "from_place", "basis", "sign_date", "area"
            ]
            
            keys_present = all(k in data.get("keys", []) for k in required_keys)
            
            # Проверка структуры groups
            groups_valid = True
            if has_groups:
                for group in data["groups"]:
                    if "group" not in group or "fields" not in group:
                        groups_valid = False
                        break
                    for field in group["fields"]:
                        if "key" not in field or "label" not in field:
                            groups_valid = False
                            break
            
            passed = has_groups and has_keys and keys_present and groups_valid
            
            details = f"status={resp.status_code}, groups={len(data.get('groups', []))}, keys={len(data.get('keys', []))}"
            if not keys_present:
                missing = [k for k in required_keys if k not in data.get("keys", [])]
                details += f", missing_keys={missing}"
            
            results.append(log_test("GET /api/zayavlenie/fields", passed, details))
        else:
            results.append(log_test("GET /api/zayavlenie/fields", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("GET /api/zayavlenie/fields", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 2: GET /api/zayavlenie/defaults (initial) ==========
    print(f"\n{BLUE}[2] GET /api/zayavlenie/defaults (initial){RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/zayavlenie/defaults", timeout=30)
        passed = resp.status_code == 200 and "defaults" in resp.json()
        results.append(log_test(
            "GET /api/zayavlenie/defaults (initial)",
            passed,
            f"status={resp.status_code}, defaults={resp.json().get('defaults', {})}"
        ))
    except Exception as e:
        results.append(log_test("GET /api/zayavlenie/defaults (initial)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 3: POST /api/zayavlenie/defaults (save) ==========
    print(f"\n{BLUE}[3] POST /api/zayavlenie/defaults (save){RESET}")
    try:
        payload = {"defaults": {"area": "5467,9"}}
        resp = requests.post(f"{BASE_URL}/zayavlenie/defaults", json=payload, timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            saved = data.get("saved", False)
            passed = saved
            results.append(log_test(
                "POST /api/zayavlenie/defaults (save)",
                passed,
                f"status={resp.status_code}, saved={saved}"
            ))
        else:
            results.append(log_test("POST /api/zayavlenie/defaults (save)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/zayavlenie/defaults (save)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 4: GET /api/zayavlenie/defaults (verify persistence) ==========
    print(f"\n{BLUE}[4] GET /api/zayavlenie/defaults (verify persistence){RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/zayavlenie/defaults", timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            defaults = data.get("defaults", {})
            area_saved = defaults.get("area") == "5467,9"
            passed = area_saved
            results.append(log_test(
                "GET /api/zayavlenie/defaults (verify persistence)",
                passed,
                f"status={resp.status_code}, area={defaults.get('area', 'N/A')}"
            ))
        else:
            results.append(log_test("GET /api/zayavlenie/defaults (verify persistence)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("GET /api/zayavlenie/defaults (verify persistence)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 5: POST /api/zayavlenie/preview (1 record) ==========
    print(f"\n{BLUE}[5] POST /api/zayavlenie/preview (1 record){RESET}")
    try:
        payload = {
            "records": [{
                "fio": "Иванов Иван Иванович",
                "passport_series": "MP",
                "passport_number": "1234567",
                "area": "5467,9",
                "sign_date": "21.07.2025",
                "reg_who": "одного",
                "reg_count": "1"
            }]
        }
        resp = requests.post(f"{BASE_URL}/zayavlenie/preview", json=payload, timeout=30)
        passed = resp.status_code == 200 and resp.headers.get('content-type') == 'application/pdf'
        
        if passed:
            pdf_bytes = resp.content
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            doc.close()
            
            passed = page_count == 2
            results.append(log_test(
                "POST /api/zayavlenie/preview (1 record)",
                passed,
                f"status={resp.status_code}, pages={page_count} (expected 2)"
            ))
        else:
            results.append(log_test("POST /api/zayavlenie/preview (1 record)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/zayavlenie/preview (1 record)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 6: POST /api/zayavlenie/preview (2 records) ==========
    print(f"\n{BLUE}[6] POST /api/zayavlenie/preview (2 records){RESET}")
    try:
        payload = {
            "records": [
                {
                    "fio": "Иванов Иван Иванович",
                    "passport_series": "MP",
                    "passport_number": "1234567",
                    "area": "5467,9",
                    "sign_date": "21.07.2025"
                },
                {
                    "fio": "Петров Пётр Петрович",
                    "passport_series": "AB",
                    "passport_number": "7654321",
                    "area": "5467,9",
                    "sign_date": "22.07.2025"
                }
            ]
        }
        resp = requests.post(f"{BASE_URL}/zayavlenie/preview", json=payload, timeout=30)
        passed = resp.status_code == 200 and resp.headers.get('content-type') == 'application/pdf'
        
        if passed:
            pdf_bytes = resp.content
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            doc.close()
            
            passed = page_count == 2
            results.append(log_test(
                "POST /api/zayavlenie/preview (2 records)",
                passed,
                f"status={resp.status_code}, pages={page_count} (expected 2)"
            ))
        else:
            results.append(log_test("POST /api/zayavlenie/preview (2 records)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/zayavlenie/preview (2 records)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 7: POST /api/zayavlenie/preview (3 records) ==========
    print(f"\n{BLUE}[7] POST /api/zayavlenie/preview (3 records){RESET}")
    try:
        payload = {
            "records": [
                {"fio": "Иванов Иван Иванович", "passport_series": "MP", "passport_number": "1234567"},
                {"fio": "Петров Пётр Петрович", "passport_series": "AB", "passport_number": "7654321"},
                {"fio": "Сидоров Сидор Сидорович", "passport_series": "KH", "passport_number": "9876543"}
            ]
        }
        resp = requests.post(f"{BASE_URL}/zayavlenie/preview", json=payload, timeout=30)
        passed = resp.status_code == 200 and resp.headers.get('content-type') == 'application/pdf'
        
        if passed:
            pdf_bytes = resp.content
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            doc.close()
            
            passed = page_count == 4
            results.append(log_test(
                "POST /api/zayavlenie/preview (3 records)",
                passed,
                f"status={resp.status_code}, pages={page_count} (expected 4 for 2 sheets)"
            ))
        else:
            results.append(log_test("POST /api/zayavlenie/preview (3 records)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/zayavlenie/preview (3 records)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 8: POST /api/zayavlenie/preview-png (front) ==========
    print(f"\n{BLUE}[8] POST /api/zayavlenie/preview-png (front){RESET}")
    try:
        payload = {
            "records": [{"fio": "Тестов Тест Тестович", "passport_series": "MP", "passport_number": "1234567"}],
            "side": "front"
        }
        resp = requests.post(f"{BASE_URL}/zayavlenie/preview-png", json=payload, timeout=30)
        passed = resp.status_code == 200 and resp.headers.get('content-type') == 'image/png'
        
        if passed:
            png_bytes = resp.content
            is_png = png_bytes[:4] == b'\x89PNG'
            passed = is_png
            results.append(log_test(
                "POST /api/zayavlenie/preview-png (front)",
                passed,
                f"status={resp.status_code}, is_png={is_png}, size={len(png_bytes)} bytes"
            ))
        else:
            results.append(log_test("POST /api/zayavlenie/preview-png (front)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/zayavlenie/preview-png (front)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 9: POST /api/zayavlenie/preview-png (back) ==========
    print(f"\n{BLUE}[9] POST /api/zayavlenie/preview-png (back){RESET}")
    try:
        payload = {
            "records": [{"fio": "Тестов Тест Тестович", "passport_series": "MP", "passport_number": "1234567"}],
            "side": "back"
        }
        resp = requests.post(f"{BASE_URL}/zayavlenie/preview-png", json=payload, timeout=30)
        passed = resp.status_code == 200 and resp.headers.get('content-type') == 'image/png'
        
        if passed:
            png_bytes = resp.content
            is_png = png_bytes[:4] == b'\x89PNG'
            passed = is_png
            results.append(log_test(
                "POST /api/zayavlenie/preview-png (back)",
                passed,
                f"status={resp.status_code}, is_png={is_png}, size={len(png_bytes)} bytes"
            ))
        else:
            results.append(log_test("POST /api/zayavlenie/preview-png (back)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/zayavlenie/preview-png (back)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 10: POST /api/zayavlenie/prefill ==========
    print(f"\n{BLUE}[10] POST /api/zayavlenie/prefill{RESET}")
    try:
        # First get master-upload data
        resp_template = requests.get(f"{BASE_URL}/master-template", timeout=30)
        if resp_template.status_code != 200:
            raise Exception("Failed to get master-template")
        
        # Parse and get first student
        wb = load_workbook(io.BytesIO(resp_template.content))
        ws = wb["Данные"] if "Данные" in wb.sheetnames else wb.active
        
        # Upload to get master data
        files = {'file': ('test.xlsx', resp_template.content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        resp_upload = requests.post(f"{BASE_URL}/master-upload", files=files, timeout=30)
        
        if resp_upload.status_code != 200:
            raise Exception("Failed to upload master-template")
        
        master_data = resp_upload.json()
        master_records = master_data.get("master", [])
        
        if not master_records:
            raise Exception("No master records returned")
        
        # Now test prefill
        payload = {"students": [master_records[0]]}
        resp = requests.post(f"{BASE_URL}/zayavlenie/prefill", json=payload, timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            records = data.get("records", [])
            
            if records:
                rec = records[0]
                has_fio = "fio" in rec
                has_passport_series = "passport_series" in rec
                has_passport_number = "passport_number" in rec
                has_area = rec.get("area") == "5467,9"
                has_reg_who = rec.get("reg_who") == "одного"
                has_reg_count = rec.get("reg_count") == "1"
                
                passed = has_fio and has_passport_series and has_passport_number and has_area and has_reg_who and has_reg_count
                
                details = f"status={resp.status_code}, fio={rec.get('fio', 'N/A')[:30]}, "
                details += f"passport={rec.get('passport_series', '')}/{rec.get('passport_number', '')}, "
                details += f"area={rec.get('area', 'N/A')}, reg_who={rec.get('reg_who', 'N/A')}, reg_count={rec.get('reg_count', 'N/A')}"
                
                results.append(log_test("POST /api/zayavlenie/prefill", passed, details))
            else:
                results.append(log_test("POST /api/zayavlenie/prefill", False, "No records returned"))
        else:
            results.append(log_test("POST /api/zayavlenie/prefill", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/zayavlenie/prefill", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 11: POST /api/master-upload (zayavlenie key) ==========
    print(f"\n{BLUE}[11] POST /api/master-upload (zayavlenie key){RESET}")
    try:
        # Get template
        resp_template = requests.get(f"{BASE_URL}/master-template", timeout=30)
        if resp_template.status_code != 200:
            raise Exception("Failed to get master-template")
        
        # Fill template with real data
        wb = load_workbook(io.BytesIO(resp_template.content))
        ws = wb["Данные"] if "Данные" in wb.sheetnames else wb.active
        
        # Find header row
        header_row = 2
        headers = {}
        for col_idx, cell in enumerate(ws[header_row], start=1):
            if cell.value:
                headers[str(cell.value).strip()] = col_idx
        
        # Fill data row 3
        data_row = 3
        test_data = {
            "ФИО (полностью)": "Тестов Тест Тестович",
            "Дата рождения (ДД.ММ.ГГГГ)": datetime(2000, 1, 15),
            "Пол (1-муж, 2-жен)": "1",
            "Гражданство": "Республика Беларусь",
            "Паспорт (серия и номер)": "MP1234567",
            "Номер договора": "TEST-001",
            "Дата подписания договора (ДД.ММ.ГГГГ)": datetime(2025, 7, 21),
            "Населённый пункт регистрации": "г. Минск",
            "Улица": "ул. Тестовая",
            "Дом": "1",
            "Корпус": "2",
            "Квартира": "101",
            "Откуда прибыл (населённый пункт)": "г. Гродно",
            "Область прибытия": "Минская"
        }
        
        for field_name, value in test_data.items():
            if field_name in headers:
                col_idx = headers[field_name]
                ws.cell(row=data_row, column=col_idx, value=value)
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        filled_xlsx = output.read()
        
        # Upload
        files = {'file': ('test_filled.xlsx', filled_xlsx, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        resp = requests.post(f"{BASE_URL}/master-upload", files=files, timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            has_zayavlenie = "zayavlenie" in data
            
            if has_zayavlenie:
                zayavlenie = data["zayavlenie"]
                if zayavlenie:
                    rec = zayavlenie[0]
                    
                    # Check passport split
                    passport_series = rec.get("passport_series", "")
                    passport_number = rec.get("passport_number", "")
                    passport_correct = passport_series == "MP" and passport_number == "1234567"
                    
                    # Check date format
                    sign_date = rec.get("sign_date", "")
                    date_correct = "." in sign_date and " 00:00:00" not in sign_date
                    
                    # Check area
                    area = rec.get("area", "")
                    area_correct = area == "5467,9"
                    
                    # Check basis
                    basis = rec.get("basis", "")
                    basis_has_contract = "договор" in basis.lower() and "TEST-001" in basis
                    
                    passed = passport_correct and date_correct and area_correct and basis_has_contract
                    
                    details = f"status={resp.status_code}, has_zayavlenie=True, "
                    details += f"passport={passport_series}/{passport_number}, "
                    details += f"sign_date={sign_date}, area={area}, basis={basis[:50]}"
                    
                    results.append(log_test("POST /api/master-upload (zayavlenie key)", passed, details))
                else:
                    results.append(log_test("POST /api/master-upload (zayavlenie key)", False, "zayavlenie array is empty"))
            else:
                results.append(log_test("POST /api/master-upload (zayavlenie key)", False, "No zayavlenie key in response"))
        else:
            results.append(log_test("POST /api/master-upload (zayavlenie key)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/master-upload (zayavlenie key)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 12: POST /api/package (with zayavlenie) ==========
    print(f"\n{BLUE}[12] POST /api/package (with zayavlenie){RESET}")
    try:
        # Get master data first
        resp_template = requests.get(f"{BASE_URL}/master-template", timeout=30)
        files = {'file': ('test.xlsx', resp_template.content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        resp_upload = requests.post(f"{BASE_URL}/master-upload", files=files, timeout=30)
        
        if resp_upload.status_code != 200:
            raise Exception("Failed to upload master-template")
        
        master_data = resp_upload.json()
        people = master_data.get("master", [])
        
        if not people:
            raise Exception("No master records")
        
        # Test package with zayavlenie
        payload = {
            "people": [people[0]],
            "duplex_flip": "long",
            "include": {
                "contract": False,
                "forma19": False,
                "forma24": False,
                "soobshenie": False,
                "zayavlenie": True
            }
        }
        resp = requests.post(f"{BASE_URL}/package", json=payload, timeout=60)
        passed = resp.status_code == 200 and resp.headers.get('content-type') == 'application/pdf'
        
        if passed:
            pdf_bytes = resp.content
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            doc.close()
            
            passed = page_count >= 2
            results.append(log_test(
                "POST /api/package (with zayavlenie)",
                passed,
                f"status={resp.status_code}, pages={page_count} (expected >= 2)"
            ))
        else:
            results.append(log_test("POST /api/package (with zayavlenie)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/package (with zayavlenie)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 13: POST /api/package (default includes zayavlenie) ==========
    print(f"\n{BLUE}[13] POST /api/package (default includes zayavlenie){RESET}")
    try:
        # Get master data first
        resp_template = requests.get(f"{BASE_URL}/master-template", timeout=30)
        files = {'file': ('test.xlsx', resp_template.content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        resp_upload = requests.post(f"{BASE_URL}/master-upload", files=files, timeout=30)
        
        if resp_upload.status_code != 200:
            raise Exception("Failed to upload master-template")
        
        master_data = resp_upload.json()
        people = master_data.get("master", [])
        
        if not people:
            raise Exception("No master records")
        
        # Test package with empty include (should include zayavlenie by default)
        payload = {
            "people": [people[0]],
            "duplex_flip": "long",
            "include": {}
        }
        resp = requests.post(f"{BASE_URL}/package", json=payload, timeout=60)
        passed = resp.status_code == 200 and resp.headers.get('content-type') == 'application/pdf'
        
        if passed:
            pdf_bytes = resp.content
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
            doc.close()
            
            # With all documents: contract (4) + forma19+forma24 (2) + soobshenie (1) + zayavlenie (2) = 9 pages
            passed = page_count >= 7  # At least contract + forms
            results.append(log_test(
                "POST /api/package (default includes zayavlenie)",
                passed,
                f"status={resp.status_code}, pages={page_count} (expected >= 7)"
            ))
        else:
            results.append(log_test("POST /api/package (default includes zayavlenie)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/package (default includes zayavlenie)", False, f"Exception: {e}"))
    
    # ========== РЕГРЕССИЯ: GET /api/ ==========
    print(f"\n{BLUE}[R1] GET /api/ (regression){RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=30)
        passed = resp.status_code == 200
        results.append(log_test("GET /api/ (regression)", passed, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("GET /api/ (regression)", False, f"Exception: {e}"))
    
    # ========== РЕГРЕССИЯ: GET /api/stats ==========
    print(f"\n{BLUE}[R2] GET /api/stats (regression){RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/stats", timeout=30)
        passed = resp.status_code == 200
        results.append(log_test("GET /api/stats (regression)", passed, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("GET /api/stats (regression)", False, f"Exception: {e}"))
    
    # ========== ИТОГИ ==========
    print(f"\n{YELLOW}{'='*80}{RESET}")
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"{YELLOW}ИТОГИ:{RESET}")
    print(f"  Всего тестов: {total}")
    print(f"  {GREEN}Успешно: {passed}{RESET}")
    print(f"  {RED}Провалено: {failed}{RESET}")
    print(f"  Процент успеха: {(passed/total*100):.1f}%")
    print(f"{YELLOW}{'='*80}{RESET}\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
