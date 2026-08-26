#!/usr/bin/env python3
"""Extract Cyrillic text from PDF to verify font rendering"""
import requests
import pymupdf

BASE_URL = "https://code-review-hub-160.preview.emergentagent.com/api"

# Test overlay/generate
print("=" * 80)
print("EXTRACTING TEXT FROM /api/overlay/generate PDF")
print("=" * 80)
payload = {
    "records": [
        {
            "fio": "Иванов Иван Иванович",
            "address": "г. Минск"
        }
    ],
    "page_size": "card",
    "with_form": True
}
r = requests.post(f"{BASE_URL}/overlay/generate", json=payload, timeout=30)
doc = pymupdf.open(stream=r.content, filetype="pdf")
text = doc[0].get_text()
print(f"\nExtracted text from overlay PDF (first 500 chars):")
print(text[:500])
doc.close()

# Test contracts/preview
print("\n" + "=" * 80)
print("EXTRACTING TEXT FROM /api/contracts/preview?format=pdf")
print("=" * 80)
payload = {
    "fields": {
        "contract_number": "TEST-001",
        "full_name": "Тестов Тест Тестович",
        "citizenship": "Республики Беларусь",
        "birth_date": "01.01.2000",
        "room_number": "101",
        "registration_address": "г. Минск, ул. Тестовая, д. 1",
        "passport_number": "AB1234567",
        "phone": "+375291234567"
    }
}
r = requests.post(f"{BASE_URL}/contracts/preview?format=pdf", json=payload, timeout=120)
doc = pymupdf.open(stream=r.content, filetype="pdf")
text = doc[0].get_text()
print(f"\nExtracted text from contract PDF (first 800 chars):")
print(text[:800])
doc.close()
