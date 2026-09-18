#!/usr/bin/env python3
"""
Тест эндпоинта GET/POST /api/app-config для Banetskaya.by.
"""
import sys
import requests

# Backend URL
BASE_URL = "https://vibrant-swartz-12.preview.emergentagent.com/api"

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
    print(f"{YELLOW}ТЕСТ ЭНДПОИНТА /api/app-config{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}\n")
    
    results = []
    
    # ========== ТЕСТ 1: GET /api/app-config (default) ==========
    print(f"\n{BLUE}[1] GET /api/app-config (default){RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/app-config", timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            has_url = "windows_download_url" in data
            passed = has_url
            
            results.append(log_test(
                "GET /api/app-config (default)",
                passed,
                f"status={resp.status_code}, windows_download_url={data.get('windows_download_url', 'N/A')}"
            ))
        else:
            results.append(log_test("GET /api/app-config (default)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("GET /api/app-config (default)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 2: POST /api/app-config (set URL) ==========
    print(f"\n{BLUE}[2] POST /api/app-config (set URL){RESET}")
    try:
        test_url = "https://example.com/banetskaya-setup.exe"
        payload = {"windows_download_url": test_url}
        resp = requests.post(f"{BASE_URL}/app-config", json=payload, timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            saved = data.get("saved", False)
            url_match = data.get("windows_download_url") == test_url
            passed = saved and url_match
            
            results.append(log_test(
                "POST /api/app-config (set URL)",
                passed,
                f"status={resp.status_code}, saved={saved}, url={data.get('windows_download_url', 'N/A')}"
            ))
        else:
            results.append(log_test("POST /api/app-config (set URL)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/app-config (set URL)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 3: GET /api/app-config (verify persistence) ==========
    print(f"\n{BLUE}[3] GET /api/app-config (verify persistence){RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/app-config", timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            url = data.get("windows_download_url", "")
            url_persisted = url == "https://example.com/banetskaya-setup.exe"
            passed = url_persisted
            
            results.append(log_test(
                "GET /api/app-config (verify persistence)",
                passed,
                f"status={resp.status_code}, url={url}"
            ))
        else:
            results.append(log_test("GET /api/app-config (verify persistence)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("GET /api/app-config (verify persistence)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 4: POST /api/app-config (clear URL) ==========
    print(f"\n{BLUE}[4] POST /api/app-config (clear URL){RESET}")
    try:
        payload = {"windows_download_url": ""}
        resp = requests.post(f"{BASE_URL}/app-config", json=payload, timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            saved = data.get("saved", False)
            url_empty = data.get("windows_download_url") == ""
            passed = saved and url_empty
            
            results.append(log_test(
                "POST /api/app-config (clear URL)",
                passed,
                f"status={resp.status_code}, saved={saved}, url='{data.get('windows_download_url', 'N/A')}'"
            ))
        else:
            results.append(log_test("POST /api/app-config (clear URL)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("POST /api/app-config (clear URL)", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 5: GET /api/app-config (verify empty) ==========
    print(f"\n{BLUE}[5] GET /api/app-config (verify empty){RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/app-config", timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            url = data.get("windows_download_url", None)
            url_empty = url == ""
            passed = url_empty
            
            results.append(log_test(
                "GET /api/app-config (verify empty)",
                passed,
                f"status={resp.status_code}, url='{url}'"
            ))
        else:
            results.append(log_test("GET /api/app-config (verify empty)", False, f"status={resp.status_code}"))
    except Exception as e:
        results.append(log_test("GET /api/app-config (verify empty)", False, f"Exception: {e}"))
    
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
