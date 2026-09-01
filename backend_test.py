#!/usr/bin/env python3
"""
Тестирование backend API раздела «Заселение» (residents).
Проверяет эндпоинты /api/residents/* согласно чек-листу из test_result.md.
"""
import requests
import json
from pathlib import Path

# Base URL из frontend/.env
BASE_URL = "https://cloud-server-1.preview.emergentagent.com/api"

# Тестовый файл заселения
TEST_FILE = Path("/tmp/zaselenie.xlsx")

# Цвета для вывода
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def log_test(name, passed, details=""):
    """Логирование результата теста."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} {BOLD}{name}{RESET}")
    if details:
        print(f"    {details}")
    return passed

def test_1_import_excel():
    """Тест 1: POST /api/residents/import с файлом /tmp/zaselenie.xlsx → {imported:674}"""
    print(f"\n{BOLD}=== ТЕСТ 1: Импорт Excel заселения ==={RESET}")
    
    if not TEST_FILE.exists():
        return log_test("POST /api/residents/import", False, 
                       f"Файл {TEST_FILE} не найден")
    
    with open(TEST_FILE, "rb") as f:
        files = {"file": ("zaselenie.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        resp = requests.post(f"{BASE_URL}/residents/import", files=files, timeout=30)
    
    if resp.status_code != 200:
        return log_test("POST /api/residents/import", False, 
                       f"Статус {resp.status_code}, ожидался 200. Ответ: {resp.text[:200]}")
    
    data = resp.json()
    imported = data.get("imported", 0)
    
    # Ожидается 674 жильца, но допускаем небольшое отклонение (>600)
    if imported < 600:
        return log_test("POST /api/residents/import", False, 
                       f"Импортировано {imported} жильцов, ожидалось >600")
    
    return log_test("POST /api/residents/import", True, 
                   f"Импортировано {imported} жильцов (ожидалось ~674)")

def test_2_get_floors():
    """Тест 2: GET /api/residents/floors → этажи 2-9, у каждого people>0, total>600"""
    print(f"\n{BOLD}=== ТЕСТ 2: Получение сводки по этажам ==={RESET}")
    
    resp = requests.get(f"{BASE_URL}/residents/floors", timeout=10)
    
    if resp.status_code != 200:
        return log_test("GET /api/residents/floors", False, 
                       f"Статус {resp.status_code}, ожидался 200")
    
    data = resp.json()
    floors = data.get("floors", [])
    total = data.get("total", 0)
    
    if total < 600:
        return log_test("GET /api/residents/floors", False, 
                       f"total={total}, ожидалось >600")
    
    # Проверяем наличие этажей 2-9
    floor_nums = {f["floor"] for f in floors}
    expected_floors = set(range(2, 10))
    
    if not expected_floors.issubset(floor_nums):
        missing = expected_floors - floor_nums
        return log_test("GET /api/residents/floors", False, 
                       f"Отсутствуют этажи: {missing}")
    
    # Проверяем что у каждого этажа 2-9 есть люди
    for floor in floors:
        if floor["floor"] in expected_floors and floor["people"] == 0:
            return log_test("GET /api/residents/floors", False, 
                           f"Этаж {floor['floor']} имеет people=0")
    
    return log_test("GET /api/residents/floors", True, 
                   f"Этажи 2-9 присутствуют, total={total}")

def test_3_get_floor_9():
    """Тест 3: GET /api/residents/floor/9 → 15 блоков (901-915)"""
    print(f"\n{BOLD}=== ТЕСТ 3: Получение блоков этажа 9 ==={RESET}")
    
    resp = requests.get(f"{BASE_URL}/residents/floor/9", timeout=10)
    
    if resp.status_code != 200:
        return log_test("GET /api/residents/floor/9", False, 
                       f"Статус {resp.status_code}, ожидался 200")
    
    data = resp.json()
    blocks = data.get("blocks", [])
    
    if len(blocks) != 15:
        return log_test("GET /api/residents/floor/9", False, 
                       f"Получено {len(blocks)} блоков, ожидалось 15")
    
    # Проверяем наличие блока 901
    block_nums = [b["block"] for b in blocks]
    if "901" not in block_nums:
        return log_test("GET /api/residents/floor/9", False, 
                       f"Блок 901 не найден. Блоки: {block_nums}")
    
    # Проверяем структуру блоков
    for block in blocks:
        if not all(k in block for k in ["block", "index", "people", "rooms"]):
            return log_test("GET /api/residents/floor/9", False, 
                           f"Блок {block.get('block')} имеет неполную структуру")
    
    return log_test("GET /api/residents/floor/9", True, 
                   f"Получено 15 блоков, включая 901")

def test_4_get_block_902():
    """Тест 4: GET /api/residents/block/902 → проверка checks для Мороз и Чумаков"""
    print(f"\n{BOLD}=== ТЕСТ 4: Получение жильцов блока 902 и проверка сверки с договорами ==={RESET}")
    
    resp = requests.get(f"{BASE_URL}/residents/block/902", timeout=10)
    
    if resp.status_code != 200:
        return log_test("GET /api/residents/block/902", False, 
                       f"Статус {resp.status_code}, ожидался 200")
    
    data = resp.json()
    
    # Проверяем структуру ответа
    if not all(k in data for k in ["block", "floor", "rooms"]):
        return log_test("GET /api/residents/block/902", False, 
                       f"Неполная структура ответа: {data.keys()}")
    
    if data["block"] != "902":
        return log_test("GET /api/residents/block/902", False, 
                       f"block={data['block']}, ожидался '902'")
    
    if data["floor"] != 9:
        return log_test("GET /api/residents/block/902", False, 
                       f"floor={data['floor']}, ожидался 9")
    
    # Собираем всех людей из всех комнат
    all_people = []
    for room_data in data.get("rooms", []):
        all_people.extend(room_data.get("people", []))
    
    # Ищем Мороз Иван Дмитриевич (должен быть без mismatch)
    moroz = None
    for person in all_people:
        if "мороз" in person.get("full_name", "").lower() and "иван" in person.get("full_name", "").lower():
            moroz = person
            break
    
    # Ищем Чумаков Иван Сергеевич (должен быть с room_mismatch=true)
    chumakov = None
    for person in all_people:
        if "чумаков" in person.get("full_name", "").lower() and "иван" in person.get("full_name", "").lower():
            chumakov = person
            break
    
    issues = []
    
    # Проверяем Мороз
    if moroz:
        checks = moroz.get("checks", {})
        if not checks.get("has_contract"):
            issues.append(f"Мороз: has_contract={checks.get('has_contract')}, ожидался True")
        if checks.get("room_mismatch"):
            issues.append(f"Мороз: room_mismatch={checks.get('room_mismatch')}, ожидался False")
        if checks.get("mismatches"):
            issues.append(f"Мороз: mismatches не пустой: {checks.get('mismatches')}")
        print(f"    {GREEN}✓{RESET} Мороз Иван Дмитриевич: has_contract={checks.get('has_contract')}, room_mismatch={checks.get('room_mismatch')}")
    else:
        issues.append("Мороз Иван Дмитриевич не найден в блоке 902")
    
    # Проверяем Чумаков
    if chumakov:
        checks = chumakov.get("checks", {})
        if not checks.get("has_contract"):
            issues.append(f"Чумаков: has_contract={checks.get('has_contract')}, ожидался True")
        if not checks.get("room_mismatch"):
            issues.append(f"Чумаков: room_mismatch={checks.get('room_mismatch')}, ожидался True")
        
        # Проверяем наличие mismatch с field="room"
        mismatches = checks.get("mismatches", [])
        room_mismatch_found = any(m.get("field") == "room" for m in mismatches)
        if not room_mismatch_found:
            issues.append(f"Чумаков: не найден mismatch с field='room' в {mismatches}")
        else:
            # Проверяем значения в mismatch
            room_mm = next((m for m in mismatches if m.get("field") == "room"), {})
            if "902/2" not in str(room_mm.get("accommodation", "")):
                issues.append(f"Чумаков: accommodation не содержит '902/2': {room_mm}")
            if "905/4" not in str(room_mm.get("contract", "")):
                issues.append(f"Чумаков: contract не содержит '905/4': {room_mm}")
        
        print(f"    {GREEN}✓{RESET} Чумаков Иван Сергеевич: has_contract={checks.get('has_contract')}, room_mismatch={checks.get('room_mismatch')}")
    else:
        issues.append("Чумаков Иван Сергеевич не найден в блоке 902")
    
    # Проверяем людей без договора
    people_without_contract = [p for p in all_people if p.get("checks", {}).get("no_contract")]
    if people_without_contract:
        sample = people_without_contract[0]
        checks = sample.get("checks", {})
        mismatches = checks.get("mismatches", [])
        contract_mismatch = any(m.get("field") == "contract" for m in mismatches)
        if not contract_mismatch:
            issues.append(f"Человек без договора ({sample.get('full_name')}): нет mismatch с field='contract'")
        print(f"    {GREEN}✓{RESET} Люди без договора имеют checks.no_contract=true и mismatch 'Договор'")
    
    if issues:
        return log_test("GET /api/residents/block/902", False, 
                       "\n    ".join(issues))
    
    return log_test("GET /api/residents/block/902", True, 
                   f"Сверка с договорами работает корректно")

def test_5_create_resident():
    """Тест 5: POST /api/residents → создание жильца, floor вычисляется из block"""
    print(f"\n{BOLD}=== ТЕСТ 5: Создание нового жильца ==={RESET}")
    
    payload = {
        "full_name": "Тест Тестов Тестович",
        "block": "910",
        "room": "2",
        "benefit": "сирота",
        "study_group": "ТЕСТ-1"
    }
    
    resp = requests.post(f"{BASE_URL}/residents", json=payload, timeout=10)
    
    if resp.status_code != 200:
        return log_test("POST /api/residents", False, 
                       f"Статус {resp.status_code}, ожидался 200. Ответ: {resp.text[:200]}")
    
    data = resp.json()
    
    # Проверяем что floor вычислен правильно (910 → floor 9)
    if data.get("floor") != 9:
        return log_test("POST /api/residents", False, 
                       f"floor={data.get('floor')}, ожидался 9 (из block='910')")
    
    # Проверяем что все поля сохранены
    for key, value in payload.items():
        if data.get(key) != value:
            return log_test("POST /api/residents", False, 
                           f"{key}={data.get(key)}, ожидался '{value}'")
    
    # Сохраняем ID для следующих тестов
    global created_resident_id
    created_resident_id = data.get("id")
    
    return log_test("POST /api/residents", True, 
                   f"Жилец создан, id={created_resident_id}, floor=9")

def test_6_update_resident():
    """Тест 6: PATCH /api/residents/{id} → обновление полей"""
    print(f"\n{BOLD}=== ТЕСТ 6: Обновление жильца ==={RESET}")
    
    if not created_resident_id:
        return log_test("PATCH /api/residents/{id}", False, 
                       "Нет ID созданного жильца (тест 5 не прошёл)")
    
    payload = {
        "benefit": "ЧАЭС",
        "study_group": "НОВ-2",
        "room": "4"
    }
    
    resp = requests.patch(f"{BASE_URL}/residents/{created_resident_id}", 
                         json=payload, timeout=10)
    
    if resp.status_code != 200:
        return log_test("PATCH /api/residents/{id}", False, 
                       f"Статус {resp.status_code}, ожидался 200. Ответ: {resp.text[:200]}")
    
    data = resp.json()
    
    # Проверяем что поля обновились
    for key, value in payload.items():
        if data.get(key) != value:
            return log_test("PATCH /api/residents/{id}", False, 
                           f"{key}={data.get(key)}, ожидался '{value}'")
    
    return log_test("PATCH /api/residents/{id}", True, 
                   f"Поля обновлены: benefit=ЧАЭС, study_group=НОВ-2, room=4")

def test_7_get_resident():
    """Тест 7: GET /api/residents/{id} → проверка обновлений"""
    print(f"\n{BOLD}=== ТЕСТ 7: Получение жильца по ID ==={RESET}")
    
    if not created_resident_id:
        return log_test("GET /api/residents/{id}", False, 
                       "Нет ID созданного жильца (тест 5 не прошёл)")
    
    resp = requests.get(f"{BASE_URL}/residents/{created_resident_id}", timeout=10)
    
    if resp.status_code != 200:
        return log_test("GET /api/residents/{id}", False, 
                       f"Статус {resp.status_code}, ожидался 200")
    
    data = resp.json()
    
    # Проверяем обновлённые значения из теста 6
    expected = {
        "benefit": "ЧАЭС",
        "study_group": "НОВ-2",
        "room": "4",
        "full_name": "Тест Тестов Тестович",
        "block": "910",
        "floor": 9
    }
    
    for key, value in expected.items():
        if data.get(key) != value:
            return log_test("GET /api/residents/{id}", False, 
                           f"{key}={data.get(key)}, ожидался '{value}'")
    
    return log_test("GET /api/residents/{id}", True, 
                   f"Обновления отражены корректно")

def test_8_reimport_preserves_manual_edits():
    """Тест 8: Повторный импорт сохраняет ручные правки (benefit/study_group)"""
    print(f"\n{BOLD}=== ТЕСТ 8: Повторный импорт сохраняет ручные правки ==={RESET}")
    
    # Шаг 1: Получаем любого реального жильца из импорта
    resp = requests.get(f"{BASE_URL}/residents/block/902", timeout=10)
    if resp.status_code != 200:
        return log_test("Повторный импорт (сохранение правок)", False, 
                       "Не удалось получить блок 902")
    
    data = resp.json()
    all_people = []
    for room_data in data.get("rooms", []):
        all_people.extend(room_data.get("people", []))
    
    if not all_people:
        return log_test("Повторный импорт (сохранение правок)", False, 
                       "Нет жильцов в блоке 902")
    
    # Берём первого человека
    person = all_people[0]
    person_id = person.get("id")
    original_name = person.get("full_name")
    
    print(f"    Выбран жилец: {original_name} (id={person_id})")
    
    # Шаг 2: Обновляем benefit
    test_benefit = "ПРОВЕРКА_ЛЬГОТЫ"
    resp = requests.patch(f"{BASE_URL}/residents/{person_id}", 
                         json={"benefit": test_benefit}, timeout=10)
    
    if resp.status_code != 200:
        return log_test("Повторный импорт (сохранение правок)", False, 
                       f"Не удалось обновить benefit: {resp.status_code}")
    
    print(f"    Установлен benefit='{test_benefit}'")
    
    # Шаг 3: Повторный импорт
    with open(TEST_FILE, "rb") as f:
        files = {"file": ("zaselenie.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        resp = requests.post(f"{BASE_URL}/residents/import", files=files, timeout=30)
    
    if resp.status_code != 200:
        return log_test("Повторный импорт (сохранение правок)", False, 
                       f"Повторный импорт не удался: {resp.status_code}")
    
    print(f"    Повторный импорт выполнен")
    
    # Шаг 4: Проверяем что benefit сохранился
    # Ищем человека по ФИО (после импорта ID могут измениться)
    resp = requests.get(f"{BASE_URL}/residents/block/902", timeout=10)
    if resp.status_code != 200:
        return log_test("Повторный импорт (сохранение правок)", False, 
                       "Не удалось получить блок 902 после импорта")
    
    data = resp.json()
    all_people = []
    for room_data in data.get("rooms", []):
        all_people.extend(room_data.get("people", []))
    
    # Ищем нашего человека по ФИО
    found_person = None
    for p in all_people:
        if p.get("full_name") == original_name:
            found_person = p
            break
    
    if not found_person:
        return log_test("Повторный импорт (сохранение правок)", False, 
                       f"Жилец {original_name} не найден после импорта")
    
    if found_person.get("benefit") != test_benefit:
        return log_test("Повторный импорт (сохранение правок)", False, 
                       f"benefit={found_person.get('benefit')}, ожидался '{test_benefit}' (ручная правка не сохранилась)")
    
    return log_test("Повторный импорт (сохранение правок)", True, 
                   f"benefit='{test_benefit}' сохранился после повторного импорта (мердж по ФИО работает)")

def test_9_delete_resident():
    """Тест 9: DELETE /api/residents/{id}"""
    print(f"\n{BOLD}=== ТЕСТ 9: Удаление жильца ==={RESET}")
    
    # Создаём нового жильца для удаления (т.к. после повторного импорта в тесте 8
    # созданный в тесте 5 мог удалиться)
    payload = {
        "full_name": "Удаляемый Жилец Тестович",
        "block": "915",
        "room": "1"
    }
    
    resp = requests.post(f"{BASE_URL}/residents", json=payload, timeout=10)
    if resp.status_code != 200:
        return log_test("DELETE /api/residents/{id}", False, 
                       f"Не удалось создать жильца для удаления: {resp.status_code}")
    
    delete_id = resp.json().get("id")
    print(f"    Создан жилец для удаления: id={delete_id}")
    
    # Удаляем
    resp = requests.delete(f"{BASE_URL}/residents/{delete_id}", timeout=10)
    
    if resp.status_code != 200:
        return log_test("DELETE /api/residents/{id}", False, 
                       f"Статус {resp.status_code}, ожидался 200")
    
    data = resp.json()
    if not data.get("deleted"):
        return log_test("DELETE /api/residents/{id}", False, 
                       f"deleted={data.get('deleted')}, ожидался True")
    
    # Проверяем что жилец действительно удалён
    resp = requests.get(f"{BASE_URL}/residents/{delete_id}", timeout=10)
    if resp.status_code != 404:
        return log_test("DELETE /api/residents/{id}", False, 
                       f"После удаления GET вернул {resp.status_code}, ожидался 404")
    
    return log_test("DELETE /api/residents/{id}", True, 
                   f"Жилец удалён, GET возвращает 404")

def main():
    """Запуск всех тестов."""
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}ТЕСТИРОВАНИЕ BACKEND API: РАЗДЕЛ «ЗАСЕЛЕНИЕ» (residents){RESET}")
    print(f"{BOLD}Base URL: {BASE_URL}{RESET}")
    print(f"{BOLD}{'='*70}{RESET}")
    
    global created_resident_id
    created_resident_id = None
    
    results = []
    
    # Запускаем тесты по порядку
    results.append(test_1_import_excel())
    results.append(test_2_get_floors())
    results.append(test_3_get_floor_9())
    results.append(test_4_get_block_902())
    results.append(test_5_create_resident())
    results.append(test_6_update_resident())
    results.append(test_7_get_resident())
    results.append(test_8_reimport_preserves_manual_edits())
    results.append(test_9_delete_resident())
    
    # Итоги
    print(f"\n{BOLD}{'='*70}{RESET}")
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    if passed == total:
        print(f"{GREEN}{BOLD}✓ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО: {passed}/{total} ({percentage:.0f}%){RESET}")
    else:
        print(f"{RED}{BOLD}✗ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ: {passed}/{total} ({percentage:.0f}%){RESET}")
    
    print(f"{BOLD}{'='*70}{RESET}\n")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
