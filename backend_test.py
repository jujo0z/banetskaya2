#!/usr/bin/env python3
"""
Тест фикса парсинга дат из Excel для приложения Banetskaya.by (Document Engine).

Проверяет, что даты из Excel (объекты datetime) корректно конвертируются
в белорусский формат ДД.ММ.ГГГГ, а не остаются в виде "YYYY-MM-DD 00:00:00".
"""
import io
import sys
import requests
from datetime import datetime, date
from openpyxl import load_workbook

# Backend URL
BASE_URL = "https://cdb3aa12-3471-40c2-bf41-ada0349ed1fe.preview.emergentagent.com/api"

# Цвета для вывода
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def log_test(name, passed, details=""):
    """Логирование результата теста."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {name}")
    if details:
        print(f"       {details}")
    return passed

def check_date_format(value, field_name):
    """Проверяет, что значение даты в формате ДД.ММ.ГГГГ, а не YYYY-MM-DD или ISO."""
    if not value or not isinstance(value, str):
        return True, ""
    
    # Проверяем, что НЕ содержит "YYYY-MM-DD" или "00:00:00"
    if " 00:00:00" in value:
        return False, f"{field_name}='{value}' содержит ' 00:00:00' (не конвертировано)"
    
    # Проверяем, что НЕ в ISO формате (YYYY-MM-DD)
    if len(value) >= 10 and value[4] == '-' and value[7] == '-':
        return False, f"{field_name}='{value}' в ISO формате YYYY-MM-DD (не конвертировано)"
    
    # Проверяем, что в формате ДД.ММ.ГГГГ
    parts = value.split('.')
    if len(parts) == 3:
        try:
            day, month, year = parts
            if len(day) == 2 and len(month) == 2 and len(year) == 4:
                return True, f"{field_name}='{value}' ✓"
        except Exception:
            pass
    
    return True, f"{field_name}='{value}' (формат не распознан, но нет явных ошибок)"

def main():
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}ТЕСТ ФИКСА ПАРСИНГА ДАТ ИЗ EXCEL{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}\n")
    
    results = []
    date_values = []
    
    # ========== ТЕСТ 1: GET /api/master-template ==========
    print(f"\n{YELLOW}[1] GET /api/master-template{RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/master-template", timeout=30)
        passed = resp.status_code == 200 and resp.headers.get('content-type', '').startswith('application/vnd.openxmlformats')
        results.append(log_test(
            "GET /api/master-template",
            passed,
            f"status={resp.status_code}, content-type={resp.headers.get('content-type', 'N/A')[:50]}"
        ))
        
        if not passed:
            print(f"{RED}Не удалось скачать шаблон. Прерываем тест.{RESET}")
            sys.exit(1)
        
        template_bytes = resp.content
        print(f"       Шаблон скачан, размер: {len(template_bytes)} байт")
        
    except Exception as e:
        results.append(log_test("GET /api/master-template", False, f"Exception: {e}"))
        sys.exit(1)
    
    # ========== ТЕСТ 2: Заполнение шаблона с datetime объектами ==========
    print(f"\n{YELLOW}[2] Заполнение шаблона с datetime объектами{RESET}")
    try:
        wb = load_workbook(io.BytesIO(template_bytes))
        ws = wb["Данные"] if "Данные" in wb.sheetnames else wb.active
        
        # Найдём строку заголовков (обычно строка 2)
        header_row = 2
        headers = {}
        for col_idx, cell in enumerate(ws[header_row], start=1):
            if cell.value:
                headers[str(cell.value).strip()] = col_idx
        
        print(f"       Найдено {len(headers)} колонок в шаблоне")
        
        # Заполним строку 3 реальными данными с datetime объектами
        data_row = 3
        
        # Реальные datetime объекты для дат
        test_dates = {
            "Дата рождения (ДД.ММ.ГГГГ)": datetime(2006, 8, 3),  # 03.08.2006
            "Паспорт: дата выдачи": datetime(2020, 1, 10),       # 10.01.2020
            "Паспорт: действителен до": datetime(2030, 1, 10),   # 10.01.2030
            "Дата прибытия": datetime(2024, 9, 1),               # 01.09.2024
            "Проживал там с": datetime(2010, 1, 1),              # 01.01.2010
            "Дата подписания договора": datetime(2025, 7, 21),   # 21.07.2025
            "Дата приказа": datetime(2025, 7, 21),               # 21.07.2025
            "Срок договора до": datetime(2028, 6, 30),           # 30.06.2028
            "Дата сообщения": datetime(2024, 9, 1),              # 01.09.2024
            "Зарегистрирован с": datetime(2024, 9, 1),           # 01.09.2024
            "Зарегистрирован по": datetime(2028, 6, 30),         # 30.06.2028
            "Срок пребывания (по...)": datetime(2028, 6, 30),    # 30.06.2028
        }
        
        # Заполним текстовые поля
        text_data = {
            "ФИО (полностью)": "Иванов Иван Иванович",
            "Пол (1-муж, 2-жен)": "1",
            "Национальность": "белорус",
            "Гражданство": "Республика Беларусь",
            "Телефон": "+375291234567",
            "Идентификационный номер (ИИН)": "3060803A011PB5",
            "Паспорт (серия и номер)": "AB 1234567",
            "Паспорт: кем выдан": "Первомайским РУВД г. Минска",
            "Место рождения: город (пгт)": "Минск",
            "Жительство: город (пгт)": "Минск",
            "Жительство: улица": "пр-т Дзержинского",
            "Жительство: дом": "85",
            "Жительство: комната/квартира": "302/2",
            "Откуда прибыл: город (пгт)": "Гомель",
            "Номер договора": "0047390 003370",
            "Номер приказа": "228",
            "Номер комнаты": "302/2",
            "Орган регистрации": "Первомайский РУВД г. Минска",
            "№ сообщения": "125",
            "Начальник (ФИО)": "Петров П.П.",
            "Цель приезда (текст, Ф.19)": "на обучение",
            "Цель приезда Ф.24 (1-работа, 2-обучение)": "2",
        }
        
        # Заполняем ячейки
        for header, value in test_dates.items():
            if header in headers:
                col_idx = headers[header]
                cell = ws.cell(row=data_row, column=col_idx)
                cell.value = value  # ВАЖНО: записываем datetime объект, не строку!
                print(f"       Заполнено {header}: {value} (тип: {type(value).__name__})")
        
        for header, value in text_data.items():
            if header in headers:
                col_idx = headers[header]
                ws.cell(row=data_row, column=col_idx, value=value)
        
        # Сохраняем в BytesIO
        filled_file = io.BytesIO()
        wb.save(filled_file)
        filled_file.seek(0)
        filled_bytes = filled_file.getvalue()
        
        results.append(log_test(
            "Заполнение шаблона с datetime объектами",
            True,
            f"Заполнено {len(test_dates)} полей-дат с datetime объектами"
        ))
        
    except Exception as e:
        results.append(log_test("Заполнение шаблона", False, f"Exception: {e}"))
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # ========== ТЕСТ 3: POST /api/master-upload ==========
    print(f"\n{YELLOW}[3] POST /api/master-upload{RESET}")
    try:
        files = {'file': ('test_data.xlsx', filled_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        resp = requests.post(f"{BASE_URL}/master-upload", files=files, timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            count = data.get('count', 0)
            master = data.get('master', [])
            contracts = data.get('contracts', [])
            forma19 = data.get('forma19', [])
            forma24 = data.get('forma24', [])
            soobshenie = data.get('soobshenie', [])
            
            results.append(log_test(
                "POST /api/master-upload",
                True,
                f"status=200, count={count}, master={len(master)}, contracts={len(contracts)}"
            ))
            
            # Проверяем формат дат во ВСЕХ возвращённых данных
            print(f"\n       {YELLOW}Проверка формата дат в master:{RESET}")
            if master:
                person = master[0]
                date_fields = ['birth_date', 'passport_issue_date', 'passport_valid_until', 
                              'arrival_date', 'lived_since', 'sign_date', 'order_date', 
                              'contract_end_date', 'reg_date', 'reg_from_date', 'reg_to_date', 
                              'purpose_term']
                
                all_dates_ok = True
                for field in date_fields:
                    if field in person:
                        ok, msg = check_date_format(person[field], field)
                        print(f"         {msg}")
                        date_values.append((field, person[field]))
                        if not ok:
                            all_dates_ok = False
                
                results.append(log_test(
                    "Формат дат в master",
                    all_dates_ok,
                    "Все даты в формате ДД.ММ.ГГГГ" if all_dates_ok else "Найдены даты в неправильном формате"
                ))
            
            print(f"\n       {YELLOW}Проверка формата дат в contracts:{RESET}")
            if contracts:
                contract = contracts[0]
                contract_date_fields = ['birth_date', 'passport_issue_date', 'passport_valid_until',
                                       'sign_date', 'order_date', 'contract_end_date']
                
                all_dates_ok = True
                for field in contract_date_fields:
                    if field in contract:
                        ok, msg = check_date_format(contract[field], field)
                        print(f"         {msg}")
                        date_values.append((f"contract.{field}", contract[field]))
                        if not ok:
                            all_dates_ok = False
                
                results.append(log_test(
                    "Формат дат в contracts",
                    all_dates_ok,
                    "Все даты в формате ДД.ММ.ГГГГ" if all_dates_ok else "Найдены даты в неправильном формате"
                ))
            
            print(f"\n       {YELLOW}Проверка формата дат в forma19:{RESET}")
            if forma19:
                f19 = forma19[0]
                # В forma19 даты разбиты на компоненты (birth_day, birth_month, birth_year)
                # но arrival_date и purpose_term остаются целыми
                f19_date_fields = ['arrival_date', 'purpose_term']
                
                all_dates_ok = True
                for field in f19_date_fields:
                    if field in f19:
                        ok, msg = check_date_format(f19[field], field)
                        print(f"         {msg}")
                        date_values.append((f"forma19.{field}", f19[field]))
                        if not ok:
                            all_dates_ok = False
                
                # Проверяем компоненты даты рождения
                if 'birth_day' in f19 and 'birth_month' in f19 and 'birth_year' in f19:
                    birth_str = f"{f19.get('birth_day', '')}.{f19.get('birth_month', '')}.{f19.get('birth_year', '')}"
                    print(f"         birth_date (компоненты)='{birth_str}' ✓")
                
                results.append(log_test(
                    "Формат дат в forma19",
                    all_dates_ok,
                    "Все даты в формате ДД.ММ.ГГГГ" if all_dates_ok else "Найдены даты в неправильном формате"
                ))
            
            print(f"\n       {YELLOW}Проверка формата дат в forma24:{RESET}")
            if forma24:
                f24 = forma24[0]
                f24_date_fields = ['arrival_date', 'lived_since', 'term']
                
                all_dates_ok = True
                for field in f24_date_fields:
                    if field in f24:
                        ok, msg = check_date_format(f24[field], field)
                        print(f"         {msg}")
                        date_values.append((f"forma24.{field}", f24[field]))
                        if not ok:
                            all_dates_ok = False
                
                results.append(log_test(
                    "Формат дат в forma24",
                    all_dates_ok,
                    "Все даты в формате ДД.ММ.ГГГГ" if all_dates_ok else "Найдены даты в неправильном формате"
                ))
            
            print(f"\n       {YELLOW}Проверка формат дат в soobshenie:{RESET}")
            if soobshenie:
                soob = soobshenie[0]
                # В soobshenie даты разбиты на компоненты (date_day, date_month, date_year и т.д.)
                # Проверяем, что компоненты не содержат "00:00:00"
                date_components = ['date_day', 'date_month', 'date_year', 
                                  'issue_day', 'issue_month', 'issue_year',
                                  'from_day', 'from_month', 'from_year',
                                  'to_day', 'to_month', 'to_year']
                
                all_dates_ok = True
                for field in date_components:
                    if field in soob:
                        value = soob[field]
                        if " 00:00:00" in str(value):
                            print(f"         {field}='{value}' ✗ содержит ' 00:00:00'")
                            all_dates_ok = False
                        else:
                            print(f"         {field}='{value}' ✓")
                
                results.append(log_test(
                    "Формат дат в soobshenie",
                    all_dates_ok,
                    "Все компоненты дат корректны" if all_dates_ok else "Найдены компоненты с ' 00:00:00'"
                ))
        else:
            results.append(log_test(
                "POST /api/master-upload",
                False,
                f"status={resp.status_code}, body={resp.text[:200]}"
            ))
    
    except Exception as e:
        results.append(log_test("POST /api/master-upload", False, f"Exception: {e}"))
        import traceback
        traceback.print_exc()
    
    # ========== ТЕСТ 4: POST /api/generate/upload (режим master) ==========
    print(f"\n{YELLOW}[4] POST /api/generate/upload (режим master){RESET}")
    try:
        files = {'file': ('test_data.xlsx', filled_bytes, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        resp = requests.post(f"{BASE_URL}/generate/upload", files=files, timeout=30)
        passed = resp.status_code == 200
        
        if passed:
            data = resp.json()
            mode = data.get('mode', '')
            students = data.get('students', [])
            masters = data.get('masters', [])
            
            results.append(log_test(
                "POST /api/generate/upload",
                mode == 'master',
                f"status=200, mode={mode}, students={len(students)}, masters={len(masters)}"
            ))
            
            # Проверяем формат дат в students (поля договора)
            print(f"\n       {YELLOW}Проверка формата дат в students:{RESET}")
            if students:
                student = students[0]
                student_date_fields = ['birth_date', 'passport_issue_date', 'passport_valid_until',
                                      'sign_date', 'order_date', 'contract_end_date']
                
                all_dates_ok = True
                for field in student_date_fields:
                    if field in student:
                        ok, msg = check_date_format(student[field], field)
                        print(f"         {msg}")
                        date_values.append((f"student.{field}", student[field]))
                        if not ok:
                            all_dates_ok = False
                
                results.append(log_test(
                    "Формат дат в students (generate/upload)",
                    all_dates_ok,
                    "Все даты в формате ДД.ММ.ГГГГ" if all_dates_ok else "Найдены даты в неправильном формате"
                ))
        else:
            results.append(log_test(
                "POST /api/generate/upload",
                False,
                f"status={resp.status_code}, body={resp.text[:200]}"
            ))
    
    except Exception as e:
        results.append(log_test("POST /api/generate/upload", False, f"Exception: {e}"))
        import traceback
        traceback.print_exc()
    
    # ========== ТЕСТ 5: POST /api/package (дополнительно) ==========
    print(f"\n{YELLOW}[5] POST /api/package (дополнительно){RESET}")
    try:
        # Используем данные из master-upload
        if master and len(master) > 0:
            payload = {
                "people": [master[0]],
                "duplex_flip": "long",
                "include": {
                    "contract": True,
                    "forma19": True,
                    "forma24": True,
                    "soobshenie": True
                }
            }
            resp = requests.post(f"{BASE_URL}/package", json=payload, timeout=60)
            passed = resp.status_code == 200 and resp.headers.get('content-type', '').startswith('application/pdf')
            
            results.append(log_test(
                "POST /api/package",
                passed,
                f"status={resp.status_code}, content-type={resp.headers.get('content-type', 'N/A')[:50]}, size={len(resp.content)} байт"
            ))
            
            if passed:
                print(f"       Пакет документов сгенерирован успешно (PDF, {len(resp.content)} байт)")
        else:
            results.append(log_test("POST /api/package", False, "Нет данных master для теста"))
    
    except Exception as e:
        results.append(log_test("POST /api/package", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 6: Регрессия - GET /api/ ==========
    print(f"\n{YELLOW}[6] Регрессия: GET /api/{RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=10)
        passed = resp.status_code == 200
        results.append(log_test(
            "GET /api/",
            passed,
            f"status={resp.status_code}"
        ))
    except Exception as e:
        results.append(log_test("GET /api/", False, f"Exception: {e}"))
    
    # ========== ТЕСТ 7: Регрессия - GET /api/stats ==========
    print(f"\n{YELLOW}[7] Регрессия: GET /api/stats{RESET}")
    try:
        resp = requests.get(f"{BASE_URL}/stats", timeout=10)
        passed = resp.status_code == 200
        if passed:
            data = resp.json()
            has_keys = all(k in data for k in ['total', 'drafts', 'this_month', 'datasets', 'recent'])
            passed = has_keys
        
        results.append(log_test(
            "GET /api/stats",
            passed,
            f"status={resp.status_code}, keys={'OK' if has_keys else 'MISSING'}"
        ))
    except Exception as e:
        results.append(log_test("GET /api/stats", False, f"Exception: {e}"))
    
    # ========== ИТОГИ ==========
    print(f"\n{YELLOW}{'='*80}{RESET}")
    print(f"{YELLOW}ИТОГИ ТЕСТИРОВАНИЯ{RESET}")
    print(f"{YELLOW}{'='*80}{RESET}\n")
    
    total = len(results)
    passed = sum(1 for r in results if r)
    failed = total - passed
    
    print(f"Всего тестов: {total}")
    print(f"{GREEN}Успешно: {passed}{RESET}")
    if failed > 0:
        print(f"{RED}Провалено: {failed}{RESET}")
    
    # Выводим все значения дат, которые мы нашли
    if date_values:
        print(f"\n{YELLOW}КОНКРЕТНЫЕ ЗНАЧЕНИЯ ПОЛЕЙ-ДАТ:{RESET}")
        for field, value in date_values:
            # Проверяем на наличие проблемных паттернов
            if " 00:00:00" in str(value) or (len(str(value)) >= 10 and str(value)[4] == '-'):
                print(f"  {RED}✗{RESET} {field}: '{value}'")
            else:
                print(f"  {GREEN}✓{RESET} {field}: '{value}'")
    
    print(f"\n{YELLOW}{'='*80}{RESET}")
    
    # Главный критерий успеха
    has_bad_dates = any(" 00:00:00" in str(v) or (len(str(v)) >= 10 and str(v)[4] == '-') 
                       for _, v in date_values)
    
    if has_bad_dates:
        print(f"\n{RED}❌ КРИТИЧЕСКИЙ ПРОВАЛ: Найдены даты в формате 'YYYY-MM-DD 00:00:00' или ISO{RESET}")
        print(f"{RED}   Фикс парсинга дат НЕ РАБОТАЕТ!{RESET}\n")
        sys.exit(1)
    else:
        print(f"\n{GREEN}✅ УСПЕХ: Все даты в формате ДД.ММ.ГГГГ{RESET}")
        print(f"{GREEN}   Фикс парсинга дат РАБОТАЕТ КОРРЕКТНО!{RESET}\n")
        sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
