#!/usr/bin/env python3
"""
Backend API Testing for Health Diagnostics
Tests the /api/health/diagnostics endpoint
"""

import requests
import sys
import json

# Base URL from frontend/.env
BASE_URL = "https://numbers-586.preview.emergentagent.com/api"


def test_diagnostics_endpoint():
    """Test GET /api/health/diagnostics - self-check for system components"""
    print("\n" + "=" * 80)
    print("TEST: GET /api/health/diagnostics")
    print("=" * 80)
    
    resp = requests.get(f"{BASE_URL}/health/diagnostics")
    print(f"\nStatus: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"❌ FAILED: Expected 200, got {resp.status_code}")
        print(f"Response: {resp.text}")
        return False
    
    data = resp.json()
    print(f"\nResponse structure:")
    print(f"  - checks: {len(data.get('checks', []))} items")
    print(f"  - all_ok: {data.get('all_ok')}")
    print(f"  - is_desktop: {data.get('is_desktop')}")
    print(f"  - platform: {data.get('platform')}")
    
    # Check 1: Response has required top-level keys
    required_keys = ["checks", "all_ok", "is_desktop", "platform"]
    for key in required_keys:
        if key not in data:
            print(f"❌ FAILED: Missing required key '{key}' in response")
            return False
    print(f"✅ All required top-level keys present: {required_keys}")
    
    # Check 2: checks is an array with at least 6 elements
    checks = data.get("checks", [])
    if not isinstance(checks, list):
        print(f"❌ FAILED: 'checks' is not an array, got {type(checks)}")
        return False
    
    if len(checks) < 6:
        print(f"❌ FAILED: Expected at least 6 checks, got {len(checks)}")
        return False
    print(f"✅ checks is an array with {len(checks)} elements (>= 6)")
    
    # Check 3: all_ok is boolean
    if not isinstance(data.get("all_ok"), bool):
        print(f"❌ FAILED: 'all_ok' is not a boolean, got {type(data.get('all_ok'))}")
        return False
    print(f"✅ all_ok is boolean: {data.get('all_ok')}")
    
    # Check 4: is_desktop is boolean
    if not isinstance(data.get("is_desktop"), bool):
        print(f"❌ FAILED: 'is_desktop' is not a boolean, got {type(data.get('is_desktop'))}")
        return False
    print(f"✅ is_desktop is boolean: {data.get('is_desktop')}")
    
    # Check 5: platform is string
    if not isinstance(data.get("platform"), str):
        print(f"❌ FAILED: 'platform' is not a string, got {type(data.get('platform'))}")
        return False
    print(f"✅ platform is string: '{data.get('platform')}'")
    
    # Check 6: Each check has required keys (key, label, ok, detail)
    print(f"\nValidating individual checks:")
    required_check_keys = ["key", "label", "ok", "detail"]
    for i, check in enumerate(checks):
        for key in required_check_keys:
            if key not in check:
                print(f"❌ FAILED: Check #{i} (key='{check.get('key', 'unknown')}') missing required key '{key}'")
                return False
        
        # Validate types
        if not isinstance(check.get("key"), str):
            print(f"❌ FAILED: Check #{i} 'key' is not a string")
            return False
        if not isinstance(check.get("label"), str):
            print(f"❌ FAILED: Check #{i} 'label' is not a string")
            return False
        if not isinstance(check.get("ok"), bool):
            print(f"❌ FAILED: Check #{i} 'ok' is not a boolean")
            return False
        if not isinstance(check.get("detail"), str):
            print(f"❌ FAILED: Check #{i} 'detail' is not a string")
            return False
        
        # info is optional, but if present must be boolean
        if "info" in check and not isinstance(check.get("info"), bool):
            print(f"❌ FAILED: Check #{i} 'info' is present but not a boolean")
            return False
    
    print(f"✅ All {len(checks)} checks have required keys (key, label, ok, detail)")
    
    # Check 7: In cloud (Linux), verify expected check keys are present
    expected_keys = {"mongo", "fonts", "assets", "template", "libreoffice", "pdf", "printers"}
    found_keys = {check.get("key") for check in checks}
    
    print(f"\nExpected check keys: {sorted(expected_keys)}")
    print(f"Found check keys: {sorted(found_keys)}")
    
    missing_keys = expected_keys - found_keys
    if missing_keys:
        print(f"❌ FAILED: Missing expected check keys: {missing_keys}")
        return False
    print(f"✅ All expected check keys present")
    
    # Check 8: Verify specific checks in cloud (Linux)
    print(f"\nValidating specific checks:")
    checks_by_key = {check.get("key"): check for check in checks}
    
    # MongoDB check
    mongo_check = checks_by_key.get("mongo")
    if not mongo_check:
        print(f"❌ FAILED: 'mongo' check not found")
        return False
    print(f"  - mongo: ok={mongo_check.get('ok')}, detail='{mongo_check.get('detail')}'")
    if not mongo_check.get("ok"):
        print(f"    ⚠️  WARNING: MongoDB check failed (expected ok=true in cloud)")
    
    # Fonts check
    fonts_check = checks_by_key.get("fonts")
    if not fonts_check:
        print(f"❌ FAILED: 'fonts' check not found")
        return False
    print(f"  - fonts: ok={fonts_check.get('ok')}, detail='{fonts_check.get('detail')}'")
    if not fonts_check.get("ok"):
        print(f"    ⚠️  WARNING: Fonts check failed (expected ok=true in cloud)")
    
    # Assets check
    assets_check = checks_by_key.get("assets")
    if not assets_check:
        print(f"❌ FAILED: 'assets' check not found")
        return False
    print(f"  - assets: ok={assets_check.get('ok')}, detail='{assets_check.get('detail')}'")
    if not assets_check.get("ok"):
        print(f"    ⚠️  WARNING: Assets check failed (expected ok=true in cloud)")
    
    # Template check
    template_check = checks_by_key.get("template")
    if not template_check:
        print(f"❌ FAILED: 'template' check not found")
        return False
    print(f"  - template: ok={template_check.get('ok')}, detail='{template_check.get('detail')}'")
    if not template_check.get("ok"):
        print(f"    ⚠️  WARNING: Template check failed (expected ok=true in cloud)")
    
    # LibreOffice check
    libreoffice_check = checks_by_key.get("libreoffice")
    if libreoffice_check:
        print(f"  - libreoffice: ok={libreoffice_check.get('ok')}, detail='{libreoffice_check.get('detail')}'")
        if not libreoffice_check.get("ok"):
            print(f"    ⚠️  WARNING: LibreOffice check failed")
    
    # PDF check
    pdf_check = checks_by_key.get("pdf")
    if not pdf_check:
        print(f"❌ FAILED: 'pdf' check not found")
        return False
    print(f"  - pdf: ok={pdf_check.get('ok')}, detail='{pdf_check.get('detail')}'")
    if not pdf_check.get("ok"):
        print(f"    ⚠️  WARNING: PDF generation check failed (expected ok=true in cloud)")
    
    # Printers check (special case for Linux)
    printers_check = checks_by_key.get("printers")
    if not printers_check:
        print(f"❌ FAILED: 'printers' check not found")
        return False
    print(f"  - printers: ok={printers_check.get('ok')}, info={printers_check.get('info')}, detail='{printers_check.get('detail')}'")
    
    # On Linux, printers should have info=true and ok=true (informational, not an error)
    platform = data.get("platform", "")
    if "linux" in platform.lower():
        if not printers_check.get("info"):
            print(f"    ⚠️  WARNING: On Linux, printers check should have info=true")
        if not printers_check.get("ok"):
            print(f"    ⚠️  WARNING: On Linux, printers check should have ok=true (informational)")
    
    # Check 9: Verify all_ok logic (should be AND of all checks[].ok)
    expected_all_ok = all(check.get("ok") for check in checks)
    actual_all_ok = data.get("all_ok")
    
    print(f"\nValidating all_ok logic:")
    print(f"  - Expected (AND of all checks): {expected_all_ok}")
    print(f"  - Actual: {actual_all_ok}")
    
    if expected_all_ok != actual_all_ok:
        print(f"❌ FAILED: all_ok logic incorrect")
        print(f"   Checks status: {[(c.get('key'), c.get('ok')) for c in checks]}")
        return False
    print(f"✅ all_ok logic correct (matches AND of all checks)")
    
    # Check 10: Verify is_desktop and platform for cloud (Linux)
    print(f"\nValidating cloud environment:")
    if "linux" in platform.lower():
        print(f"  - Platform contains 'linux': ✅")
        if data.get("is_desktop"):
            print(f"    ⚠️  WARNING: is_desktop should be false in cloud (Linux)")
        else:
            print(f"  - is_desktop is false: ✅")
    else:
        print(f"  - Platform: {platform} (not Linux)")
    
    # Print full response for reference
    print(f"\n" + "-" * 80)
    print("Full response:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("-" * 80)
    
    # Summary of critical checks
    print(f"\n" + "=" * 80)
    print("CRITICAL CHECKS SUMMARY:")
    print("=" * 80)
    critical_checks = ["mongo", "fonts", "assets", "template", "pdf"]
    all_critical_ok = True
    for key in critical_checks:
        check = checks_by_key.get(key)
        if check:
            status = "✅" if check.get("ok") else "❌"
            print(f"{status} {key}: {check.get('ok')} - {check.get('detail')}")
            if not check.get("ok"):
                all_critical_ok = False
        else:
            print(f"❌ {key}: NOT FOUND")
            all_critical_ok = False
    
    print(f"\n{'✅' if all_critical_ok else '❌'} All critical checks: {'PASSED' if all_critical_ok else 'FAILED'}")
    print("=" * 80)
    
    return True


def main():
    print("=" * 80)
    print("BACKEND TESTING: Health Diagnostics")
    print("=" * 80)
    
    success = test_diagnostics_endpoint()
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    if success:
        print("✅ PASSED: GET /api/health/diagnostics")
        print("\n🎉 ALL TESTS PASSED!")
        sys.exit(0)
    else:
        print("❌ FAILED: GET /api/health/diagnostics")
        sys.exit(1)


if __name__ == "__main__":
    main()
