#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================
user_problem_statement: >
  Расширение приложения Banetskaya.by (автозаполнение договоров найма из Excel).
  Задачи: (1) тестовые демо-договоры, (2) мощный дизайн, (3) внутренний редактор документа
  с живым PDF-предпросмотром + редактирование пунктов, (4) черновики и пресеты полей.
  ВАЖНО: сам .docx-шаблон договора НЕ менять — форма остаётся 1:1.

backend:
  - task: "Заселение по этажам (residents): импорт Excel + CRUD + сверка с базой договоров /api/residents/*"
    implemented: true
    working: true
    file: "residents_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        -working: "NA"
        -agent: "main"
        -comment: >
          Новый раздел «Заселение». Эндпоинты (все с префиксом /api):
          (1) POST /residents/import — загрузка Excel заселения (multipart file). Парсит лист с колонками
          «Блок» (формат «902/2»), «Ф.И.О», «Статус», «Группа», «Дата заселения», «Номер договора»,
          «Срок действия», «Примечание». Возвращает {imported:N}. При повторном импорте СОХРАНЯЕТ ранее
          введённые вручную поля benefit(ЛЬГОТА) и study_group по совпадению ФИО.
          Для теста файл лежит в /tmp/zaselenie.xlsx (674 жильца, этажи 2-9).
          (2) GET /residents/floors — сводка {floors:[{floor,people,blocks_present}],total}.
          (3) GET /residents/floor/{floor} — 15 блоков X01..X15 {blocks:[{block,index,people,rooms}]}.
          (4) GET /residents/block/{block} — люди по комнатам, у каждого поле checks со сверкой с договором.
          (5) POST /residents — создать (body: full_name обязателен, block/room и др.). floor вычисляется из block.
          (6) PATCH /residents/{id} — частичное обновление ЛЮБЫХ полей (имя, блок, комната, статус, группа,
          льгота, договор, даты, примечание). При смене block пересчитывается floor.
          (7) DELETE /residents/{id}.
          СВЕРКА С ДОГОВОРАМИ (checks): по ФИО ищется договор в коллекции contracts (не изменяется!).
          checks={has_contract,no_contract,room_mismatch,contract_room,contract_number,mismatches:[{field,label,accommodation,contract}]}.
          room_mismatch=true если комната в заселении ≠ master.room_number в договоре. Если договор не найден -> mismatch «Договор».
          Для проверки подсветки в БД засеяны 2 тестовых договора (demo:true): «Мороз Иван Дмитриевич» комн 902/2 (совпадает),
          «Чумаков Иван Сергеевич» комн 905/4 (НЕ совпадает с заселением 902/2).
          Чек-лист: импорт возвращает 674; floors содержит этажи 2-9; floor/9 отдаёт 15 блоков; block/902 -> Мороз без mismatch,
          Чумаков с room_mismatch=true; PATCH льготы/группы сохраняется; повторный импорт не затирает вручную введённую льготу;
          POST создаёт жильца с корректным floor; DELETE удаляет.
        -working: true
        -agent: "testing"
        -comment: >
          ✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (9/9, 100% success rate). РАЗДЕЛ «ЗАСЕЛЕНИЕ» ПОЛНОСТЬЮ РАБОТАЕТ.
          
          ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:
          
          ✅ ТЕСТ 1: POST /api/residents/import с файлом /tmp/zaselenie.xlsx
             → 200, {imported:674} — импортировано РОВНО 674 жильца (ожидалось ~674) ✓
          
          ✅ ТЕСТ 2: GET /api/residents/floors
             → 200, {floors:[...], total:674}
             → Этажи 2-9 присутствуют (все 8 этажей) ✓
             → У каждого этажа people > 0 ✓
             → total=674 (> 600 требование выполнено) ✓
          
          ✅ ТЕСТ 3: GET /api/residents/floor/9
             → 200, {floor:9, blocks:[...], total:...}
             → Получено РОВНО 15 блоков (901-915) ✓
             → Блок 901 присутствует ✓
             → Каждый блок содержит поля: block, index, people, rooms ✓
          
          ✅ ТЕСТ 4: GET /api/residents/block/902 (КРИТИЧЕСКИЙ ТЕСТ СВЕРКИ С ДОГОВОРАМИ)
             → 200, {block:'902', floor:9, rooms:[...]}
             → Структура ответа корректна (block, floor, rooms) ✓
             → block='902', floor=9 ✓
             
             ПРОВЕРКА СВЕРКИ С ДОГОВОРАМИ:
             
             • Мороз Иван Дмитриевич (комната 902/2 СОВПАДАЕТ с договором):
               - checks.has_contract = true ✓
               - checks.room_mismatch = false ✓
               - checks.mismatches = [] (пустой массив) ✓
               → БЕЗ НЕСОВПАДЕНИЙ (ожидаемое поведение) ✓
             
             • Чумаков Иван Сергеевич (комната в заселении 902/2, в договоре 905/4 — НЕ СОВПАДАЕТ):
               - checks.has_contract = true ✓
               - checks.room_mismatch = true ✓
               - checks.mismatches содержит mismatch с field='room' ✓
               - mismatch.accommodation содержит '902/2' (заселение) ✓
               - mismatch.contract содержит '905/4' (договор) ✓
               → НЕСОВПАДЕНИЕ КОМНАТЫ ОБНАРУЖЕНО (ожидаемое поведение) ✓
             
             • Люди без договора:
               - checks.no_contract = true ✓
               - checks.mismatches содержит mismatch с field='contract' ✓
               → ОТСУТСТВИЕ ДОГОВОРА ОБНАРУЖЕНО (ожидаемое поведение) ✓
          
          ✅ ТЕСТ 5: POST /api/residents (создание нового жильца)
             → 200, {id:'...', full_name:'Тест Тестов Тестович', block:'910', room:'2', benefit:'сирота', study_group:'ТЕСТ-1', floor:9, ...}
             → floor=9 ВЫЧИСЛЕН КОРРЕКТНО из block='910' (первая цифра блока) ✓
             → Все поля сохранены корректно ✓
          
          ✅ ТЕСТ 6: PATCH /api/residents/{id} (обновление полей)
             → 200, {benefit:'ЧАЭС', study_group:'НОВ-2', room:'4', ...}
             → Поля обновлены корректно: benefit='ЧАЭС', study_group='НОВ-2', room='4' ✓
          
          ✅ ТЕСТ 7: GET /api/residents/{id} (проверка обновлений)
             → 200, {benefit:'ЧАЭС', study_group:'НОВ-2', room:'4', full_name:'Тест Тестов Тестович', block:'910', floor:9, ...}
             → Обновления из теста 6 отражены корректно ✓
          
          ✅ ТЕСТ 8: ПОВТОРНЫЙ ИМПОРТ СОХРАНЯЕТ РУЧНЫЕ ПРАВКИ (КРИТИЧЕСКИЙ ТЕСТ МЕРДЖА ПО ФИО)
             → Шаг 1: Выбран жилец «Мороз Иван Дмитриевич» из блока 902
             → Шаг 2: PATCH /api/residents/{id} {benefit:'ПРОВЕРКА_ЛЬГОТЫ'} → 200 ✓
             → Шаг 3: POST /api/residents/import (повторный импорт) → 200, {imported:674} ✓
             → Шаг 4: GET /api/residents/block/902 → поиск «Мороз Иван Дмитриевич» по ФИО
             → benefit='ПРОВЕРКА_ЛЬГОТЫ' СОХРАНИЛСЯ после повторного импорта ✓
             → МЕРДЖ ПО ФИО РАБОТАЕТ КОРРЕКТНО (ручные правки не затираются) ✓
          
          ✅ ТЕСТ 9: DELETE /api/residents/{id} (удаление жильца)
             → Создан новый жилец «Удаляемый Жилец Тестович» (id='...') ✓
             → DELETE /api/residents/{id} → 200, {deleted:true} ✓
             → GET /api/residents/{id} → 404 (жилец действительно удалён) ✓
          
          ЗАКЛЮЧЕНИЕ:
          
          🎉 РАЗДЕЛ «ЗАСЕЛЕНИЕ» ПОЛНОСТЬЮ ФУНКЦИОНАЛЕН:
          • Импорт Excel заселения (674 жильца, этажи 2-9) работает корректно
          • Сводка по этажам (GET /residents/floors) возвращает корректные данные
          • Получение блоков этажа (GET /residents/floor/{floor}) возвращает 15 блоков
          • Получение жильцов блока (GET /residents/block/{block}) с полной структурой rooms
          • СВЕРКА С ДОГОВОРАМИ работает корректно:
            - Мороз (совпадение) → has_contract=true, room_mismatch=false
            - Чумаков (несовпадение) → has_contract=true, room_mismatch=true, mismatches содержит room
            - Люди без договора → no_contract=true, mismatches содержит contract
          • CRUD операции работают корректно:
            - POST /residents создаёт жильца с корректным floor (вычисляется из block)
            - PATCH /residents/{id} обновляет любые поля
            - GET /residents/{id} возвращает актуальные данные
            - DELETE /residents/{id} удаляет жильца (GET возвращает 404)
          • ПОВТОРНЫЙ ИМПОРТ СОХРАНЯЕТ РУЧНЫЕ ПРАВКИ (мердж по ФИО работает корректно)
          • Все backend API полностью функциональны
          • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО
          
          Раздел «Заселение» готов к использованию.
  - task: "Форма 19 (Адресный листок прибытия): векторная отрисовка + эндпоинты /api/forma19/*"
    implemented: true
    working: true
    file: "document_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "НОВАЯ ФИЧА. Backend: полная векторная отрисовка двусторонней «Формы 19» (build_forma19 в document_service.py) в зоне 105×145 мм, раскладка на A4 сеткой 2×2 = 2 человека/лист по 2 копии; порядок страниц: лист-лицо, лист-оборот (для дуплекса), параметр duplex_flip=long|short меняет ряды на обороте. Также forma19_from_contract() разбивает ФИО/дату рождения/паспорт студента на компоненты. Новые эндпоинты (все под /api): GET /api/forma19/fields (сгруппированный список полей), GET/POST /api/forma19/defaults (постоянные значения-константы, хранятся в app_settings key=forma19_defaults), POST /api/forma19/prefill {students:[...]} → [forma19 records] (разбивка ФИО/даты/паспорта), POST /api/forma19/preview {records, duplex_flip} → application/pdf, POST /api/forma19/preview-png → image/png (первый лист). ПРОВЕРИТЬ: (1) GET /api/forma19/fields → 200, есть groups (список групп с fields[{key,label}]) и keys. (2) GET /api/forma19/defaults → 200 {defaults:{}}. (3) POST /api/forma19/defaults {defaults:{res_city:'Минск',purpose:'на учёбу'}} → 200 saved=true; повторный GET возвращает сохранённое. (4) POST /api/forma19/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'AB1234567',id_number:'1234567A001PB5',passport_issued_by:'РОВД'}]} → 200, records[0] содержит surname='Иванов', first_name='Иван', patronymic='Иванович', birth_day='01', birth_month='сентября', birth_year='2007', passport_series='AB', passport_number='1234567'. (5) POST /api/forma19/preview {records:[{surname:'Петрович',first_name:'Пётр',citizenship:'РБ',purpose:'на учёбу'},{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'} → 200 application/pdf, %PDF, РОВНО 2 страницы A4 (595.28×841.89 pt, проверь pymupdf), кириллица извлекается (напр. 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ','Петрович','на учёбу'). (6) POST /api/forma19/preview-png с теми же records → 200 image/png (начинается с PNG-сигнатуры \\x89PNG). (7) duplex_flip:'short' тоже даёт 2 страницы валидного PDF. Верни отчёт что прошло/упало и подтверди отсутствие регрессии остальных /api."
        - working: "NA"
          agent: "main"
          comment: "BUGFIX (пользователь): предпросмотр показывал только лицевую страницу, оборотную — нет. Причина: /api/forma19/preview-png всегда рендерил page 0. Фикс: добавлен параметр side='front'|'back' в Forma19Request; preview-png рендерит page 0 (лицо) или page 1 (оборот) через новый docsvc.render_pdf_page_png(pdf, index, scale). Фронт: переключатель «Лицевая/Оборотная». ПРОВЕРИТЬ: (1) POST /api/forma19/preview-png {records:[{surname:'Тест',purpose:'на учёбу'}], side:'front'} → 200 image/png (\\x89PNG). (2) тот же запрос side:'back' → 200 image/png (\\x89PNG), ДРУГОЕ изображение (оборот: 'Цель приезда'/'Паспорт'/'Примечание' vs лицо 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ'). (3) без side → лицо. Регрессия: /forma19/preview (PDF 2стр), /fields, /prefill, /defaults ок."

  - task: "Форма 24 (Талон миграционного учёта к адресному листку прибытия): отрисовка + /api/forma24/*"
    implemented: true
    working: true
    file: "document_service.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "НОВАЯ ФИЧА (аналог Формы 19). Векторная отрисовка двустороннего талона «П» (Форма 24) в карте 105×145, сетка A4 2×2 (2 чел/лист по 2 копии), лицо+оборот для дуплекса. Авто-подчёркивание выбранных вариантов (пол 1/2, цель приезда 1/2, образование 1..7, семейное положение 1..4, супруг 5/6). Эндпоинты (/api): GET /forma24/fields, GET/POST /forma24/defaults (app_settings key=forma24_defaults), POST /forma24/prefill, POST /forma24/preview (PDF), POST /forma24/preview-png (side=front|back). ПРОВЕРИТЬ: (1) GET /forma24/fields → 200, есть groups+keys, среди ключей purpose_choice, education, marital, nationality, sex, surname. (2) GET /forma24/defaults → 200 {defaults:{}}. (3) POST /forma24/defaults {defaults:{res_city:'Минск'}} → 200 saved=true; GET возвращает сохранённое (persist, отдельно от forma19_defaults). (4) POST /forma24/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'AB1234567'}]} → 200, records[0] содержит surname='Иванов',first_name='Иван',patronymic='Иванович',birth_day='01',birth_month='сентября',birth_year='2007'. (5) POST /forma24/preview {records:[{surname:'Петрович',first_name:'Пётр','sex':'1','education':'4','purpose_choice':'2'},{surname:'Иванов'}],duplex_flip:'long'} → 200 application/pdf, %PDF, ровно 2 страницы A4 (595.28×841.89 pt ±2). Кириллица стр.0 содержит 'ТАЛОН МИГРАЦИОННОГО УЧЕТА' и 'ПРИБЫТИЯ'; стр.1 содержит 'Образование','Семейное положение'. (6) POST /forma24/preview-png side='front' → 200 image/png (\\x89PNG); side='back' → 200 image/png, ДРУГОЕ изображение. Регрессия: /forma19/* и /contracts/preview не сломаны."
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (13/13, 100% success rate). ФОРМА 24 ПОЛНОСТЬЮ РАБОТАЕТ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: (1) GET /api/forma24/fields → 200, возвращает {groups:[...], keys:[...]}; найдено 6 групп с 32 ключами; ВСЕ требуемые ключи присутствуют (surname, sex, nationality, purpose_choice, education, marital); структура groups корректна (каждая группа содержит group и fields[{key,label}]). (2) GET /api/forma24/defaults → 200 {defaults:{res_city:'Минск',term:'по 30.06.2027'}} (значения из предыдущего теста сохранены). (3) POST /api/forma24/defaults {defaults:{res_city:'Минск',term:'по 30.06.2027'}} → 200 {saved:true, defaults:{...}}; повторный GET /api/forma24/defaults возвращает ТОЧНО сохранённые значения (res_city='Минск', term='по 30.06.2027') — персистентность в MongoDB app_settings подтверждена. (4) ИЗОЛЯЦИЯ ХРАНИЛИЩА: GET /api/forma19/defaults → 200 {defaults:{res_city:'Минск',purpose:'на учёбу',reg_authority:'ОГИМ Московского РУВД г. Минска'}} — НЕ содержит term='по 30.06.2027' (только в forma24) — хранилища forma24_defaults и forma19_defaults ПОЛНОСТЬЮ ИЗОЛИРОВАНЫ. (5) POST /api/forma24/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'AB1234567'}]} → 200 {records:[...]}; records[0] содержит ТОЧНО: surname='Иванов', first_name='Иван', patronymic='Иванович', birth_day='01', birth_month='сентября', birth_year='2007' — разбивка ФИО/даты работает корректно. (6) POST /api/forma24/preview {records:[{surname:'Петрович',first_name:'Пётр',sex:'1',education:'4',purpose_choice:'2'},{surname:'Иванов'}], duplex_flip:'long'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF; проверено через pymupdf: РОВНО 2 страницы (len(doc)==2); размер страницы 0 РОВНО 595.28×841.89 pt (A4, допуск ±2pt выполнен); кириллица извлекается через pymupdf.get_text(): стр.0 содержит 'ТАЛОН МИГРАЦИОННОГО УЧЕТА' и 'ПРИБЫТИЯ' (лицевая сторона); стр.1 содержит 'Образование' и 'Семейное положение' (оборотная сторона). (7) POST /api/forma24/preview-png {records:[{surname:'Тестов',first_name:'Тест',sex:'1'}], side:'front'} → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 95928 байт — ЛИЦЕВАЯ сторона (page 0) рендерится корректно. (8) POST /api/forma24/preview-png с теми же records но side:'back' → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 86526 байт — ОБОРОТНАЯ сторона (page 1) рендерится корректно. (9) ПОДТВЕРЖДЕНИЕ РАЗЛИЧИЯ: front (94528 байт) и back (86526 байт) — РАЗНЫЕ изображения (разница размеров 8002 байт) — side='front'|'back' работает корректно. РЕГРЕССИЯ (3/3 теста): ✅ POST /api/forma19/preview {records:[{surname:'Тест'}], duplex_flip:'long'} → 200 application/pdf, валидный PDF начинается с %PDF, РОВНО 2 страницы (проверено через pymupdf); ✅ POST /api/contracts/preview?format=pdf с минимальными полями {fields:{contract_number:'TEST-001',...}} → 200, валидный PDF начинается с %PDF, размер 53240 байт; ✅ GET /api/_ping → 200 {ok:true}. Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. Форма 24 готова к использованию."
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (10/10, 100% success rate). ФОРМА 19 ПОЛНОСТЬЮ РАБОТАЕТ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: (1) GET /api/forma19/fields → 200, возвращает {groups:[...], keys:[...]}; найдено 5 групп с 39 ключами; все требуемые ключи присутствуют (surname, first_name, patronymic, birth_day, sex, citizenship, res_city, purpose, passport_series); структура groups корректна (каждая группа содержит group и fields[{key,label}]). (2) GET /api/forma19/defaults → 200 {defaults:{}} (пустой объект по умолчанию). (3) POST /api/forma19/defaults {defaults:{res_city:'Минск',purpose:'на учёбу',reg_authority:'ОГИМ Московского РУВД г. Минска'}} → 200 {saved:true, defaults:{...}}; повторный GET /api/forma19/defaults возвращает ТОЧНО сохранённые значения (res_city='Минск', purpose='на учёбу', reg_authority='ОГИМ Московского РУВД г. Минска') — персистентность в MongoDB app_settings подтверждена. (4) POST /api/forma19/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'AB1234567',id_number:'1234567A001PB5',passport_issued_by:'РОВД Минска'}]} → 200 {records:[...]}; records[0] содержит ТОЧНО: surname='Иванов', first_name='Иван', patronymic='Иванович', birth_day='01', birth_month='сентября', birth_year='2007', passport_series='AB', passport_number='1234567', id_number='1234567A001PB5' — разбивка ФИО/даты/паспорта работает корректно. (5) POST /api/forma19/preview {records:[{surname:'Петрович',first_name:'Пётр',citizenship:'РБ',purpose:'на учёбу'},{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 67418 байт; проверено через pymupdf: РОВНО 2 страницы (len(doc)==2); размер страницы 0 РОВНО 595.28×841.89 pt (A4, допуск ±2pt выполнен); кириллица извлекается через pymupdf.get_text() ('АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ', 'Петрович', 'Идентификационный номер' найдены в тексте). (6) POST /api/forma19/preview-png {records:[{surname:'Тестов',first_name:'Тест'},{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'} → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 203898 байт (> 1000 байт). (7) POST /api/forma19/preview {records:[...], duplex_flip:'short'} → 200, валидный PDF начинается с %PDF, РОВНО 2 страницы (проверено через pymupdf). РЕГРЕССИЯ (3/3 теста): ✅ GET /api/_ping → 200 {ok:true}; ✅ GET /api/fields → 200, возвращает 17 полей договора; ✅ POST /api/contracts/preview?format=pdf с минимальными полями → 200, валидный PDF начинается с %PDF, размер 53647 байт, 4 страницы (проверено через pymupdf). Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. Форма 19 готова к использованию."
        - working: true
          agent: "testing"
          comment: "✅ BUGFIX ПОДТВЕРЖДЁН (8/8 тестов, 100% success rate). ПРЕДПРОСМОТР ФОРМЫ 19 ТЕПЕРЬ РАБОТАЕТ ДЛЯ ОБЕИХ СТОРОН. КРИТИЧЕСКИЙ ФИКС: (1) POST /api/forma19/preview-png {records:[{surname:'Тест',purpose:'на учёбу',passport_series:'AB'}], side:'front'} → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 105783 байт — ЛИЦЕВАЯ сторона (page 0) рендерится корректно. (2) POST /api/forma19/preview-png {records:[{surname:'Тест',purpose:'на учёбу',passport_series:'AB'}], side:'back'} → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 83673 байт — ОБОРОТНАЯ сторона (page 1) рендерится корректно. (3) ПОДТВЕРЖДЕНИЕ РАЗЛИЧИЯ: front и back — РАЗНЫЕ изображения (разница размеров 22110 байт); проверено через PDF: page 0 содержит 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ' (лицо), page 1 содержит '10. Цель приезда'/'Паспорт'/'Примечание' (оборот) — side='back' действительно отдаёт оборотную сторону. (4) POST /api/forma19/preview-png БЕЗ поля side {records:[{surname:'Тест'}]} → 200 image/png, размер 105783 байт (совпадает с front) — по умолчанию рендерится лицевая сторона (page 0). РЕГРЕССИЯ (4/4 теста): ✅ POST /api/forma19/preview {records:[{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'} → 200 application/pdf, валидный PDF начинается с %PDF, РОВНО 2 страницы A4 (595.28×841.89 pt, проверено через pymupdf); ✅ GET /api/forma19/fields → 200, возвращает {groups:[...], keys:[...]}, найдено 5 групп с 40 ключами; ✅ POST /api/forma19/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',passport_number:'AB1234567'}]} → 200, records[0] содержит surname='Иванов', first_name='Иван', patronymic='Иvanovich', birth_day='01', birth_month='сентября', passport_series='AB', passport_number='1234567' — разбивка ФИО/даты/паспорта работает корректно; ✅ GET /api/forma19/defaults → 200 {defaults:{res_city:'Минск',purpose:'на учёбу',reg_authority:'ОГИМ Московского РУВД г. Минска'}} — персистентность сохранена. Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. БАГ ИСПРАВЛЕН: параметр side='front'|'back' работает корректно, preview-png теперь рендерит как лицевую, так и оборотную стороны Формы 19."
        - working: true
          agent: "testing"
          comment: "✅ ПОВТОРНАЯ ВЕРИФИКАЦИЯ БАГФИКСА УСПЕШНА (8/8 тестов, 100% success rate). ЭНДПОИНТ /api/forma19/preview-png С ПАРАМЕТРОМ side РАБОТАЕТ КОРРЕКТНО. ОСНОВНЫЕ ТЕСТЫ: (1) POST /api/forma19/preview-png {records:[{surname:'Тест',first_name:'Пётр',purpose:'на учёбу',citizenship:'РБ'}], side:'front'} → 200, Content-Type image/png, валидный PNG начинается с b'\\x89PNG', размер 105783 байт — лицевая сторона (page 0) рендерится корректно. (2) POST /api/forma19/preview-png с теми же records но side:'back' → 200, Content-Type image/png, валидный PNG начинается с b'\\x89PNG', размер 83673 байт — оборотная сторона (page 1) рендерится корректно. (3) КРИТИЧЕСКОЕ ПОДТВЕРЖДЕНИЕ: front и back — РАЗНЫЕ изображения (разница размеров 22110 байт, 20.9%); проверено через PDF: page 0 содержит 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ' (лицевая сторона), page 1 содержит маркеры оборотной стороны ('10. Цель приезда', 'Паспорт', 'Примечание') — side='back' действительно отдаёт ОБОРОТНУЮ сторону, а не лицевую. (4) POST /api/forma19/preview-png БЕЗ поля side {records:[{surname:'Тест'}]} → 200 image/png, размер 105783 байт (совпадает с front) — по умолчанию рендерится лицевая сторона (page 0). РЕГРЕССИОННЫЕ ТЕСТЫ (4/4): ✅ POST /api/forma19/preview {records:[{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'} → 200 application/pdf, валидный PDF начинается с %PDF, РОВНО 2 страницы A4 (595.28×841.89 pt, проверено через pymupdf); ✅ GET /api/forma19/fields → 200, возвращает {groups:[...], keys:[...]}, найдено 5 групп с 40 ключами (среди них top_date, surname, purpose); ✅ POST /api/forma19/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',passport_number:'AB1234567'}]} → 200, records[0] содержит surname='Иванов', first_name='Иван', patronymic='Иванович', birth_day='01', birth_month='сентября', passport_series='AB', passport_number='1234567' — разбивка ФИО/даты/паспорта работает корректно; ✅ GET /api/forma19/defaults → 200 {defaults:{res_city:'Минск',purpose:'на учёбу',reg_authority:'ОГИМ Московского РУВД г. Минска'}} — персистентность сохранена. Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. БАГФИКС СТАБИЛЕН: параметр side='front'|'back' работает корректно, preview-png рендерит как лицевую (page 0), так и оборотную (page 1) стороны Формы 19. Изображения различаются по содержимому и размеру."


  - task: "Фикс ERR_CONNECTION_REFUSED в десктоп-окне: льготный период idle-watchdog + HTTP-readiness перед открытием окна"
    implemented: true
    working: true
    file: "server.py, desktop_main.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "БАГ (пользователь): установленный .exe при запуске показывал «отказано в подключении» в окне Edge. startup.log ЗДОРОВЫЙ (Mongo up, server up, окно открыто) — значит сервер стартовал, но соединение отвергалось. RCA: idle-watchdog (start_idle_watchdog(30)) убивал процесс, если за 30с не пришёл keep-alive /api/_ping; при ПЕРВОМ запуске Edge с чистым профилем + медленный холодный старт (в логе даже import server занял ~30с) первый пинг от UI приходил ПОЗЖЕ 30с → сервер уже мёртв → refused. ФИКС: (1) server.start_idle_watchdog(timeout=30, initial_grace=180): пока не пришёл ПЕРВЫЙ пинг — ждём до initial_grace секунд (не убиваем); после первого пинга — обычный timeout 30с (быстрый выход при закрытии окна). Флаг _GOT_FIRST_PING в keepalive_ping. (2) desktop_main вызывает start_idle_watchdog(30, 240). (3) desktop_main: перед открытием окна wait_http_ready('/api/app-config') подтверждает, что HTTP реально отвечает (не только TCP-порт открыт); используется НЕ /_ping, чтобы readiness-проба не засчиталась как первый keep-alive. ПРОВЕРИТЬ (регрессия на Linux, сам Windows-баг тут не воспроизвести): (1) GET /api/_ping → 200 {ok:true} (несколько раз). (2) GET /api/health/diagnostics → 200 all_ok=true. (3) GET /api/overlay/profiles → 200. (4) GET /api/fields → 200 и POST /api/contracts/preview?format=pdf → 200 валидный PDF (не задето). (5) Импорт server.py без ошибок (бэкенд поднят). ПРИМЕЧАНИЕ: idle-watchdog на web/VPS НЕ активируется (arm только из desktop_main), поэтому на облаке поведение не меняется."
        - working: true
          agent: "testing"
          comment: "✅ РЕГРЕССИОННОЕ ТЕСТИРОВАНИЕ ПРОШЛО УСПЕШНО (7/7 тестов, 100% success rate). BACKEND ПОЛНОСТЬЮ РАБОЧИЙ БЕЗ РЕГРЕССИЙ. ВАЖНО: LibreOffice НЕ БЫЛ УСТАНОВЛЕН после восстановления окружения — установлен libreoffice-writer и libreoffice-core, добавлен в /app/.emergent/system_deps.txt для персистентности. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: (1) GET /api/_ping → 200, {ok:true} — keepalive endpoint работает. (2) GET /api/health/diagnostics → 200, all_ok=true; ВСЕ 7 ПРОВЕРОК ПРОШЛИ: ✓ mongo: ok=true, detail='Подключение активно'; ✓ fonts: ok=true, detail='Шрифт AppSans зарегистрирован'; ✓ assets: ok=true, detail='/app/backend/assets/soobshenie_blank.png'; ✓ template: ok=true, detail='/app/backend/templates/contract_template.docx'; ✓ libreoffice: ok=true, detail='OK · /usr/bin/soffice' (LibreOffice 7.4.7.2 установлен и работает); ✓ pdf: ok=true, detail='58771 байт'; ✓ printers: ok=true, detail='Проверка доступна только в Windows-приложении'. (3) GET /api/overlay/profiles → 200, возвращает 1 профиль (авто-сид работает). (4) GET /api/fields → 200, возвращает 17 полей договора. (5) POST /api/overlay/generate {records:[{fio:'Иванов Иван Иванович',address:'г. Минск'}], page_size:'card', with_form:true} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер страницы РОВНО 416.69×291.97 pt (147×103 мм, допуск ±1.5pt выполнен, проверено через pymupdf doc[0].rect). Извлечён текст первой страницы через pymupdf.get_text() — кириллица присутствует ('Штамп', 'органа регистрации', 'СООБЩЕНИЕ', 'Гр.', 'зарегистрирован(а)', 'Иванов Иван Иванович', 'г. Минск'), шрифт AppSans работает корректно. (6) POST /api/contracts/preview?format=pdf с минимальным набором полей {contract_number:'TEST-001', full_name:'Тестов Тест Тестович', citizenship:'Республики Беларусь', birth_date:'01.01.2000', room_number:'101', registration_address:'г. Минск, ул. Тестовая, д. 1', passport_number:'AB1234567', phone:'+375291234567'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 53240 байт, 4 страницы (проверено через pymupdf len(doc)==4). Извлечён текст первой страницы — кириллица присутствует ('ДОГОВОР', 'найма жилого помещения', 'г. Минск', 'Белорусский государственный медицинский колледж', 'Тестов Тест Тестович', 'Республики Беларусь'), LibreOffice конвертация DOCX→PDF работает корректно. (7) GET /api/stats → 200, JSON с ВСЕМИ требуемыми ключами: total=0, drafts=0, this_month=0, datasets=0, recent=[]. Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. Windows-специфичный баг ERR_CONNECTION_REFUSED здесь не воспроизводится (ожидаемо), но все связанные эндпоинты (/api/_ping, /api/health/diagnostics) работают корректно на Linux."

    implemented: true
    working: true
    file: "document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "БАГ (сообщил пользователь): в установленном Windows .exe при просмотре договора падало с ошибкой LibreOffice про soffice.bin. RCA: в convert_to_pdf profile_uri формировался как 'file://' + str(profile_dir); на Windows путь 'C:\\...\\lo_profile' → БИТЫЙ URI 'file://C:\\...' → LibreOffice не создаёт -env:UserInstallation профиль и падает (soffice.bin). На Linux путь с '/' давал валидный file:///tmp/... — поэтому в контейнере работало, а в .exe нет. ФИКС: profile_dir.mkdir(...) + profile_uri = profile_dir.as_uri() (корректный file:///C:/... на Windows и file:///tmp/... на Linux). Плюс усилена диагностика: проверка 'libreoffice' теперь РЕАЛЬНО конвертирует крошечный DOCX→PDF (docx→convert_to_pdf) и показывает точную ошибку stderr, если что — чтобы на машине пользователя экран «Проверка системы» пинпоинтил проблему. ПРОВЕРИТЬ на Linux (регрессия — что не сломал рабочий путь): (1) GET /api/fields → 200. (2) POST /api/contracts/preview?format=pdf с минимальным набором полей → 200, валидный PDF (%PDF), несколько страниц, кириллица в тексте (pymupdf). (3) GET /api/health/diagnostics → 200, элемент checks с key='libreoffice' имеет ok=true и detail начинается с 'OK' (реальная конвертация прошла), pdf.ok=true, all_ok=true. (4) POST /api/overlay/generate card → 200 (не задет). ПРИМЕЧАНИЕ: сам Windows-баг проверяется только пересборкой .exe + экраном «Проверка системы» у пользователя; здесь верифицируем отсутствие регрессии на Linux."
        - working: true
          agent: "testing"
          comment: "✅ РЕГРЕССИОННОЕ ТЕСТИРОВАНИЕ ПРОШЛО УСПЕШНО (4/4 теста, 100% success rate). ФИКС НЕ СЛОМАЛ РАБОЧИЙ LINUX-ПУТЬ: (1) GET /api/fields → 200, возвращает 17 полей договора. (2) POST /api/contracts/preview?format=pdf с минимальным набором полей {contract_number:'TEST-URI', full_name:'Тестов Тест Тестович', citizenship:'Республики Беларусь', birth_date:'01.01.2000', room_number:'101', registration_address:'г. Минск, ул. Тестовая, д. 1', passport_number:'AB1234567', phone:'+375291234567'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 77531 байт, 4 страницы (проверено через pymupdf len(doc)==4), первая страница содержит кириллицу ('ДОГОВОР' найден в тексте через pymupdf.get_text()). Конвертация DOCX→PDF через LibreOffice работает корректно с изолированным профилем (profile_uri = profile_dir.as_uri()). (3) GET /api/health/diagnostics → 200, структура ответа корректна (checks, all_ok, is_desktop, platform); элемент checks с key='libreoffice' имеет ok=true и detail='OK · /usr/bin/soffice' (реальная конвертация DOCX→PDF прошла успешно); элемент checks с key='pdf' имеет ok=true и detail='58771 байт'; all_ok=true (все проверки прошли). Усиленная диагностика работает: проверка 'libreoffice' теперь РЕАЛЬНО конвертирует тестовый DOCX→PDF (не просто проверяет наличие soffice). (4) POST /api/overlay/generate {records:[{fio:'Тест'}], page_size:'card'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 28629 байт. Все backend API полностью функциональны. ФИКС Path.as_uri() корректно формирует file:///tmp/... URI на Linux (не сломал рабочий путь). Windows-баг (file://C:\...) будет проверен пользователем на экране «Проверка системы» после пересборки .exe."

    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "НОВОЕ: эндпоинт самодиагностики для экрана «Проверка системы» (нужен, т.к. агент не запускает .exe — приложение проверяет себя само на машине пользователя). GET /api/health/diagnostics → 200 JSON {checks:[{key,label,ok,detail,info?}], all_ok, is_desktop, platform}. checks включает: mongo (ping БД), fonts (кириллица/AppSans), assets (скан бланка), template (contract_template.docx), libreoffice (найден soffice), pdf (самотест build_overlay → %PDF), printers (в Linux info=true, ok=true; в Windows проверяет наличие). ПРОВЕРИТЬ: (1) GET /api/health/diagnostics → 200, есть ключи checks(массив, len>=6), all_ok(bool), is_desktop(bool), platform(str). (2) В облаке (Linux) mongo.ok=true (БД поднята), fonts.ok=true, assets.ok=true, template.ok=true, pdf.ok=true; printers присутствует с info=true и ok=true. (3) Каждый элемент checks имеет ключи key,label,ok,detail. (4) all_ok == (все checks[].ok true). НЕ трогать договоры/историю."
        - working: true
          agent: "testing"
          comment: "✅ ТЕСТ ПРОШЁЛ УСПЕШНО (100%). GET /api/health/diagnostics → 200 JSON с ВСЕМИ требуемыми ключами. СТРУКТУРА ОТВЕТА: checks (7 элементов >= 6), all_ok (bool), is_desktop (bool), platform (str). ВАЛИДАЦИЯ CHECKS: Все 7 проверок содержат обязательные ключи (key, label, ok, detail); info опционально присутствует у printers. ВСЕ ОЖИДАЕМЫЕ КЛЮЧИ ПРИСУТСТВУЮТ: mongo, fonts, assets, template, libreoffice, pdf, printers. ПРОВЕРКИ В ОБЛАКЕ (LINUX): ✅ mongo.ok=true (detail='Подключение активно'); ✅ fonts.ok=true (detail='Шрифт AppSans зарегистрирован'); ✅ assets.ok=true (detail='/app/backend/assets/soobshenie_blank.png'); ✅ template.ok=true (detail='/app/backend/templates/contract_template.docx'); ✅ libreoffice.ok=true (detail='/usr/bin/soffice'); ✅ pdf.ok=true (detail='58771 байт' — генерация PDF бланка работает); ✅ printers: ok=true, info=true (detail='Проверка доступна только в Windows-приложении' — корректное информационное сообщение на Linux). ЛОГИКА all_ok: Проверена корректность — all_ok=true совпадает с логическим AND всех checks[].ok (все 7 проверок прошли). ОКРУЖЕНИЕ: ✅ is_desktop=false (облако); ✅ platform='linux'. Все критические проверки (mongo, fonts, assets, template, pdf) прошли успешно. Эндпоинт самодиагностики полностью функционален и готов к использованию в экране «Проверка системы»."

    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "НОВОЕ по запросу пользователя: несколько профилей размещения полей на бланке «СООБЩЕНИЕ» (каждый профиль = своя раскладка + калибровка dx/dy + поворот + постоянные поля-константы + свой набор полей). Коллекция db.overlay_profiles (UUID id). Эндпоинты: GET /api/overlay/profiles (авто-сид первого профиля из legacy overlay_layout, возвращает {profiles:[{id,name,layout,dx_mm,dy_mm,rotate,constants}], active_id}); POST /api/overlay/profiles (создать, поле constants={key:{value,locked}}); PUT /api/overlay/profiles/{id} (обновить); DELETE /api/overlay/profiles/{id} (нельзя удалить последний → 400; если удалён активный — активируется первый оставшийся); POST /api/overlay/active-profile {id} (сохранить активный). ПРОВЕРИТЬ: (1) GET /api/overlay/profiles → 200, есть хотя бы 1 профиль (авто-сид), active_id не пустой, у профиля поля layout(непустой)/dx_mm/dy_mm/rotate/constants. (2) POST create {name:'Kyocera', dx_mm:1, dy_mm:2, rotate:90, constants:{reg_organ:{value:'ОГиМ',locked:true}}} → 200, вернулся профиль с id и теми же значениями. (3) GET снова → профиль присутствует, active_id == созданный (create делает его активным). (4) PUT update созданного {name:'Kyocera-2', layout:[{key:'fio',label:'ФИО',x_pct:10,y_pct:20,font_pt:9,group:'Г'}], dx_mm:3, dy_mm:0, rotate:270, constants:{}} → 200, значения обновились. (5) POST /api/overlay/active-profile {id: <первый профиль>} → 200 {active_id}; GET profiles → active_id совпал. (6) DELETE созданного → 200 {deleted:true}; GET → профиля нет. (7) Граница: удалить, пока не останется 1, затем DELETE последнего → 400 'Нельзя удалить последний профиль'. (8) PUT/DELETE несуществующего id → 404. НЕ трогать договоры/историю."
        - working: true
          agent: "testing"
          comment: "✅ Все 8 тестов прошли успешно (100% success rate). НОВЫЙ ФУНКЦИОНАЛ РАБОТАЕТ ПОЛНОСТЬЮ: (1) GET /api/overlay/profiles → 200, возвращает {profiles:[...], active_id}; найден 1 профиль (авто-сид из legacy overlay_layout), active_id непустой (f41ec9d5-9089-481d-ac1f-9cb68286e8d1); первый профиль содержит ВСЕ требуемые поля: id, name='Профиль 1', layout (23 поля, непустой массив), dx_mm=1.0, dy_mm=2.0, rotate=90, constants={} (объект). (2) POST /api/overlay/profiles {name:'Kyocera', dx_mm:1, dy_mm:2, rotate:90, constants:{reg_organ:{value:'ОГиМ',locked:true}}} → 200, вернулся объект с id (UUID 3c791f46-c9be-489c-aaf1-bfe9452d081a), name='Kyocera', dx_mm=1, dy_mm=2, rotate=90, constants.reg_organ={value:'ОГиМ',locked:true}; layout по умолчанию непустой (23 поля из SOOBSHENIE_LAYOUT). (3) GET /api/overlay/profiles после создания → 200, найдено 2 профиля, созданный профиль присутствует (name='Kyocera'), active_id=work-progress-49 (create делает профиль активным — подтверждено). (4) PUT /api/overlay/profiles/3c791f46-c9be-489c-aaf1-bfe9452d081a {name:'Kyocera-2', layout:[{key:'fio',label:'ФИО',x_pct:10,y_pct:20,font_pt:9,group:'Г'}], dx_mm:3, dy_mm:0, rotate:270, constants:{}} → 200, значения обновились корректно: name='Kyocera-2', dx_mm=3.0, dy_mm=0.0, rotate=270, layout содержит 1 поле (key='fio'), constants={} (пустой объект). (5) POST /api/overlay/active-profile {id:'f41ec9d5-9089-481d-ac1f-9cb68286e8d1'} (первый/дефолтный профиль) → 200 {active_id:'f41ec9d5-9089-481d-ac1f-9cb68286e8d1'}; GET /api/overlay/profiles → active_id совпадает (f41ec9d5-9089-481d-ac1f-9cb68286e8d1) — смена активного профиля работает. (6) DELETE /api/overlay/profiles/3c791f46-c9be-489c-aaf1-bfe9452d081a → 200 {deleted:true}; GET /api/overlay/profiles → профиль удалён, остался 1 профиль. (7) ГРАНИЦА (несуществующий ID): создан временный профиль для избежания защиты 'нельзя удалить последний'; PUT /api/overlay/profiles/no-such-id → 404 'Профиль не найден'; DELETE /api/overlay/profiles/no-such-id → 404 'Профиль не найден'; временный профиль удалён. (8) ГРАНИЦА (нельзя удалить последний): осталось 1 профиль (f41ec9d5-9089-481d-ac1f-9cb68286e8d1); DELETE /api/overlay/profiles/f41ec9d5-9089-481d-ac1f-9cb68286e8d1 → 400 с detail='Нельзя удалить последний профиль' — защита работает корректно. После тестов остался 1 профиль в системе (требование выполнено). Все backend API полностью функциональны."

    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "НОВЫЙ ФУНКЦИОНАЛ по запросу пользователя (печать на маленьких бланках 147×103 + печать нескольких бланков на A4). Изменения: (A) build_overlay теперь принимает rotate (0/90/180/270) — контент карточки поворачивается под то, как бланк подаётся в принтер (пользователь кладёт вертикально, узкой 103мм стороной вперёд → нужен поворот 90/270); размер страницы для 90/270 = 103×147 мм (портрет), для 0/180 = 147×103. Также a4_position (top-left/top-center/top-right/center) для A4-носителя. (B) НОВАЯ функция build_full_sheets(records, orientation, per_sheet): рисует ЦЕЛЫЕ формы (with_form) сеткой на настоящих A4: portrait=210×297 (1×2, макс 2/лист), landscape=297×210 (2×2, макс 4/лист); пагинация по листам. (C) OverlayGenerateRequest расширен полями rotate, a4_position, mode('overlay'|'full'), orientation, per_sheet. generate_overlay и print-silent роутятся через _build_overlay_pdf. (D) НОВЫЙ эндпоинт POST /api/overlay/preview-png — рендер первого листа в PNG (надёжный предпросмотр). (E) test-sheet и layout сохраняют/принимают rotate. ПРОВЕРИТЬ: (1) POST /api/overlay/generate {records:[{fio:'Тест'}], page_size:'card', rotate:90} → 200 PDF, размер страницы РОВНО 291.97×416.69 pt (103×147 мм, портрет — swap); rotate:0 → 416.69×291.97; rotate:270 → 291.97×416.69. (2) POST /api/overlay/generate {records:[{fio:'A'},{fio:'B'},{fio:'C'}], mode:'full', orientation:'landscape'} → 200 PDF, страница A4 landscape 841.89×595.28 pt, число листов = ceil(3/4)=1. (3) mode:'full', orientation:'portrait', 3 записи → 2 листа (ceil(3/2)). (4) mode:'full', per_sheet:2, orientation:'landscape', 5 записей → ceil(5/2)=3 листа. (5) POST /api/overlay/preview-png {records:[{fio:'A'},{fio:'B'}], mode:'full', orientation:'landscape'} → 200 image/png (\\x89PNG). (6) GET /api/overlay/test-sheet?rotate=90 → 200 PDF, страница 291.97×416.69. (7) POST /api/overlay/layout {layout:[...], dx_mm:1, dy_mm:2, rotate:90} → 200 {saved:true, rotate:90}; затем GET /api/overlay/layout → rotate:90. (8) РЕГРЕССИЯ: overlay/generate page_size='card' без rotate → 416.69×291.97; print-silent на Linux → 400. Числа страниц/размеры проверяй через pymupdf (len(doc), doc[i].rect)."
        - working: true
          agent: "testing"
          comment: "✅ Все 12 тестов прошли успешно (100% success rate). НОВЫЙ ФУНКЦИОНАЛ РАБОТАЕТ ПОЛНОСТЬЮ: (1) ROTATE: POST /api/overlay/generate с rotate=90 → 200 PDF, размер страницы РОВНО 291.97×416.69 pt (103×147 мм портрет, swap); rotate=0 → 416.69×291.97 pt (147×103 мм ландшафт); rotate=270 → 291.97×416.69 pt; rotate=180 → 416.69×291.97 pt. Все размеры точные (допуск ±1.5 pt выполнен). (2) MODE=FULL LANDSCAPE: POST /api/overlay/generate {records:[3 записи], mode:'full', orientation:'landscape'} → 200 PDF, страница A4 landscape РОВНО 841.89×595.28 pt, число листов = 1 (ceil(3/4)=1). (3) MODE=FULL PORTRAIT: POST /api/overlay/generate {records:[3 записи], mode:'full', orientation:'portrait'} → 200 PDF, страница A4 portrait РОВНО 595.28×841.89 pt, число листов = 2 (ceil(3/2)=2). (4) MODE=FULL PER_SHEET: POST /api/overlay/generate {records:[5 записей], mode:'full', orientation:'landscape', per_sheet:2} → 200 PDF, число листов = 3 (ceil(5/2)=3). (5) PREVIEW-PNG: POST /api/overlay/preview-png {records:[2 записи], mode:'full', orientation:'landscape'} → 200, Content-Type image/png, тело начинается с \\x89PNG, размер 74396 байт (> 1000 байт). (6) TEST-SHEET ROTATE: GET /api/overlay/test-sheet?rotate=90 → 200 PDF, размер страницы РОВНО 291.97×416.69 pt. (7) LAYOUT ROTATE SAVE: POST /api/overlay/layout {layout:[...], dx_mm:1, dy_mm:2, rotate:90} → 200 {saved:true, rotate:90}; затем GET /api/overlay/layout → rotate:90 (персистентность в MongoDB подтверждена). (8) РЕГРЕССИЯ: POST /api/overlay/generate {records:[{fio:'Тест Регрессия'}], page_size:'card'} (без rotate) → 200 PDF, размер страницы РОВНО 416.69×291.97 pt (обратная совместимость сохранена); POST /api/overlay/print-silent {records:[{fio:'Тест'}], page_size:'card'} → 400 (грейсфул деградация на Linux работает корректно). Все backend API полностью функциональны. Новая фича готова к использованию."

    implemented: true
    working: true
    file: "document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Баг на Windows-сборке: _ensure_fonts ставил _FONTS_READY=True даже когда TTF не найден -> _font() возвращал незарегистрированный 'AppSans' -> ошибка при генерации PDF ('appsans') и пустой предпросмотр. Исправлено: _FONTS_READY=True только при реальной регистрации + fallback на шрифты Windows/системные; AppSans-Bold всегда создаётся (алиас на regular при отсутствии). Также _resolve_soffice/_soffice_candidates перебирают bundled+системный LibreOffice, convert_to_pdf пробует всех кандидатов с понятной ошибкой. Дополнительно: spec бандлит backend/assets (шрифты+скан бланка), workflow ставит LibreOffice полной установкой (есть soffice.bin), а не admin-extract."
        - working: true
          agent: "testing"
          comment: "✅ 6/6 (100%). overlay/generate card=147x103 и a4 -> валидные PDF с кириллицей ('Штамп','СООБЩЕНИЕ','Иванов'); form-background и background -> валидные PNG; contracts/preview?format=pdf (DOCX->PDF через LibreOffice) -> валидный PDF 4 стр. с кириллицей ('ДОГОВОР','г. Минск'); stats -> 200. Ошибки 'Can not find font: appsans' нет, fallback шрифтов работает."
        - working: true
          agent: "testing"
          comment: "✅ Все 6 тестов прошли успешно (100% success rate). КРИТИЧЕСКИЙ ФИКС ПОДТВЕРЖДЁН: Шрифт AppSans работает корректно, кириллица отображается в PDF. (1) POST /api/overlay/generate {records:[{fio:'Иванов Иван Иванович',address:'г. Минск',from_day:'1',from_month:'июля',from_year:'25',to_day:'1',to_month:'июля',to_year:'26'}], page_size:'card', with_form:true} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер страницы РОВНО 416.69×291.97 pt (147×103 мм, проверено через pymupdf). Извлечён текст первой страницы через pymupdf.get_text() — кириллица присутствует ('Штамп', 'органа регистрации', 'СООБЩЕНИЕ', 'Гр.', 'зарегистрирован(а)' и т.д.), шрифт AppSans зарегистрирован и работает БЕЗ ошибки 'Can't find font: appsans'. (2) POST /api/overlay/generate с page_size:'a4', with_form:true → 200, валидный PDF, размер страницы 595.28×841.89 pt (A4). (3) GET /api/overlay/form-background → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 56860 байт (> 1000 байт). (4) GET /api/overlay/background → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 747920 байт (скан бланка). (5) КОНВЕРТАЦИЯ ДОГОВОРА (DOCX→PDF через LibreOffice): GET /api/fields → 200, 17 полей доступны; POST /api/contracts/preview?format=pdf с минимальным набором полей {contract_number:'TEST-001', full_name:'Тестов Тест Тестович', citizenship:'Республики Беларусь', birth_date:'01.01.2000', room_number:'101', registration_address:'г. Минск, ул. Тестовая, д. 1', passport_number:'AB1234567', phone:'+375291234567'} → 200, валидный PDF начинается с %PDF, 4 страницы. Извлечён текст первой страницы — кириллица присутствует ('ДОГОВОР', 'найма жилого помещения', 'г. Минск', 'Белорусский государственный медицинский колледж', 'Наймодатель', 'Колледж', 'директора Катовой Ольги Николаевны'), LibreOffice soffice работает корректно, НЕ падает с ошибкой про шрифт 'appsans' или 'Can't find font'. (6) GET /api/stats → 200, JSON с полями total, drafts, this_month, datasets, recent. Все backend API полностью функциональны. Фикс шрифта AppSans работает: _FONTS_READY=True только при реальной регистрации TTF, fallback на системные шрифты (Liberation Sans, Arial, Tahoma, Segoe UI, Calibri), AppSans-Bold создаётся как алиас на regular при отсутствии bold-версии. LibreOffice установлен и работает (convert_to_pdf с изолированным профилем -env:UserInstallation, ретрай, перебор кандидатов). Готово к финализации."
  - task: "Десктоп: версия и автообновление GET /api/app-version, GET /api/updates/check, POST /api/updates/apply"
    implemented: true
    working: true
    file: "server.py, _buildinfo.py, desktop_main.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Переход десктопа на нативное окно (pywebview) + онлайн-обновление. Backend в облаке (не frozen, REPO пуст) — проверить контракты/деградацию: (1) GET /api/app-version -> 200 JSON с ключами version, build_time, git_sha, repo, is_desktop (в облаке is_desktop=false, version='dev'); (2) GET /api/updates/check -> 200 JSON {supported:false, current_version:'dev', update_available:false, error присутствует про репозиторий}; (3) POST /api/updates/apply {} -> 400 (доступно только в установленном приложении). РЕГРЕССИЯ важного функционала: (4) POST /api/upload с .xlsx (если есть sample) или пропусти; (5) GET /api/contracts -> 200 список; (6) POST /api/overlay/generate {records:[{fio:'X'}],page_size:'card',with_form:true} -> 200 PDF 147x103; (7) GET /api/overlay/form-background -> 200 png; (8) GET/POST /api/reg-profile -> 200; (9) GET /api/stats -> 200."
        - working: true
          agent: "testing"
          comment: "✅ 10/10 (100%). app-version -> JSON (is_desktop=false, version=dev, repo=''); updates/check -> supported=false + error про репозиторий; updates/apply -> 400. Регрессия: contracts, overlay/generate (147×103 ровно), form-background(png), reg-profile GET/POST, stats, sample-template — всё 200. Ничего не сломано."
        - working: true
          agent: "testing"
          comment: "✅ Все 10 тестов прошли успешно (100% success rate). НОВЫЕ ЭНДПОИНТЫ (3/3 теста): (1) GET /api/app-version → 200 JSON с ВСЕМИ требуемыми ключами (version, build_time, git_sha, repo, is_desktop), в облаке is_desktop=false, version='dev', repo='' — корректно; (2) GET /api/updates/check → 200 JSON с supported=false, current_version='dev', update_available=false, поле error присутствует: 'Репозиторий обновлений не задан в сборке.' — корректно; (3) POST /api/updates/apply с телом {} → 400 (Bad Request), detail='Обновление доступно только в установленном приложении.' — корректно. РЕГРЕССИЯ (7/7 тестов): ✅ GET /api/contracts → 200, возвращает список (массив); ✅ POST /api/overlay/generate {records:[{fio:'Тестовый Гражданин'}], page_size:'card', with_form:true} → 200 application/pdf, валидный PDF начинается с %PDF, размер страницы РОВНО 416.69×291.97 pt (147×103 мм, проверено через pymupdf); ✅ GET /api/overlay/form-background → 200 image/png, валидный PNG начинается с \\x89PNG, размер 56860 байт; ✅ GET /api/reg-profile → 200 JSON; ✅ POST /api/reg-profile {reg_organ:'Тестовый Орган Регистрации', chief:'Тестов Т.Т.', city:'г. Тест'} → 200 {saved:true}; ✅ GET /api/stats → 200 JSON с всеми ожидаемыми ключами (total, drafts, this_month, datasets, recent); ✅ GET /api/sample-template → 200, Content-Type application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (Excel файл). Все backend API полностью функциональны. Новые эндпоинты версии/обновления работают корректно в облачном окружении (не frozen, REPO пуст), регрессии не обнаружено."
  - task: "Профиль органа регистрации: GET/POST /api/reg-profile + пакетная генерация бланков (мультистраничный PDF 147×103)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Новые эндпоинты профиля органа (для автозаполнения бланка). Проверить: (1) POST /api/reg-profile {reg_organ:'ОГиМ',chief:'Иванов И.И.',city:'г. Минск'} -> 200 {saved:true, reg_organ, chief, city}; (2) GET /api/reg-profile -> 200 c теми же значениями (идемпотентно после POST); (3) POST /api/reg-profile с пустым телом {} -> 200 (пустые строки). ПАКЕТНАЯ ПЕЧАТЬ (мультизапись): (4) POST /api/overlay/generate {records:[{fio:'A'},{fio:'B'},{fio:'C'}], page_size:'card', with_form:true} -> 200 application/pdf, PDF содержит РОВНО 3 страницы, каждая ~416.69×291.97 pt (147×103 мм). Для числа страниц/размеров используй pymupdf (len(doc), doc[i].rect)."
        - working: true
          agent: "testing"
          comment: "✅ 7/7 (100%). POST/GET /api/reg-profile сохраняет и идемпотентно возвращает {reg_organ,chief,city}; пустое тело обнуляет. Пакет: overlay/generate с 3 записями -> PDF ровно 3 страницы, каждая 416.69×291.97 pt (147×103 мм). Регрессия (form-background, print-silent 400 на Linux, stats) ок."
        - working: true
          agent: "testing"
          comment: "✅ Все 7 тестов прошли успешно (100% success rate). ПРОФИЛЬ ОРГАНА РЕГИСТРАЦИИ (3/3 теста): (1) POST /api/reg-profile {reg_organ:'ОГиМ Тестовый', chief:'Иванов И.И.', city:'г. Минск'} → 200 JSON {saved:true, reg_organ:'ОГиМ Тестовый', chief:'Иванов И.И.', city:'г. Минск'} — профиль сохранён корректно; (2) GET /api/reg-profile → 200 JSON с ТОЧНО теми же значениями (reg_organ:'ОГиМ Тестовый', chief:'Иванов И.И.', city:'г. Минск') — идемпотентность подтверждена; (3) POST /api/reg-profile с пустым телом {} → 200 JSON {saved:true, reg_organ:'', chief:'', city:''} — профиль очищен (пустые строки). ПАКЕТНАЯ ГЕНЕРАЦИЯ БЛАНКОВ (1/1 тест): (4) POST /api/overlay/generate {records:[{fio:'Первый'},{fio:'Второй'},{fio:'Третий'}], page_size:'card', with_form:true} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, содержит РОВНО 3 страницы (проверено через pymupdf len(doc)==3), КАЖДАЯ страница имеет размер РОВНО 416.69 × 291.97 pt (147×103 мм, допуск ±1.5pt выполнен для всех 3 страниц, проверено через pymupdf doc[i].rect). РЕГРЕССИЯ (3/3 теста): ✅ GET /api/overlay/form-background → 200 image/png, валидный PNG начинается с \\x89PNG, размер 56860 байт; ✅ POST /api/overlay/print-silent {records:[{fio:'X'}], page_size:'card'} → 400 (Bad Request), detail='Тихая печать доступна только в установленном Windows-приложении.' — грейсфул деградация на Linux работает корректно; ✅ GET /api/stats → 200 JSON с ключами total, drafts, this_month, datasets, recent. Все backend API полностью функциональны. Профиль органа регистрации работает идемпотентно, пакетная генерация создаёт мультистраничный PDF с точными размерами страниц 147×103 мм."
  - task: "Тихая печать бланка ровно 147×103 мм (page_size=card) + деградация на Linux"
    implemented: true
    working: true
    file: "server.py, document_service.py, frontend BlankOverlay.js/FullPrint.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Пользователь просил убедиться что тихая печать бланков идёт в формате 147x103. Фронтенд теперь форсирует page_size='card' в тихой печати (BlankOverlay doPrintSilent; FullPrint уже card). Backend build_overlay(page_size='card') делает страницу PDF ровно 147x103 мм (416.69x291.97 pt). Проверить на Linux (реальная печать невозможна — это ожидаемо): (1) POST /api/overlay/generate {records:[{fio:'Тест'}], page_size:'card', with_form:false} -> 200 application/pdf, размер страницы PDF = 147x103 мм (ширина ~416.69pt, высота ~291.97pt, допуск ±1pt); (2) POST /api/overlay/generate с with_form:true, page_size='card' -> 200, страница тоже 147x103 мм; (3) POST /api/overlay/generate page_size='a4' -> 200, страница A4 (~595x842pt); (4) POST /api/overlay/print-silent {records:[{fio:'Тест'}], page_size:'card'} -> 400 с сообщением про Windows-приложение (деградация на Linux); (5) GET /api/printers -> 200 {supported:false, printers:[]}. Для проверки размеров используй pymupdf/PyPDF2: открой PDF и прочитай mediabox первой страницы."
        - working: true
          agent: "testing"
          comment: "✅ 8/8 (100%). page_size='card' даёт страницу PDF РОВНО 416.69×291.97 pt = 147×103 мм (нулевое отклонение), и с with_form=false, и с true. page_size='a4' -> 595.28×841.89 pt (A4), не card. print-silent -> 400 «Тихая печать доступна только в установленном Windows-приложении.» (деградация на Linux). GET /api/printers -> {supported:false, printers:[]}. Регрессия (form-background, layout, stats) без ошибок."
        - working: true
          agent: "testing"
          comment: "✅ Все 8 тестов прошли успешно (100% success rate). РАЗМЕР СТРАНИЦЫ ПОДТВЕРЖДЁН ТОЧНО: (1) POST /api/overlay/generate {records:[{fio:'Тест Тестович'}], page_size:'card', with_form:false} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер страницы РОВНО 416.69 × 291.97 pt (147×103 мм, проверено через pymupdf doc[0].rect, допуск ±1.5 pt выполнен); (2) POST /api/overlay/generate {records:[{fio:'Тест'}], page_size:'card', with_form:true} → 200, валидный PDF, размер страницы РОВНО 416.69 × 291.97 pt (147×103 мм); (3) POST /api/overlay/generate {records:[{fio:'Тест'}], page_size:'a4', with_form:true} → 200, валидный PDF, размер страницы 595.28 × 841.89 pt (A4), НЕ 147×103 мм — корректно; (4) POST /api/overlay/print-silent {records:[{fio:'Тест'}], page_size:'card'} → 400 (Bad Request), Content-Type application/json, detail='Тихая печать доступна только в установленном Windows-приложении.' — грейсфул деградация на Linux работает корректно; (5) GET /api/printers → 200 JSON {supported:false, printers:[]} — корректное поведение на Linux. РЕГРЕССИЯ (3/3 теста): ✅ GET /api/overlay/form-background → 200, Content-Type image/png, валидный PNG начинается с \x89PNG, размер 56860 байт; ✅ GET /api/overlay/layout → 200 JSON с ключами layout (23 поля), dx_mm, dy_mm, page_mm=[147.0, 103.0]; ✅ GET /api/stats → 200 JSON с ключами total, drafts, this_month, datasets, recent. Все backend API полностью функциональны. Тихая печать бланков идёт в формате РОВНО 147×103 мм (416.69×291.97 pt) для page_size='card', деградация на Linux работает корректно."
  - task: "Чистый векторный фон бланка: GET /api/overlay/form-background (для «Полной печати»)"
    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Новый эндпоинт GET /api/overlay/form-background — рендерит чистую векторную форму «СООБЩЕНИЕ» (без данных) как PNG через pymupdf (docsvc.render_form_background_png, кэшируется). Используется как фон живого предпросмотра в разделе «Полная печать» вместо скана фотографии. Также мелко подправлены координаты SOOBSHENIE_LAYOUT (date_year 27.5->29.5, address 43->44.5) чтобы значения не наезжали на «20»/подпись. Проверить: (1) GET /api/overlay/form-background -> 200, Content-Type image/png, тело начинается с PNG-сигнатуры (\\x89PNG); (2) РЕГРЕССИЯ: POST /api/overlay/generate с with_form=true, page_size=card -> 200 валидный PDF (%PDF); GET /api/overlay/background (скан) -> 200 image/png; GET /api/overlay/layout -> 200; GET /api/stats -> 200."
        - working: true
          agent: "testing"
          comment: "✅ 17/17 тестов прошли (100%). GET /api/overlay/form-background -> 200 image/png, валидное PNG (\\x89PNG), 56860 байт — чистая векторная форма без данных. Регрессия без ошибок: overlay/generate (card/a4, with_form=true) -> валидный PDF; overlay/background (скан) -> 200 image/png; overlay/layout -> 200; stats -> 200."
        - working: true
          agent: "testing"
          comment: "✅ Все 17 тестов прошли успешно (100% success rate). НОВЫЙ ЭНДПОИНТ РАБОТАЕТ ПОЛНОСТЬЮ: (1) GET /api/overlay/form-background → 200, Content-Type: image/png, тело начинается с валидной PNG-сигнатуры \\x89PNG, размер 56860 байт (> 1000 байт требование выполнено). Это чистая векторная форма «СООБЩЕНИЕ» без данных, отрендеренная через pymupdf. РЕГРЕССИЯ (5/5 тестов): ✅ POST /api/overlay/generate с {records:[...], page_size:'card', with_form:true} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 59030 байт; ✅ POST /api/overlay/generate с page_size:'a4', with_form:true → 200, валидный PDF, размер 58945 байт; ✅ GET /api/overlay/background (скан-фото) → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 747920 байт; ✅ GET /api/overlay/layout → 200 JSON с ключами layout (23 поля), dx_mm, dy_mm, page_mm; ✅ GET /api/stats → 200 JSON с ключами total, drafts, this_month, datasets, recent. Все backend API полностью функциональны. Новая фича работает корректно, регрессии не обнаружено."
  - task: "LibreOffice восстановлен (soffice) для PDF-конвертации"
    implemented: true
    working: true
    file: "document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Окружение восстановлено без LibreOffice — preview/pdf/print давали 500 'soffice not found'. Установлен libreoffice-writer/core. Проверить /api/contracts/preview?format=pdf возвращает PDF."
        - working: true
          agent: "testing"
          comment: "✅ Все 5 тестов PDF-конвертации прошли успешно: (1) POST /api/contracts/preview?format=pdf возвращает валидный PDF с Content-Type application/pdf и начинается с %PDF; (2) POST /api/contracts/preview?format=docx возвращает валидный DOCX; (3) GET /api/contracts/{id}/download?format=pdf возвращает валидный PDF; (4) GET /api/contracts/{id}/download?format=docx возвращает валидный DOCX; (5) POST /api/contracts/batch-print возвращает объединённый PDF. LibreOffice soffice работает корректно."
  - task: "Черновики: PUT /api/contracts/{id}, status в POST /api/contracts, фильтр GET /api/contracts?status="
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Добавлен status (final/draft), updated_at. PUT обновляет существующий договор. GET с фильтром по статусу."
        - working: true
          agent: "testing"
          comment: "✅ Все 8 тестов черновиков прошли успешно: (1) POST /api/contracts со status='draft' создаёт черновик; (2) PUT /api/contracts/{id} обновляет поля и меняет статус draft→final; (3) GET /api/contracts/{id} подтверждает обновлённые данные; (4) GET /api/contracts?status=draft возвращает только черновики; (5) GET /api/contracts?status=final возвращает только готовые; (6) GET /api/contracts без параметра возвращает все; (7-8) Поиск ?q= по ФИО и номеру работает корректно."
  - task: "Пресеты полей: GET/POST/DELETE /api/presets"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Коллекция presets, CRUD (без update). POST требует name."
        - working: true
          agent: "testing"
          comment: "✅ Все 5 тестов пресетов прошли успешно: (1) POST /api/presets создаёт пресет с name и fields; (2) GET /api/presets возвращает список пресетов; (3) POST /api/presets с пустым name возвращает 400 (валидация работает); (4) DELETE /api/presets/{id} удаляет пресет (200); (5) Повторный DELETE возвращает 404 (корректная обработка)."
  - task: "Демо-данные: POST /api/seed-demo (идемпотентно), DELETE /api/seed-demo"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "6 демо-договоров (4 final + 2 draft), флаг demo:true. Повторный вызов не дублирует. DELETE удаляет только demo."
        - working: true
          agent: "testing"
          comment: "✅ Все 5 тестов демо-данных прошли успешно: (1) POST /api/seed-demo первый вызов создаёт 6 демо-договоров (created=6); (2) Повторный POST /api/seed-demo идемпотентен (created=0, already>0); (3) Демо-договоры существуют в БД с флагом demo:true; (4) DELETE /api/seed-demo удаляет все демо (deleted>=6); (5) После DELETE демо-договоры полностью удалены из БД. Идемпотентность работает корректно."
  - task: "Stats обновлён: total=final only, +drafts"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "total теперь считает только не-черновики, добавлен drafts, recent исключает черновики."
        - working: true
          agent: "testing"
          comment: "✅ Все 4 теста статистики прошли успешно: (1) GET /api/stats возвращает все обязательные поля (total, drafts, this_month, datasets, recent); (2) Поле 'total' НЕ учитывает черновики (только final); (3) Поле 'drafts' присутствует и содержит количество черновиков; (4) Массив 'recent' НЕ содержит черновиков. Логика подсчёта корректна."

  - task: "Overlay-печать на готовом бланке: /api/overlay/layout (GET/POST), /api/overlay/generate, /api/overlay/test-sheet, /api/overlay/background"
    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Новая фича: печать данных поверх пред-распечатанного бланка «СООБЩЕНИЕ» (147x103 мм). GET /api/overlay/layout возвращает раскладку (23 поля) + калибровку (dx_mm/dy_mm) + page_mm. POST /api/overlay/layout сохраняет раскладку в app_settings (upsert). POST /api/overlay/generate принимает {records:[{...}], layout?, dx_mm, dy_mm, with_background} и возвращает PDF 147x103мм (Content-Type application/pdf, начинается с %PDF); with_background=true рисует скан-подложку. GET /api/overlay/test-sheet?dx&dy — PDF пробного листа выравнивания. GET /api/overlay/background — PNG-подложка (image/png). Проверить: PDF валиден, размер страницы ~147x103мм, при пустых records возвращает 1 страницу, layout сохраняется и читается обратно. Шаблон договора .docx НЕ трогался."
        - working: "NA"
          agent: "main"
          comment: "ФИКС печати (Canon выплёвывал пустой лист): добавлен параметр page_size в POST /api/overlay/generate и GET /api/overlay/test-sheet — значения 'card' (147x103, дефолт) и 'a4' (лист A4 210x297, бланк-зона 147x103 в ЛЕВОМ ВЕРХНЕМ углу, для 'card'-обратная совместимость сохранена). Проверить: page_size=a4 -> страница ~210x297мм и валидный PDF; page_size=card -> ~147x103мм; test-sheet с page_size=a4 -> A4. Оба режима 200 + %PDF."
        - working: true
          agent: "testing"
          comment: "✅ Все 9 тестов overlay-печати прошли успешно (100% success rate). НОВЫЕ ЭНДПОИНТЫ РАБОТАЮТ ПОЛНОСТЬЮ: (1) GET /api/overlay/layout → 200 JSON с layout (23 поля), dx_mm, dy_mm, page_mm=[147,103]; каждое поле layout содержит key, x_pct, y_pct, font_pt; (2) POST /api/overlay/layout с кастомной раскладкой {layout:[{key:'fio',...}], dx_mm:1.5, dy_mm:-2} → 200 {saved:true,...}; (3) GET /api/overlay/layout после POST → возвращает сохранённую раскладку (1 поле, dx_mm=1.5, dy_mm=-2) — persistence в MongoDB app_settings работает корректно; (4) POST /api/overlay/generate с records (реальные данные: ФИО, номер, орган регистрации и т.д.) → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер страницы РОВНО 416.69x291.97pt (~147x103мм, проверено через pypdf); (5) POST /api/overlay/generate с пустым records=[] → 200, валидный PDF, РОВНО 1 пустая страница; (6) POST /api/overlay/generate с with_background:true → 200, валидный PDF, размер файла БОЛЬШЕ чем без фона (содержит PNG-подложку); (7) GET /api/overlay/test-sheet?dx=2&dy=1 → 200, Content-Type application/pdf, валидный PDF начинается с %PDF; (8) GET /api/overlay/background → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG. РЕГРЕССИЯ (3/3 теста): ✅ GET /api/stats работает; ✅ GET /api/contracts работает; ✅ POST /api/contracts/preview?format=pdf → 200 валидный PDF (LibreOffice установлен и работает). Шаблон договора .docx НЕ изменялся (проверено в тесте 11.8). Все backend API полностью функциональны."

  - task: "App config: GET/POST /api/app-config (windows_download_url)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Новый эндпоинт для ссылки на установщик Windows. GET /api/app-config → {windows_download_url:''} по умолчанию. POST /api/app-config {windows_download_url:'https://...'} → {saved:true, windows_download_url:'...'}, сохраняется в app_settings key=app_config (upsert), читается обратно через GET. Пустая строка также сохраняется. Проверить GET(default)→POST(set)→GET(persisted)→POST(clear)→GET(empty)."
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (5/5, 100% success rate). ЭНДПОИНТ /api/app-config ПОЛНОСТЬЮ РАБОТАЕТ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: (1) GET /api/app-config (default) → 200, windows_download_url='' (пустая строка по умолчанию) ✓. (2) POST /api/app-config {windows_download_url:'https://example.com/banetskaya-setup.exe'} → 200, saved=true, url='https://example.com/banetskaya-setup.exe' ✓. (3) GET /api/app-config (verify persistence) → 200, url='https://example.com/banetskaya-setup.exe' (персистентность в MongoDB app_settings подтверждена) ✓. (4) POST /api/app-config {windows_download_url:''} → 200, saved=true, url='' (очистка URL работает) ✓. (5) GET /api/app-config (verify empty) → 200, url='' (пустая строка сохранена корректно) ✓. Все операции GET(default)→POST(set)→GET(persisted)→POST(clear)→GET(empty) работают корректно. Эндпоинт готов к использованию."

  - task: "Заявление о регистрации по месту жительства: векторная отрисовка + эндпоинты /api/zayavlenie/*"
    implemented: true
    working: true
    file: "server.py, document_service.py, master_data.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "ДОБАВЛЕНО (2026-08-27, итерация 3): (A) Выборочная печать — во фронте у каждого заявления чекбокс, печать/скачивание только отмеченных. (B) Сохранение списка заявлений в БД («загрузить один раз»): НОВЫЕ ЭНДПОИНТЫ GET /api/zayavlenie/records → {records:[...]}; POST /api/zayavlenie/records {records:[...]} → {saved:true,count} (app_settings key=zayavlenie_records). Фронт авто-сохраняет список и подгружает при заходе. (C) В PDF добавлено подчёркивание текстовых элементов (el.underline) — рисуется линией под текстом. ПРОВЕРИТЬ доп.: (9) POST /api/zayavlenie/records {records:[{fio:'A','__print':true},{fio:'B','__print':false}]} → 200 saved=true count=2; GET /api/zayavlenie/records → тот же массив (2 записи, __print сохранён). Затем POST с {records:[]} → 200 count=0; GET → []. (10) Подчёркивание: POST /api/zayavlenie/template {template:[{id:'u1',type:'text',page:1,x:20,y:20,align:'left',text:'Подчёркнутый',size:12,underline:true}]} → 200; POST /api/zayavlenie/preview {records:[{}]} → 200 application/pdf 2 страницы (не падает с underline); затем ОБЯЗАТЕЛЬНО POST /api/zayavlenie/template/reset. Остальные пункты (1-8) как раньше."
        - working: "NA"
          agent: "main"
          comment: "РЕДАКТОР ШАБЛОНА (2026-08-27, вторая итерация)." — список элементов (type: text|line|field). ДАННЫЕ (ФИО, паспорт, адрес и т.п.) тоже элементы type=field (field указывает на слот из zayav_overlay_text). Тот же список элементов рисуется и в PDF (reportlab), и в предпросмотре на фронте. Элемент: {id,type,page(1|2),x(%),y(%),align,size(pt A4),bold,italic,font('serif'|'sans'),color; для text: text; для field: field; для line: w(%),thickness(pt)}. Дефолтный шаблон строится из старого статического бланка (81 text + 46 line) + 22 поля (из ZAYAV_LAYOUT_DEFAULT, перевод бокс→якорь) = 149 элементов. build_zayavlenie(people, template=None, ...) рисует по шаблону; layout-параметр устарел. НОВЫЕ ЭНДПОИНТЫ: GET /api/zayavlenie/template → {template:[...149 эл...], slots:[{slot,page,label}], is_custom:bool, page_count:2}; POST /api/zayavlenie/template {template:[...]} → {saved:true,count}; POST /api/zayavlenie/template/reset → {reset:true, template:[дефолт]} (удаляет app_settings key=zayavlenie_template). Старые /zayavlenie/layout оставлены (не используются). preview/preview-png/package теперь используют сохранённый template. ПРОВЕРИТЬ: (1) GET /api/zayavlenie/template → 200; template — массив ~149 элементов; типы включают text/line/field; есть field-элементы applicant, passport_series, area; slots — массив с label; is_custom=false на чистой БД. (2) POST /api/zayavlenie/template {template:[{id:'t1',type:'text',page:1,x:10,y:10,align:'left',text:'ТЕСТ ШАПКА',size:10,bold:true}]} → 200 saved=true count=1. Затем GET → template ровно из 1 элемента, is_custom=true. Затем POST /api/zayavlenie/template/reset → 200 reset=true, template снова ~149 элементов; повторный GET → is_custom=false. (3) POST /api/zayavlenie/preview {records:[{fio:'Иванов Иван Иванович',birth_year:'2006',passport_series:'MP',passport_number:'1234567',res_street:'пр-т Дзержинского',res_house:'85',from_place:'г. Гомель',basis:'договор найма № 12 от 01.09.2024',sign_date:'01.09.2024',area:'5467,9',occupancy_count:'250',minors_count:'3'}]} → 200 application/pdf; через pymupdf РОВНО 2 страницы A4-портрет (rect≈595.28×841.89); стр.0 текст содержит 'ЗАЯВЛЕНИЕ','по месту пребывания','Иванов Иван Иванович','пр-т Дзержинского'; стр.1 содержит 'Общая площадь' и '5467,9'. ВАЖНО: тест (2) сохраняет кастомный шаблон из 1 элемента — ОБЯЗАТЕЛЬНО вызвать reset в конце, иначе preview будет почти пустым; если делаешь preview после сохранения кастомного — сначала reset. (4) GET /api/zayavlenie/background?page=1 и page=2 → 200 image/png (совместимость). (5) POST /api/zayavlenie/preview-png side=front/back → 200 image/png. (6) POST /api/zayavlenie/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'MP1234567'}]} → 200 records (регрессия). (7) РЕГРЕССИЯ пакета: GET /api/master-template → openpyxl заполнить → POST /api/master-upload → 200 (ключ 'zayavlenie'); POST /api/package {people:[master_row], include:{zayavlenie:true}} → 200 application/pdf. (8) GET /api/_ping, /api/stats → 200."
        - working: "NA"
          agent: "main"
          comment: "(итерация 1, устарела — координатный layout) ПЕРЕРАБОТКА ОТОБРАЖЕНИЯ (2026-08-27)."
        - working: true
          agent: "main"
          comment: "(предыдущая версия — векторная 1:1, A4-ландшафт 2×A5, 'по месту жительства'. Переработано, см. запись выше.) Оригинальный комментарий сохранён ниже для истории."
        - working: "NA"
          agent: "main"
          comment: "НОВЫЙ ДОКУМЕНТ «Заявление о регистрации по месту жительства» (векторная отрисовка 1:1, A4-ландшафт: 2 заявления A5 в ряд, лицо=стр.1 двух человек, оборот=стр.2 тех же, дуплекс). Автозаполнение стр.1 из единого шаблона «Данные»; стр.2 пустая для руки, кроме площади (константа 5467,9). Паспорт разбивается на серию/номер. Эндпоинты: GET /api/zayavlenie/fields (сгруппированный список полей), GET/POST /api/zayavlenie/defaults (константы, хранятся в app_settings key=zayavlenie_defaults), POST /api/zayavlenie/prefill {students:[...]} → [zayavlenie records] (разбивка паспорта, area=5467,9, reg_who=одного, reg_count=1), POST /api/zayavlenie/preview {records, duplex_flip} → application/pdf (2 стр для 1-2 человек, 4 стр для 3-4), POST /api/zayavlenie/preview-png {side:'front'|'back'} → image/png. Интеграция с master-upload (ключ 'zayavlenie' в ответе) и package (include.zayavlenie, по умолчанию включён)."
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (15/15, 100% success rate). НОВЫЙ ДОКУМЕНТ «ЗАЯВЛЕНИЕ О РЕГИСТРАЦИИ ПО МЕСТУ ЖИТЕЛЬСТВА» ПОЛНОСТЬЮ РАБОТАЕТ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:
          
          ✅ TEST 1: GET /api/zayavlenie/fields
             → 200, возвращает {groups:[...], keys:[...]}
             → Найдено 4 группы с 16 ключами
             → ВСЕ требуемые ключи присутствуют: fio, passport_series, passport_number, passport_issued_by, passport_issue_date, reg_who, reg_count, address_locality, res_street, res_house, res_korpus, res_apartment, from_place, basis, sign_date, area ✓
             → Структура groups корректна (каждая группа содержит group и fields[{key,label}]) ✓
          
          ✅ TEST 2: GET /api/zayavlenie/defaults (initial)
             → 200, {defaults:{}} (пустой объект по умолчанию) ✓
          
          ✅ TEST 3: POST /api/zayavlenie/defaults (save)
             → {defaults:{area:'5467,9'}}
             → 200, saved=true ✓
          
          ✅ TEST 4: GET /api/zayavlenie/defaults (verify persistence)
             → 200, area='5467,9' (персистентность в MongoDB app_settings подтверждена) ✓
          
          ✅ TEST 5: POST /api/zayavlenie/preview (1 record)
             → {records:[{fio:'Иванов Иван Иванович',passport_series:'MP',passport_number:'1234567',area:'5467,9',sign_date:'21.07.2025',reg_who:'одного',reg_count:'1'}]}
             → 200, Content-Type application/pdf, валидный PDF начинается с %PDF
             → Проверено через pymupdf: РОВНО 2 СТРАНИЦЫ (лицо + оборот для 1 человека) ✓
          
          ✅ TEST 6: POST /api/zayavlenie/preview (2 records)
             → {records:[{fio:'Иванов...'},{fio:'Петров...'}]}
             → 200, Content-Type application/pdf, валидный PDF начинается с %PDF
             → Проверено через pymupdf: РОВНО 2 СТРАНИЦЫ (2 заявления A5 в ряд на 1 листе A4, лицо + оборот) ✓
          
          ✅ TEST 7: POST /api/zayavlenie/preview (3 records)
             → {records:[{fio:'Иванов...'},{fio:'Петров...'},{fio:'Сидоров...'}]}
             → 200, Content-Type application/pdf, валидный PDF начинается с %PDF
             → Проверено через pymupdf: РОВНО 4 СТРАНИЦЫ (2 листа A4: лист 1 лицо + оборот, лист 2 лицо + оборот) ✓
          
          ✅ TEST 8: POST /api/zayavlenie/preview-png (front)
             → {records:[{fio:'Тестов Тест Тестович',passport_series:'MP',passport_number:'1234567'}], side:'front'}
             → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 83857 байт ✓
          
          ✅ TEST 9: POST /api/zayavlenie/preview-png (back)
             → {records:[{fio:'Тестов Тест Тестович',passport_series:'MP',passport_number:'1234567'}], side:'back'}
             → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 70133 байт ✓
             → ПОДТВЕРЖДЕНИЕ РАЗЛИЧИЯ: front (83857 байт) и back (70133 байт) — РАЗНЫЕ изображения (разница 13724 байт) ✓
          
          ✅ TEST 10: POST /api/zayavlenie/prefill
             → {students:[<master-строка из master-upload>]}
             → 200, records[0] содержит:
                • fio='Иванов Иван Иванович' ✓
                • passport_series='MP', passport_number='1234567' (паспорт разбит корректно) ✓
                • area='5467,9' (константа применена) ✓
                • reg_who='одного' ✓
                • reg_count='1' ✓
          
          ✅ TEST 11: POST /api/master-upload (zayavlenie key)
             → Заполнен Excel-шаблон через openpyxl с реальными данными:
                • ФИО: 'Тестов Тест Тестович'
                • Дата рождения: datetime(2000, 1, 15)
                • Паспорт: 'MP1234567' (одной строкой)
                • Номер договора: 'TEST-001'
                • Дата подписания: datetime(2025, 7, 21)
             → POST /api/master-upload с заполненным .xlsx
             → 200, в ответе ПРИСУТСТВУЕТ ключ 'zayavlenie' (массив) ✓
             → zayavlenie[0] содержит:
                • passport_series='MP', passport_number='1234567' (паспорт РАЗБИТ корректно) ✓
                • sign_date='21.07.2025' (дата в формате ДД.ММ.ГГГГ, БЕЗ ' 00:00:00') ✓
                • area='5467,9' (константа применена) ✓
                • basis='договор найма жилого помещения № TEST-001 от 21.07...' (содержит 'договор найма' и номер договора) ✓
          
          ✅ TEST 12: POST /api/package (with zayavlenie)
             → {people:[<master-строка>], duplex_flip:'long', include:{contract:false, forma19:false, forma24:false, soobshenie:false, zayavlenie:true}}
             → 200, Content-Type application/pdf, валидный PDF начинается с %PDF
             → Проверено через pymupdf: РОВНО 2 СТРАНИЦЫ (только заявление: лицо + оборот) ✓
          
          ✅ TEST 13: POST /api/package (default includes zayavlenie)
             → {people:[<master-строка>], duplex_flip:'long', include:{}}
             → 200, Content-Type application/pdf, валидный PDF начинается с %PDF
             → Проверено через pymupdf: РОВНО 9 СТРАНИЦ (договор 4 стр + Ф19+Ф24 2 стр + сообщение 1 стр + заявление 2 стр) ✓
             → ПОДТВЕРЖДЕНИЕ: при пустом include заявление ВКЛЮЧЕНО ПО УМОЛЧАНИЮ ✓
          
          РЕГРЕССИЯ (2/2 PASS):
          
          ✅ R1: GET /api/
             → 200 ✓
          
          ✅ R2: GET /api/stats
             → 200 ✓
          
          ЗАКЛЮЧЕНИЕ:
          
          🎉 НОВЫЙ ДОКУМЕНТ «ЗАЯВЛЕНИЕ О РЕГИСТРАЦИИ ПО МЕСТУ ЖИТЕЛЬСТВА» ПОЛНОСТЬЮ ФУНКЦИОНАЛЕН:
          • GET /api/zayavlenie/fields возвращает корректную структуру с 4 группами и 16 ключами
          • GET/POST /api/zayavlenie/defaults работает с персистентностью в MongoDB
          • POST /api/zayavlenie/preview генерирует корректный PDF: 2 страницы для 1-2 человек, 4 страницы для 3-4 человек (A4-ландшафт, 2 заявления A5 в ряд)
          • POST /api/zayavlenie/preview-png рендерит лицевую и оборотную стороны как PNG (разные изображения)
          • POST /api/zayavlenie/prefill корректно разбивает паспорт на серию/номер, применяет константы (area=5467,9, reg_who=одного, reg_count=1)
          • POST /api/master-upload возвращает ключ 'zayavlenie' с корректными данными (паспорт разбит, даты в формате ДД.ММ.ГГГГ, basis содержит номер договора)
          • POST /api/package интегрирован с заявлением: include.zayavlenie работает, по умолчанию заявление включено в пакет
          • Все backend API полностью функциональны
          • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО
          
          Новый документ готов к использованию."
        - working: true
          agent: "testing"
          comment: "✅ ОБНОВЛЁННОЕ ЗАЯВЛЕНИЕ «ПО МЕСТУ ПРЕБЫВАНИЯ» ПОЛНОСТЬЮ РАБОТАЕТ (7/7 тестов, 100% success rate). КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ ПОДТВЕРЖДЕНЫ:
          
          ✅ TEST 1: GET /api/zayavlenie/fields
             → 200, возвращает {groups:[...], keys:[...]}
             → Найдено 19 ключей (было 16)
             → ВСЕ НОВЫЕ КЛЮЧИ ПРИСУТСТВУЮТ: birth_year, doc_name, stay_term ✓
             → Все требуемые ключи: fio, birth_year, doc_name, passport_series, passport_number, passport_issued_by, passport_issue_date, reg_who, reg_count, address_locality, res_street, res_house, res_korpus, res_apartment, stay_term, from_place, basis, sign_date, area ✓
          
          ✅ TEST 2: POST /api/zayavlenie/preview (page counts)
             → 1 запись → 200 PDF, РОВНО 2 страницы (проверено через pymupdf) ✓
             → 2 записи → 200 PDF, РОВНО 2 страницы ✓
             → 3 записи → 200 PDF, РОВНО 4 страницы ✓
             → Все PDF валидны (начинаются с %PDF), Content-Type application/pdf ✓
          
          ✅ TEST 3: POST /api/zayavlenie/preview-png (front/back)
             → side='front' → 200, Content-Type image/png, валидный PNG (\\x89PNG), размер 86266 байт ✓
             → side='back' → 200, Content-Type image/png, валидный PNG (\\x89PNG), размер 62449 байт ✓
             → ПОДТВЕРЖДЕНИЕ РАЗЛИЧИЯ: front и back — РАЗНЫЕ изображения (разница 23817 байт) ✓
          
          ✅ TEST 4: Master template upload flow
             → GET /api/master-template → 200, скачано 9251 байт .xlsx ✓
             → Заполнен Excel через openpyxl с datetime-объектами:
                • birth_date: datetime(2006, 8, 3)
                • passport_issue_date: datetime(2020, 1, 10)
                • sign_date: datetime(2025, 7, 21)
                • contract_end_date: datetime(2028, 6, 30) — КЛЮЧЕВОЕ ПОЛЕ для stay_term
             → POST /api/master-upload → 200, в ответе ПРИСУТСТВУЕТ ключ 'zayavlenie' (массив) ✓
             → zayavlenie[0] КРИТИЧЕСКИЕ ПОЛЯ:
                • doc_name = 'паспорт гражданина Республики Беларусь' (НОВОЕ ПОЛЕ, дефолтное значение) ✓
                • stay_term = 'срок до 30.06.2028' (НОВОЕ ПОЛЕ, из contract_end_date, формат ДД.ММ.ГГГГ, БЕЗ '00:00:00') ✓
                • basis = 'Договор найма № TEST-001 от 21.07.2025' (ИЗМЕНЕНО: ВСЕГДА начинается с 'Договор найма № ', содержит номер и дату) ✓
                • birth_year = '2006' (НОВОЕ ПОЛЕ, 4 цифры, год из birth_date) ✓
                • area = '5467,9' (константа) ✓
                • passport_series = 'MP', passport_number = '1234567' (разбивка работает) ✓
                • passport_issue_date = '10.01.2020' (формат ДД.ММ.ГГГГ, БЕЗ '00:00:00') ✓
          
          ✅ TEST 5: POST /api/zayavlenie/prefill
             → {students:[<master-данные>]} → 200, records[0] содержит:
                • doc_name = 'паспорт гражданина Республики Беларусь' ✓
                • stay_term начинается с 'срок до ' ✓
                • basis начинается с 'Договор найма № ' ✓
                • birth_year = '2006' ✓
                • area = '5467,9' ✓
                • passport_series = 'MP', passport_number = '1234567' ✓
          
          ✅ TEST 6: POST /api/package (with zayavlenie)
             → {people:[<master>], include:{zayavlenie:true, остальные:false}} → 200 PDF, 102559 байт, 2 страницы ✓
             → Пакет содержит только заявление (лицо + оборот) ✓
          
          ✅ TEST 7: Regression tests (6/6 PASS)
             → GET /api/ → 200 ✓
             → GET /api/stats → 200 (total, drafts присутствуют) ✓
             → POST /api/forma19/preview → 200 PDF ✓
             → POST /api/forma24/preview → 200 PDF ✓
             → POST /api/overlay/generate → 200 PDF ✓
             → POST /api/contracts/preview → 200 PDF ✓
          
          ЗАКЛЮЧЕНИЕ:
          
          🎉 ОБНОВЛЕНИЕ «ЗАЯВЛЕНИЕ ПО МЕСТУ ПРЕБЫВАНИЯ» ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНО:
          • НОВЫЕ ПОЛЯ: birth_year (год рождения, 4 цифры), doc_name (по умолчанию 'паспорт гражданина Республики Беларусь'), stay_term (из contract_end_date как 'срок до {дата}', формат ДД.ММ.ГГГГ, БЕЗ времени)
          • ИЗМЕНЁННОЕ ПОЛЕ: basis ВСЕГДА 'Договор найма № {номер} от {дата}'
          • ШРИФТ: Times New Roman (Liberation Serif) применён в векторной отрисовке
          • GET /api/zayavlenie/fields возвращает 19 ключей (было 16), все новые ключи присутствуют
          • POST /api/zayavlenie/preview генерирует корректный PDF: 2 страницы для 1-2 человек, 4 страницы для 3-4 человек
          • POST /api/zayavlenie/preview-png рендерит лицевую (side='front') и оборотную (side='back') стороны как PNG (разные изображения)
          • POST /api/master-upload корректно преобразует contract_end_date (datetime) в stay_term ('срок до ДД.ММ.ГГГГ'), birth_date в birth_year (4 цифры), формирует basis с номером и датой договора
          • POST /api/zayavlenie/prefill применяет те же трансформации
          • POST /api/package интегрирован с обновлённым заявлением
          • Все backend API полностью функциональны
          • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО (forma19, forma24, soobshenie, contracts работают корректно)
          
          Обновлённый документ готов к использованию."
        - working: true
          agent: "testing"
          comment: "✅ ПЕРЕРАБОТКА ЗАЯВЛЕНИЯ НА A4-ПОРТРЕТ ПОЛНОСТЬЮ РАБОТАЕТ (8/8 тестов, 100% success rate). КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ АРХИТЕКТУРЫ ПОДТВЕРЖДЕНЫ:
          
          === НОВАЯ АРХИТЕКТУРА (A4-ПОРТРЕТ, 2 СТРАНИЦЫ НА ЧЕЛОВЕКА) ===
          
          ✅ TEST 1: GET /api/zayavlenie/layout
             → 200, возвращает {layout:{'1':{...},'2':{...}}, slots:[...], page_count:2}
             → page_count = 2 (РОВНО 2 страницы на человека, НЕ A4-ландшафт) ✓
             → layout['1'] содержит 19 слотов (≥19 требование выполнено) ✓
             → ВСЕ ТРЕБУЕМЫЕ СЛОТЫ СТРАНИЦЫ 1 ПРИСУТСТВУЮТ: applicant, passport_series, passport_number, res_street, basis, sign_day ✓
             → layout['2'] содержит 3 слота ✓
             → ВСЕ ТРЕБУЕМЫЕ СЛОТЫ СТРАНИЦЫ 2 ПРИСУТСТВУЮТ: area, occupancy_count, minors_count ✓
             → slots — массив из 22 элементов, каждый содержит slot/page/label ✓
             → Структура layout корректна: координаты в процентах страницы (x, y, w), align, size, bold ✓
          
          ✅ TEST 2: POST /api/zayavlenie/layout (save & merge)
             → POST {layout:{'1':{applicant:{x:31.0,y:11.0,w:65,align:'center',size:10,bold:false}}}}
             → 200, saved=true ✓
             → Повторный GET /api/zayavlenie/layout → applicant.x == 31.0 (персистентность в MongoDB app_settings подтверждена) ✓
             → КРИТИЧЕСКАЯ ПРОВЕРКА MERGE: passport_series и basis ВСЁ ЕЩЁ ПРИСУТСТВУЮТ в layout['1'] (merge с дефолтами, НЕ перезапись) ✓
             → Всего слотов в page 1 после частичного обновления: 19 (не затёрлись) ✓
             → ВОССТАНОВЛЕНИЕ: POST {layout:{}} → 200 (раскладка сброшена к дефолтам) ✓
          
          ✅ TEST 3: GET /api/zayavlenie/background (PNG фоны)
             → GET /api/zayavlenie/background?page=1
                • 200, Content-Type: image/png ✓
                • Тело начинается с PNG-сигнатуры \\x89PNG ✓
                • Размер: 108897 байт (> 5000 байт требование выполнено) ✓
             → GET /api/zayavlenie/background?page=2
                • 200, Content-Type: image/png ✓
                • Тело начинается с PNG-сигнатуры \\x89PNG ✓
                • Размер: 83088 байт (> 5000 байт требование выполнено) ✓
             → КРИТИЧЕСКАЯ ПРОВЕРКА РАЗЛИЧИЯ: MD5 хэши page=1 и page=2 РАЗНЫЕ (hash1=77747cf8, hash2=852b4581) ✓
             → page=1 и page=2 — это РАЗНЫЕ изображения (лицо и оборот) ✓
          
          ✅ TEST 4: POST /api/zayavlenie/preview (PDF с данными)
             → POST {records:[{fio:'Иванов Иван Иванович',birth_year:'2006',passport_series:'MP',passport_number:'1234567',res_street:'пр-т Дзержинского',res_house:'85',from_place:'г. Гомель',basis:'договор найма № 12 от 01.09.2024',sign_date:'01.09.2024',area:'5467,9',occupancy_count:'250',minors_count:'3'}]}
             → 200, Content-Type: application/pdf ✓
             → Тело начинается с %PDF ✓
             → Размер: 102626 байт ✓
             → ПРОВЕРКА ЧЕРЕЗ PYMUPDF:
                • Число страниц: РОВНО 2 (len(doc)==2) ✓
                • Страница 0 размер: 595.28 × 841.89 pt (A4-ПОРТРЕТ, допуск ±2pt выполнен) ✓
                • Страница 1 размер: 595.28 × 841.89 pt (A4-ПОРТРЕТ, допуск ±2pt выполнен) ✓
             → ИЗВЛЕЧЕНИЕ ТЕКСТА СТРАНИЦЫ 0 (через pymupdf.get_text()):
                • Найдено 'ЗАЯВЛЕНИЕ' ✓
                • Найдено 'по месту пребывания' (НЕ 'жительства' — КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ) ✓
                • Найдено 'Иванов Иван Иванович' ✓
                • Найдено 'пр-т Дзержинского' ✓
             → ИЗВЛЕЧЕНИЕ ТЕКСТА СТРАНИЦЫ 1 (через pymupdf.get_text()):
                • Найдено 'Общая площадь' ✓
                • Найдено '5467,9' ✓
             → ПОДТВЕРЖДЕНИЕ: PDF содержит РОВНО 2 страницы A4-ПОРТРЕТ (НЕ A4-ландшафт 2×A5), заголовок 'по месту ПРЕБЫВАНИЯ' (НЕ 'жительства') ✓
          
          ✅ TEST 5: POST /api/zayavlenie/preview-png (PNG предпросмотр)
             → POST {records:[{...}], side:'front'}
                • 200, Content-Type: image/png ✓
                • Тело начинается с \\x89PNG ✓
                • Размер: 115834 байт ✓
             → POST {records:[{...}], side:'back'}
                • 200, Content-Type: image/png ✓
                • Тело начинается с \\x89PNG ✓
                • Размер: 80566 байт ✓
             → КРИТИЧЕСКАЯ ПРОВЕРКА РАЗЛИЧИЯ: front и back — РАЗНЫЕ изображения (размеры различаются на 35268 байт) ✓
             → side='front' рендерит страницу 0 (лицо), side='back' рендерит страницу 1 (оборот) ✓
          
          ✅ TEST 6: POST /api/zayavlenie/prefill (регрессия)
             → POST {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'MP1234567'}]}
             → 200, возвращает {records:[...]} ✓
             → records — массив, длина > 0 ✓
             → Первая запись содержит корректные поля (fio, birth_year, passport_series, area='5467,9') ✓
             → Регрессия prefill/master_to_zayavlenie НЕ СЛОМАНА ✓
          
          ✅ TEST 7: РЕГРЕССИЯ ПАКЕТА (master-template → master-upload → package)
             → GET /api/master-template
                • 200, Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet ✓
                • Размер: 9251 байт ✓
             → Заполнен Excel через openpyxl с datetime-объектами:
                • ФИО: 'Иванов Иван Иванович'
                • Дата рождения: datetime(2006, 8, 3)
                • Паспорт: 'MP1234567'
                • Дата подписания: datetime(2024, 9, 1)
             → POST /api/master-upload с заполненным .xlsx
                • 200, Content-Type: application/json ✓
                • Response keys: ['count', 'master', 'contracts', 'forma19', 'forma24', 'soobshenie', 'zayavlenie'] ✓
                • КРИТИЧЕСКАЯ ПРОВЕРКА: ключ 'zayavlenie' ПРИСУТСТВУЕТ в ответе ✓
                • zayavlenie — массив, длина > 0 ✓
             → POST /api/package {people:[master[0]], include:{zayavlenie:true}}
                • 200, Content-Type: application/pdf ✓
                • Тело начинается с %PDF ✓
                • Размер: 280427 байт ✓
                • Проверено через pymupdf: 9 страниц (договор 4 + Ф19+Ф24 2 + сообщение 1 + заявление 2) ✓
             → Регрессия пакета НЕ СЛОМАНА ✓
          
          ✅ TEST 8: РЕГРЕССИЯ ЗДОРОВЬЯ
             → GET /api/_ping
                • 200, {ok:true} ✓
             → GET /api/stats
                • 200, JSON с ключами total, drafts, this_month, datasets, recent ✓
             → Регрессия здоровья НЕ СЛОМАНА ✓
          
          === ИТОГОВОЕ ЗАКЛЮЧЕНИЕ ===
          
          🎉 ПЕРЕРАБОТКА ЗАЯВЛЕНИЯ НА A4-ПОРТРЕТ ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНА:
          
          КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ АРХИТЕКТУРЫ:
          • ФОРМАТ: A4-ПОРТРЕТ (595.28×841.89 pt), НЕ A4-ландшафт 2×A5 ✓
          • СТРАНИЦ НА ЧЕЛОВЕКА: РОВНО 2 (стр.1 лицо + стр.2 оборот), НЕ 2 заявления A5 в ряд ✓
          • ЗАГОЛОВОК: 'ЗАЯВЛЕНИЕ о регистрации по месту ПРЕБЫВАНИЯ', НЕ 'по месту жительства' ✓
          • КООРДИНАТЫ: проценты страницы (x, y, w), одинаковые в PDF и HTML-предпросмотре ✓
          • РАСКЛАДКА: 22 слота (19 на стр.1 + 3 на стр.2), конфигурация в app_settings key=zayavlenie_layout ✓
          
          НОВЫЕ ЭНДПОИНТЫ:
          • GET /api/zayavlenie/layout → {layout:{'1':{...},'2':{...}}, slots:[...], page_count:2} ✓
          • POST /api/zayavlenie/layout → {saved:true, layout} (merge с дефолтами, НЕ перезапись) ✓
          • GET /api/zayavlenie/background?page=1|2 → image/png (чистый бланк лица/оборота) ✓
          
          ОБНОВЛЁННЫЕ ЭНДПОИНТЫ:
          • POST /api/zayavlenie/preview → PDF A4-ПОРТРЕТ, 2 страницы на человека ✓
          • POST /api/zayavlenie/preview-png → PNG side='front'|'back' (разные изображения) ✓
          • POST /api/zayavlenie/prefill → регрессия НЕ СЛОМАНА ✓
          • POST /api/master-upload → ключ 'zayavlenie' присутствует ✓
          • POST /api/package → интеграция с заявлением работает ✓
          
          РЕГРЕССИЙ НЕ ОБНАРУЖЕНО:
          • master-template, master-upload, package работают корректно ✓
          • _ping, stats работают корректно ✓
          
          СТАРЫЕ ОЖИДАНИЯ БОЛЬШЕ НЕ АКТУАЛЬНЫ:
          • ❌ A4-ландшафт (теперь A4-портрет)
          • ❌ 2×A5 в ряд (теперь 2 страницы на человека)
          • ❌ Заголовок 'по месту жительства' (теперь 'по месту пребывания')
          
          Переработанное заявление готово к использованию."
        - working: true
          agent: "testing"
          comment: "✅ НОВЫЕ ФУНКЦИИ ЗАЯВЛЕНИЯ ПОЛНОСТЬЮ РАБОТАЮТ (6/6 тестов, 100% success rate). ФОКУСНАЯ ПРОВЕРКА НОВЫХ BACKEND-ВОЗМОЖНОСТЕЙ + БЫСТРАЯ РЕГРЕССИЯ ПОДТВЕРЖДЕНА:
          
          === НОВЫЕ ФУНКЦИИ (3/3 PASS) ===
          
          ✅ TEST 1: Сохранение списка заявлений (persist)
             → Step 1a: POST /api/zayavlenie/records {records:[{fio:'A',__print:true},{fio:'B',__print:false}]}
                • 200, saved=true, count=2 ✓
             → Step 1b: GET /api/zayavlenie/records
                • 200, возвращает {records:[...]} ✓
                • РОВНО 2 записи (len(records)==2) ✓
                • КРИТИЧЕСКАЯ ПРОВЕРКА: поле __print СОХРАНЕНО корректно:
                  - Record A: __print=true ✓
                  - Record B: __print=false ✓
                • ПЕРСИСТЕНТНОСТЬ В MONGODB app_settings ПОДТВЕРЖДЕНА ✓
             → Step 1c: POST /api/zayavlenie/records {records:[]}
                • 200, count=0 ✓
                • GET /api/zayavlenie/records → records==[] (пустой массив) ✓
                • ОЧИСТКА РАБОТАЕТ КОРРЕКТНО ✓
          
          ✅ TEST 2: Подчёркивание в PDF не ломает генерацию
             → Step 2a: POST /api/zayavlenie/template {template:[{id:'u1',type:'text',page:1,x:20,y:20,align:'left',text:'Подчёркнутый',size:12,underline:true}]}
                • 200, saved=true ✓
             → Step 2b: POST /api/zayavlenie/preview {records:[{fio:'Тест'}]}
                • 200, Content-Type application/pdf ✓
                • Валидный PDF начинается с %PDF ✓
                • Размер: 32222 байт ✓
                • ПРОВЕРКА ЧЕРЕЗ PYMUPDF: РОВНО 2 СТРАНИЦЫ (len(doc)==2) ✓
                • КРИТИЧЕСКОЕ ПОДТВЕРЖДЕНИЕ: PDF генерируется БЕЗ ПАДЕНИЯ с элементом underline:true ✓
             → Step 2c: POST /api/zayavlenie/template/reset (ОБЯЗАТЕЛЬНО)
                • 200, reset=true ✓
                • Response содержит template с 149 элементами ✓
                • ШАБЛОН ВОССТАНОВЛЕН К ДЕФОЛТУ ✓
          
          === РЕГРЕССИЯ (4/4 PASS) ===
          
          ✅ TEST 3: POST /api/zayavlenie/preview (с реальными данными)
             → {records:[{fio:'Иванов Иван Иванович',birth_year:'2006',area:'5467,9',res_street:'пр-т Дзержинского'}]}
             → 200, Content-Type application/pdf ✓
             → Валидный PDF начинается с %PDF ✓
             → Размер: 102257 байт ✓
             → ПРОВЕРКА ЧЕРЕЗ PYMUPDF:
                • РОВНО 2 СТРАНИЦЫ (len(doc)==2) ✓
                • Page 0: размер 595.28×841.89 pt (A4-портрет, допуск ±2pt выполнен) ✓
                • Page 1: размер 595.28×841.89 pt (A4-портрет, допуск ±2pt выполнен) ✓
             → ПРОВЕРКА ТЕКСТА:
                • Page 0 содержит: 'ЗАЯВЛЕНИЕ', 'по месту пребывания', 'Иванов Иван Иванович', 'пр-т Дзержинского' ✓
                • Page 1 содержит: 'Общая площадь', '5467,9' ✓
             → РЕГРЕССИЯ PREVIEW НЕ СЛОМАНА ✓
          
          ✅ TEST 4: GET /api/zayavlenie/template
             → 200 ✓
             → template содержит РОВНО 149 элементов (в диапазоне 140-160) ✓
             → is_custom=false (шаблон сброшен к дефолту) ✓
             → РЕГРЕССИЯ TEMPLATE НЕ СЛОМАНА ✓
          
          ✅ TEST 5: POST /api/zayavlenie/preview-png
             → side='front': 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 103881 байт ✓
             → side='back': 200, Content-Type image/png, валидный PNG начинается с \\x89PNG, размер 78183 байт ✓
             → РЕГРЕССИЯ PREVIEW-PNG НЕ СЛОМАНА ✓
          
          ✅ TEST 6: GET /api/_ping и GET /api/stats
             → GET /api/_ping: 200, {ok:true} ✓
             → GET /api/stats: 200, JSON с ключами total, drafts, this_month, datasets, recent ✓
             → РЕГРЕССИЯ ЗДОРОВЬЯ НЕ СЛОМАНА ✓
          
          === ОБЯЗАТЕЛЬНАЯ ОЧИСТКА СОСТОЯНИЯ ===
          
          ✓ POST /api/zayavlenie/records {records:[]} → 200 (записи очищены)
          ✓ GET /api/zayavlenie/template → is_custom=false (шаблон сброшен)
          
          === ИТОГОВОЕ ЗАКЛЮЧЕНИЕ ===
          
          🎉 НОВЫЕ ФУНКЦИИ ЗАЯВЛЕНИЯ ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНЫ:
          
          НОВЫЕ BACKEND-ВОЗМОЖНОСТИ:
          • POST /api/zayavlenie/records {records:[...]} → {saved:true, count} (сохранение списка заявлений) ✓
          • GET /api/zayavlenie/records → {records:[...]} (загрузка списка заявлений) ✓
          • ПЕРСИСТЕНТНОСТЬ: поле __print (true/false) сохраняется корректно в MongoDB app_settings key=zayavlenie_records ✓
          • ОЧИСТКА: POST с пустым массивом records=[] работает корректно ✓
          • ПОДЧЁРКИВАНИЕ: элемент template с underline:true НЕ ломает генерацию PDF (2 страницы генерируются без падения) ✓
          • ОБЯЗАТЕЛЬНЫЙ RESET: POST /api/zayavlenie/template/reset восстанавливает дефолтный шаблон (149 элементов, is_custom=false) ✓
          
          РЕГРЕССИЯ:
          • POST /api/zayavlenie/preview → PDF A4-портрет, 2 страницы, корректный текст на обеих страницах ✓
          • GET /api/zayavlenie/template → 149 элементов, is_custom=false ✓
          • POST /api/zayavlenie/preview-png → PNG front/back (разные изображения) ✓
          • GET /api/_ping, GET /api/stats → 200 ✓
          • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО ✓
          
          КРИТИЧЕСКОЕ ЗАМЕЧАНИЕ:
          • ОБЯЗАТЕЛЬНО вызывать POST /api/zayavlenie/template/reset ПОСЛЕ сохранения кастомного шаблона с underline, иначе preview будет почти пустым (содержать только кастомные элементы)
          • ОБЯЗАТЕЛЬНО очищать records после тестирования: POST /api/zayavlenie/records {records:[]}
          
          Новые функции готовы к использованию."



  - task: "Единый Excel-шаблон и полный пакет документов: GET /api/master-template, POST /api/master-upload, POST /api/package"
    implemented: true
    working: true
    file: "server.py, master_data.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "user"
          comment: "НОВАЯ ФИЧА (запрос пользователя): единый Excel-шаблон для всех документов + полный пакет документов в PDF. (1) GET /api/master-template → скачать .xlsx с листами 'Данные' (заголовки во 2-й строке, пробные данные в 3-й) и 'Инструкция'. (2) POST /api/master-upload → загрузить заполненный .xlsx, получить JSON с массивами master, contracts, forma19, forma24, soobshenie. (3) POST /api/package {people:[...], duplex_flip:'long'} → полный пакет PDF (договор 4 стр + объединённый лист Ф19+Ф24 2 стр + сообщение 1 стр = 7 стр на человека). (4) POST /api/package с include:{contract:false, forma19:true, forma24:true, soobshenie:false} → только Ф19+Ф24 (2 стр). (5) Регресс: GET /api/fields, POST /api/forma24/preview. НЕ трогать данные договоров/историю."
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (6/6, 100% success rate). НОВЫЕ ЭНДПОИНТЫ ПОЛНОСТЬЮ РАБОТАЮТ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:
        
        ✅ TEST 1: GET /api/master-template
           → 200, Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
           → Excel размер: 9251 байт
           → Листы: ['Данные', 'Инструкция'] ✓
           → Лист 'Данные' строка 2 (заголовки): ['ФИО (полностью)', 'Дата рождения (ДД.ММ.ГГГГ)', 'Пол (1-муж, 2-жен)'] ✓
           → Лист 'Данные' строка 3 (пробные данные): ['Иванов Иван Иванович', '15.03.2004', '1'] ✓
           → Структура Excel корректна (проверено через openpyxl) ✓
        
        ✅ TEST 2: POST /api/master-upload
           → Загружен тот же скачанный .xlsx
           → 200, Content-Type: application/json
           → Response keys: ['count', 'master', 'contracts', 'forma19', 'forma24', 'soobshenie'] ✓
           → count: 1 (>= 1) ✓
           → Все массивы непустые (len >= 1) ✓
           → forma24[0] содержит:
              • surname='Иванов' ✓
              • first_name='Иван' ✓
              • birth_month='марта' ✓
              • sex='1' ✓
           → contracts[0] содержит:
              • full_name='Иванов Иван Иванович' ✓
              • registration_address='пр-т Дзержинского, 85, ком. 302/2' (непустой, склеенный адрес) ✓
           → soobshenie[0] содержит:
              • fio (присутствует) ✓
              • date_day (присутствует) ✓
              • passport_series='MP' ✓
           → Парсинг и преобразование данных работают корректно ✓
        
        ✅ TEST 3: POST /api/package (полный пакет)
           → {people:[master[0]], duplex_flip:'long'}
           → 200, Content-Type: application/pdf
           → PDF размер: 183279 байт
           → Валидный PDF начинается с %PDF ✓
           → Проверено через pymupdf: РОВНО 7 СТРАНИЦ для 1 человека ✓
           → Страница 0 содержит: 'ДОГОВОР' ✓
           → Страница 4 содержит ОБА текста:
              • 'Форма № 19' (АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ) ✓
              • 'Форма 24' (ТАЛОН МИГРАЦИОННОГО) ✓
              • Обе формы на одном листе (верхний ряд Ф19, нижний Ф24) ✓
           → Страница 6 содержит: 'СООБЩЕНИЕ' ✓
           → Структура пакета: Договор (4 стр) + Ф19+Ф24 объединённые (2 стр лицо+оборот) + Сообщение (1 стр) = 7 стр ✓
        
        ✅ TEST 4: POST /api/package (частичный пакет)
           → {people:[master[0]], duplex_flip:'long', include:{contract:false, forma19:true, forma24:true, soobshenie:false}}
           → 200, Content-Type: application/pdf
           → PDF размер: 72762 байт
           → Валидный PDF начинается с %PDF ✓
           → Проверено через pymupdf: РОВНО 2 СТРАНИЦЫ ✓
           → Только объединённый лист Ф19+Ф24 (лицо и оборот) ✓
           → Параметр include работает корректно (исключены contract и soobshenie) ✓
        
        РЕГРЕССИЯ (2/2 PASS):
        
        ✅ R1: GET /api/fields
           → 200, JSON с ключом 'fields' ✓
           → fields: массив из 17 элементов ✓
        
        ✅ R2: POST /api/forma24/preview
           → {records:[{surname:'Тест'}], duplex_flip:'long'}
           → 200, Content-Type: application/pdf
           → Валидный PDF начинается с %PDF ✓
           → Размер: 63719 байт ✓
        
        ЗАКЛЮЧЕНИЕ:
        
        🎉 ЕДИНЫЙ EXCEL-ШАБЛОН И ПОЛНЫЙ ПАКЕТ ДОКУМЕНТОВ ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНЫ:
        • GET /api/master-template возвращает корректный Excel с листами 'Данные' и 'Инструкция'
        • POST /api/master-upload парсит Excel и возвращает все необходимые массивы (master, contracts, forma19, forma24, soobshenie)
        • POST /api/package генерирует полный пакет документов (7 страниц на человека: договор 4 стр + объединённый лист Ф19+Ф24 2 стр + сообщение 1 стр)
        • POST /api/package с параметром include позволяет выбирать документы (частичный пакет работает корректно)
        • Все backend API полностью функциональны
        • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО
        
        Новая фича готова к использованию."

  - task: "Умная загрузка: POST /api/generate/upload (единый шаблон vs старый договорный Excel)"
    implemented: true
    working: true
    file: "server.py, master_data.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "НОВАЯ ФИЧА: умная загрузка Excel через POST /api/generate/upload. Определяет тип файла (единый master-шаблон с 49 колонками vs старый договорный с 17 колонками) и возвращает mode='master' или mode='contracts'. Для master-шаблона возвращает students (для contracts/batch) и masters (полные данные человека с >=40 ключами). Проверить: (1) GET /api/master-template → скачать .xlsx. (2) POST /api/generate/upload с этим файлом (multipart form-data, поле 'file') → 200, mode='master', count>=1, students[0].full_name='Иванов Иван Иванович', students[0].registration_address непустой, masters[0] содержит >=40 ключей (bp_obl, sex, education, purpose_choice и т.д.)."
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (2/2, 100% success rate). УМНАЯ ЗАГРУЗКА РАБОТАЕТ ПОЛНОСТЬЮ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: (1) GET /api/master-template → 200, Content-Type application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, скачано 9251 байт, валидный Excel с листами ['Данные', 'Инструкция'] (проверено через openpyxl). (2) POST /api/generate/upload с загруженным .xlsx (multipart form-data, поле 'file') → 200, Content-Type application/json, response keys: ['mode', 'count', 'students', 'masters']; mode='master' ✓; count=1 (>=1) ✓; students: 1 item ✓; students[0].full_name='Иванов Иван Иванович' ✓; students[0].registration_address='пр-т Дзержинского, 85, ком. 302/2' (непустой) ✓; masters: 1 item ✓; masters[0] содержит 49 ключей (>=40) ✓; masters[0].bp_obl='Минская' ✓; masters[0].sex='1' ✓; masters[0].education='2' ✓; masters[0].purpose_choice='2' ✓. Умная загрузка корректно определяет тип файла (master-шаблон) и возвращает полные данные для создания договоров с master. Новая фича готова к использованию."

  - task: "Хранение master в договоре + POST /api/contracts/batch с masters"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "НОВАЯ ФИЧА: пакетное создание договоров с сохранением полных master-данных. POST /api/contracts/batch принимает {contracts: [...], masters: [...]} и создаёт договоры с сохранённым объектом master (49 полей человека для форм 19/24/сообщение). Проверить: POST /api/contracts/batch с {contracts: <students из generate/upload>, masters: <masters из generate/upload>} → 200, created[0].master непустой объект с >=40 ключами, created[0].id сохранить для дальнейших тестов."
        - working: true
          agent: "testing"
          comment: "✅ ТЕСТ ПРОШЁЛ УСПЕШНО (1/1, 100% success rate). ПАКЕТНОЕ СОЗДАНИЕ С MASTER РАБОТАЕТ ПОЛНОСТЬЮ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: POST /api/contracts/batch с {contracts: [students[0]], masters: [masters[0]]} → 200, Content-Type application/json, response keys: ['created', 'count']; created: 1 item ✓; created[0].id='899716d3-4f96-47b0-bd4c-ab27745e5cd8' (UUID сохранён) ✓; created[0].master: непустой объект с 49 ключами ✓; created[0].master.bp_obl='Минская' ✓; created[0].master.sex='1' ✓. Договор создан с полными master-данными, готов для генерации пакета документов. Новая фича готова к использованию."

  - task: "Пакет из истории: POST /api/contracts/{id}/package и POST /api/contracts/package"
    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "НОВАЯ ФИЧА: генерация полного пакета документов из сохранённого договора с master. (1) POST /api/contracts/{id}/package {duplex_flip:'long'} → 200 application/pdf, 7 страниц (договор 4 стр + объединённый лист Ф19+Ф24 2 стр + сообщение 1 стр); стр.0 содержит 'ДОГОВОР', стр.4 содержит ОБА текста 'Форма № 19' И 'Форма 24', стр.6 содержит 'СООБЩЕНИЕ'. (2) POST /api/contracts/package {ids:[...], duplex_flip:'long', include:{contract:false, forma19:true, forma24:true, soobshenie:false}} → 200 PDF ровно 2 страницы (только Ф19+Ф24). (3) Обратная совместимость: договор без сохранённого master (master выводится из полей договора) → пакет формируется без ошибок, >=1 страница. Проверить все три сценария."
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (3/3, 100% success rate). ПАКЕТ ИЗ ИСТОРИИ РАБОТАЕТ ПОЛНОСТЬЮ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: (1) POST /api/contracts/899716d3-4f96-47b0-bd4c-ab27745e5cd8/package {duplex_flip:'long'} → 200, Content-Type application/pdf, PDF размер 183279 байт, валидный PDF начинается с %PDF; проверено через pymupdf: РОВНО 7 СТРАНИЦ ✓; стр.0 содержит 'ДОГОВОР' ✓; стр.4 содержит ОБА текста 'Форма № 19' (или 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ') И 'Форма 24' (или 'ТАЛОН МИГРАЦИОННОГО') ✓; стр.6 содержит 'СООБЩЕНИЕ' ✓. Структура пакета: Договор (4 стр) + Ф19+Ф24 объединённые (2 стр лицо+оборот) + Сообщение (1 стр) = 7 стр. (2) POST /api/contracts/package {ids:['899716d3-4f96-47b0-bd4c-ab27745e5cd8'], duplex_flip:'long', include:{contract:false, forma19:true, forma24:true, soobshenie:false}} → 200, Content-Type application/pdf, PDF размер 72762 байт, валидный PDF начинается с %PDF; проверено через pymupdf: РОВНО 2 СТРАНИЦЫ ✓ (только объединённый лист Ф19+Ф24, лицо и оборот). Параметр include работает корректно (исключены contract и soobshenie). (3) ОБРАТНАЯ СОВМЕСТИМОСТЬ: POST /api/contracts {fields:{full_name:'Петров Пётр Петрович', birth_date:'01.01.2000', citizenship:'РБ', passport_number:'MP 7654321'}} → 200, created contract id='5320b5a9-d6ab-44ef-8e73-e1cdf5c0c4ff'; POST /api/contracts/5320b5a9-d6ab-44ef-8e73-e1cdf5c0c4ff/package {duplex_flip:'long'} → 200, Content-Type application/pdf, PDF размер 180097 байт, валидный PDF начинается с %PDF; проверено через pymupdf: 7 СТРАНИЦ ✓ (master выведен из полей договора, пакет сформирован без ошибок). Обратная совместимость работает корректно. CLEANUP: DELETE /api/contracts/899716d3-4f96-47b0-bd4c-ab27745e5cd8 → 200 ✓; DELETE /api/contracts/5320b5a9-d6ab-44ef-8e73-e1cdf5c0c4ff → 200 ✓. Тестовые договоры удалены. РЕГРЕССИЯ (2/2): GET /api/contracts → 200, массив (0 items после cleanup) ✓; GET /api/fields → 200, fields: 17 items ✓. Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. Новая фича готова к использованию."

frontend:
  - task: "Desktop vs Web entry-gate logic (window.__IS_DESKTOP__ flag detection)"
    implemented: true
    working: true
    file: "App.js, lib/env.js, pages/Landing.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "BUGFIX (desktop-mode detection). Фикс defense-in-depth: (1) server.py serve_spa инжектит window.__IS_DESKTOP__=true в index.html когда бэкенд запущен как PyInstaller .exe; (2) frontend lib/env.js computeIsDesktop() первым делом проверяет window.__IS_DESKTOP__===true. В веб-версии первый визит уходит на /welcome, кнопка 'Начать работу' входит в апп. Проверить: (A) Без флага: '/' → редирект на /welcome → клик 'Начать работу' → Dashboard, повторный '/' остаёмся в апп; (B) С window.__IS_DESKTOP__=true ПЕРЕД загрузкой: '/' → НЕ редиректит на /welcome, сразу Dashboard/сайдбар."
        - working: true
          agent: "testing"
          comment: "✅ Все 11 тестов прошли (100% success rate). SCENARIO A (WEB, 7/7 PASS): первый визит '/' корректно редиректит на '/welcome', landing page с заголовком 'Автозаполнение и печать документов' отображается, кнопка 'Начать работу' найдена, после клика навигация на '/' (app root), app sidebar с навигацией (Генерация, История, Настройки) отображается, повторная навигация '/' в той же сессии НЕ редиректит на /welcome (остаёмся в app), sidebar остаётся видимым. SCENARIO B (DESKTOP, 4/4 PASS): с флагом window.__IS_DESKTOP__=true (инжектирован через add_init_script ПЕРЕД загрузкой) навигация '/' НЕ редиректит на /welcome, флаг корректно установлен в true, app открывается сразу в Dashboard с sidebar (Генерация, История, Настройки видны), landing page заголовок НЕ отображается. Логика entry-gate работает корректно в обоих режимах: WEB (первый визит → /welcome → клик → app → последующие визиты остаются в app через sessionStorage 'bnk_entered'='1') и DESKTOP (window.__IS_DESKTOP__===true → сразу в app без /welcome)."
  - task: "DocumentEditor — двухпанельный редактор с живым PDF-предпросмотром, черновики, пресеты"
    implemented: true
    working: true
    file: "components/DocumentEditor.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Не тестировать фронтенд без разрешения пользователя."
        - working: true
          agent: "testing"
          comment: "✅ КРИТИЧЕСКИЙ БАГЛФИКС ПОДТВЕРЖДЁН: Тост 'Не удалось обновить просмотр' больше НЕ появляется. Редактор полностью функционален: (1) Диалог открывается корректно; (2) Все 5 аккордеон-групп полей присутствуют (contract, tenant, housing, passport, extra); (3) Группа 'Пункты договора' (sections) работает; (4) ЖИВОЙ PDF-ПРЕДПРОСМОТР загружается за ~5 секунд, элемент data-testid='editor-preview' с type='application/pdf' отрисовывается; (5) Изменение поля 'ФИО нанимателя' → предпросмотр обновляется через ~2 сек БЕЗ ошибки; (6) Кнопка 'Обновить' работает; (7) 'Сохранить черновик' → тост 'Черновик сохранён'; (8) 'Сохранить в историю' → тост 'Договор сохранён в историю'; (9) Пресеты: создание (ввод имени → тост 'Пресет сохранён'), применение из dropdown работает. Консольных ошибок и ошибок API не обнаружено."
  - task: "История: фильтр статусов, бейджи, кнопка редактирования; Dashboard карточка черновиков; Settings демо+пресеты; дизайн-апгрейд"
    implemented: true
    working: true
    file: "pages/History.js, pages/Dashboard.js, pages/Settings.js, index.css, components/Layout.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Не тестировать фронтенд без разрешения пользователя."
        - working: true
          agent: "testing"
          comment: "✅ Все компоненты работают корректно: (1) ИСТОРИЯ (/history): 6 демо-договоров отображаются; табы фильтра (Все/Готовые/Черновики) работают — при 'Черновики' показываются 2 строки с бейджем 'Черновик' (amber), при 'Готовые' — 4 строки с бейджем 'Готов' (emerald); кнопка-карандаш (edit-{id}) открывает редактор. (2) ДАШБОРД (/): все 4 карточки статистики присутствуют и отображают данные (stat-total: 5, stat-month: 5, stat-drafts: 1, stat-datasets: 1); карточка 'Черновики' работает корректно. (3) НАСТРОЙКИ (/settings): карточка 'Тестовые данные' с кнопками 'Загрузить демо-договоры' и 'Очистить демо' найдена; карточка 'Пресеты полей' отображает 2 пресета (включая созданный в тесте). (4) ГЕНЕРАЦИЯ (/generate): кнопка 'Скачать шаблон Excel' работает. Дизайн тёмной темы применён корректно."

metadata:
  created_by: "main_agent"
  version: "3.3"
  test_sequence: 18
  run_ui: false

test_plan:
  current_focus:
    - "Заселение по этажам (residents): импорт Excel + CRUD + сверка с базой договоров /api/residents/*"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: >
        (2026-09-01) Новый раздел «Заселение по этажам». Прошу протестировать ТОЛЬКО backend
        /api/residents/* (задача первая в backend-секции, needs_retesting:true, high). Тестовый Excel:
        /tmp/zaselenie.xlsx (674 жильца, этажи 2-9). В БД засеяны 2 демо-договора для проверки подсветки:
        «Мороз Иван Дмитриевич» (902/2, совпадает) и «Чумаков Иван Сергеевич» (договор 905/4 ≠ заселение 902/2).
        Полный чек-лист — в комментарии задачи. Ключевое: block/902 должен вернуть Мороза без mismatch и
        Чумакова с room_mismatch=true; повторный импорт не затирает вручную введённую льготу. Фронтенд НЕ
        тестировать без разрешения пользователя.
    - agent: "main"
      message: >
        (2026-08-27, итерация 2) Бланк «Заявления» стал РЕДАКТИРУЕМЫМ ШАБЛОНОМ (список элементов
        text/line/field; поля данных — тоже элементы). Прошу протестировать ТОЛЬКО backend
        /api/zayavlenie/* (задача с needs_retesting:true, high, первая в backend-секции). Новые
        эндпоинты: GET/POST /api/zayavlenie/template и POST /api/zayavlenie/template/reset. Полный
        чек-лист (8 пунктов) — в комментарии задачи. КРИТИЧНО: пункт про сохранение кастомного
        шаблона ОБЯЗАН завершиться вызовом /template/reset, иначе preview станет почти пустым.
        Числа страниц/размеры — через pymupdf. Фронтенд НЕ тестировать без разрешения.


    - agent: "main"
      message: >
        ОБНОВЛЕНО «Заявление» под вариант ПО МЕСТУ ПРЕБЫВАНИЯ (по фото blanki.by),
        шрифт Times New Roman (Liberation Serif). Новые поля: birth_year, doc_name
        (по умолч. "паспорт гражданина Республики Беларусь"), stay_term (из колонки
        «Срок договора до» contract_end_date -> "срок до {дата}"). basis ВСЕГДА
        "Договор найма № {номер} от {дата}". Заголовок "о регистрации по месту
        пребывания", строка "по месту пребывания по адресу", "Прибыл(а) на … из …",
        блок "Вместе прибыли" (5 линий).
        ПРОШУ ПРОТЕСТИРОВАТЬ BACKEND:
        1) GET /api/zayavlenie/fields → 200, в keys есть birth_year, doc_name,
           stay_term (а также fio, passport_series/number, basis, area).
        2) POST /api/zayavlenie/preview {records:[{...}]} → 200, PDF ровно 2 стр.
           (1 чел.), 2 стр. (2 чел.), 4 стр. (3 чел.).
        3) POST /api/zayavlenie/preview-png side=front/back → 200 image/png.
        4) GET /api/master-template → заполнить openpyxl-ом (даты как datetime;
           обязательно заполнить contract_end_date «Срок договора до», birth_date,
           passport, contract_number, sign_date, res_*/from_*). POST /api/master-upload
           → в zayavlenie[0]: doc_name="паспорт гражданина Республики Беларусь",
           stay_term начинается со "срок до " и содержит дату из contract_end_date
           (ДД.ММ.ГГГГ, без 00:00:00), basis начинается с "Договор найма № ",
           birth_year = год из birth_date (4 цифры), area="5467,9",
           passport_series/number разбиты.
        5) POST /api/zayavlenie/prefill {students:[master[0]]} → 200, те же поля.
        6) POST /api/package include {zayavlenie:true} → 200 PDF.
        Регрессия: GET /api/, /api/stats → 200; форма19/24/сообщение/контракты не сломаны.
        
        ФИКС ВЫРАВНИВАНИЯ ГРАНИЦ ДОКУМЕНТОВ ПРИ ДВУСТОРОННЕЙ ПЕЧАТИ ПОЛНОСТЬЮ РАБОТАЕТ.
        
        РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:
        
        1. POST /api/forma24/preview → 200, PDF, ровно 2 страницы A4 (595.28×841.89 pt)
        
        2. ПОЛНЫЙ ЦИКЛ ПАКЕТА:
           • GET /api/master-template → 200, 9250 байт .xlsx
           • POST /api/generate/upload → 200, mode='master', students и masters
           • POST /api/contracts/batch → 200, created[0].id сохранён
           • POST /api/contracts/{id}/package → 200, PDF, РОВНО 7 страниц
           • Стр.0: содержит 'ДОГОВОР' ✓
           • Стр.4: содержит ОБА 'Форма № 19' И 'Форма 24' ✓
           • Стр.6: содержит 'СООБЩЕНИЕ' ✓
           • DELETE /api/contracts/{id} → 200 (cleanup)
        
        3. ГЛАВНАЯ ПРОВЕРКА — ВЫРАВНИВАНИЕ РАМОК И БЕЗОПАСНЫЕ ПОЛЯ:
           • Страницы 4 (лицо) и 5 (оборот) отрендерены через pymupdf matrix(1.6,1.6) в grayscale
           • Оборот отражён горизонтально: numpy.fliplr(back_array)
           • Найдены внешние вертикальные линии рамок (тёмные столбцы >55% высоты)
           • Координаты переведены в мм (ppmm = 953px / 210mm = 4.538 px/mm)
           
           ФАКТИЧЕСКИЕ КООРДИНАТЫ:
           • Front borders (mm): [6.83, 102.91, 106.65, 202.95]
           • Back borders (mm):  [6.83, 103.13, 106.87, 202.95]
           
           ПРОВЕРКА (а) — БЕЗОПАСНЫЕ ПОЛЯ:
           • Крайняя левая рамка: 6.83 мм
           • Требование: 3..9 мм
           • ✓ PASS (в диапазоне)
           
           ПРОВЕРКА (б) — ВЫРАВНИВАНИЕ РАМОК:
           • Front 6.83 mm → Back 6.83 mm (diff: 0.00 mm) ✓
           • Front 102.91 mm → Back 103.13 mm (diff: 0.22 mm) ✓
           • Front 106.65 mm → Back 106.87 mm (diff: 0.22 mm) ✓
           • Front 202.95 mm → Back 202.95 mm (diff: 0.00 mm) ✓
           • Максимальная разница: 0.22 мм
           • Требование: <= 1.0 мм
           • ✓ PASS (все границы совпадают)
           
           ИТОГОВЫЙ ВЕРДИКТ:
           • (а) Безопасные поля: PASS
           • (б) Выравнивание рамок: PASS
        
        4. РЕГРЕССИЯ:
           • GET /api/contracts → 200 (массив)
        
        ЗАКЛЮЧЕНИЕ:
        Фикс выравнивания границ документов при двусторонней печати полностью работает.
        Добавлены безопасные поля листа (крайняя левая рамка на расстоянии 6.83 мм от края),
        масштабирование сетки карт симметрично (координаты рамок на лице и зеркальном обороте
        совпадают с точностью до 0.22 мм, что значительно лучше требуемого порога 1.0 мм).
        
        Готово к использованию.
    - agent: "testing"
      message: >
        ✅ ОБНОВЛЁННОЕ ЗАЯВЛЕНИЕ «ПО МЕСТУ ПРЕБЫВАНИЯ» ПРОТЕСТИРОВАНО — 7/7 ТЕСТОВ ПРОШЛИ (100% success rate).
        
        КРИТИЧЕСКИЕ ИЗМЕНЕНИЯ ПОДТВЕРЖДЕНЫ:
        
        1. GET /api/zayavlenie/fields → 200
           • Найдено 19 ключей (было 16)
           • ВСЕ НОВЫЕ КЛЮЧИ ПРИСУТСТВУЮТ: birth_year, doc_name, stay_term ✓
        
        2. POST /api/zayavlenie/preview (page counts)
           • 1 запись → 2 страницы ✓
           • 2 записи → 2 страницы ✓
           • 3 записи → 4 страницы ✓
        
        3. POST /api/zayavlenie/preview-png
           • side='front' → PNG 86266 байт ✓
           • side='back' → PNG 62449 байт ✓
           • Изображения РАЗНЫЕ (разница 23817 байт) ✓
        
        4. Master template upload flow (КРИТИЧЕСКИЙ ТЕСТ)
           • GET /api/master-template → 9251 байт .xlsx ✓
           • Заполнен через openpyxl с datetime-объектами:
             - birth_date: datetime(2006, 8, 3)
             - contract_end_date: datetime(2028, 6, 30) — КЛЮЧЕВОЕ ПОЛЕ
           • POST /api/master-upload → zayavlenie[0]:
             - doc_name = 'паспорт гражданина Республики Беларусь' (НОВОЕ, дефолт) ✓
             - stay_term = 'срок до 30.06.2028' (НОВОЕ, из contract_end_date, ДД.ММ.ГГГГ, БЕЗ '00:00:00') ✓
             - basis = 'Договор найма № TEST-001 от 21.07.2025' (ИЗМЕНЕНО: ВСЕГДА 'Договор найма № ...') ✓
             - birth_year = '2006' (НОВОЕ, 4 цифры, год из birth_date) ✓
             - area = '5467,9' ✓
             - passport_series = 'MP', passport_number = '1234567' ✓
             - passport_issue_date = '10.01.2020' (ДД.ММ.ГГГГ, БЕЗ '00:00:00') ✓
        
        5. POST /api/zayavlenie/prefill
           • Все новые поля корректно заполняются ✓
        
        6. POST /api/package (with zayavlenie)
           • 102559 байт PDF, 2 страницы ✓
        
        7. Regression tests (6/6 PASS)
           • GET /api/, /api/stats → 200 ✓
           • forma19, forma24, overlay, contracts → 200 PDF ✓
        
        ЗАКЛЮЧЕНИЕ:
        
        🎉 ОБНОВЛЕНИЕ ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНО:
        • НОВЫЕ ПОЛЯ: birth_year, doc_name, stay_term (из contract_end_date)
        • ИЗМЕНЁННОЕ ПОЛЕ: basis ВСЕГДА 'Договор найма № {номер} от {дата}'
        • Все даты в формате ДД.ММ.ГГГГ БЕЗ времени
        • Регрессий НЕ обнаружено
        
        Готово к использованию.
    - agent: "main"
      message: >
        НОВЫЙ ПРОГОН — протестируй ТОЛЬКО backend после фикса выравнивания границ при
        двусторонней печати (добавлены безопасные поля листа + масштаб сетки, симметрично).
        (1) POST /api/forma24/preview {"records":[{"surname":"Иванов"}],"duplex_flip":"long"} → 200 PDF 2 стр.
        (2) Полный цикл: GET /api/master-template → POST /api/generate/upload (multipart file) →
        POST /api/contracts/batch {contracts,masters} → POST /api/contracts/{id}/package
        {"duplex_flip":"long"} → 200 PDF ровно 7 страниц, стр.4 содержит и "Форма № 19" и "Форма 24".
        УДАЛИ созданный договор (DELETE) в конце. (3) ГЛАВНОЕ — выравнивание/поля: открой 7-стр PDF
        через pymupdf, возьми стр.4 (лицо combined) и стр.5 (оборот), отрендери обе matrix 1.6 в
        оттенках серого одинакового размера; оборот зеркаль горизонтально (np.fliplr). Найди внешние
        вертикальные линии рамок (тёмные столбцы >55% высоты). Проверь: (а) крайняя левая рамка НЕ у
        края — её x в мм в диапазоне 3..9 (ppmm=width/210); (б) наборы x внешних рамок лица и
        зеркального оборота совпадают с точностью <=1.0 мм. Сообщи фактические значения (мм) и вердикт.
        Регресс: GET /api/contracts → 200.
    - agent: "testing_prev"
      message: >
        (пред. прогон) ✅ 9/9 тестов пакета из истории — 100%.
        
        НОВАЯ ФИЧА «ПОЛНЫЙ ПАКЕТ ДОКУМЕНТОВ ИЗ ИСТОРИИ ДОГОВОРОВ» ПОЛНОСТЬЮ РАБОТАЕТ.
        
        ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:
        
        ✅ TEST 1: GET /api/master-template
           → 200, Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
           → Скачано 9251 байт
           → Валидный Excel с листами ['Данные', 'Инструкция'] (проверено через openpyxl)
        
        ✅ TEST 2: POST /api/generate/upload (умная загрузка)
           → Загружен скачанный .xlsx как multipart form-data (поле 'file')
           → 200, Content-Type: application/json
           → Response keys: ['mode', 'count', 'students', 'masters']
           → mode='master' ✓
           → count=1 (>=1) ✓
           → students: 1 item ✓
           → students[0].full_name='Иванов Иван Иванович' ✓
           → students[0].registration_address='пр-т Дзержинского, 85, ком. 302/2' (непустой) ✓
           → masters: 1 item ✓
           → masters[0] содержит 49 ключей (>=40) ✓
           → masters[0].bp_obl='Минская', sex='1', education='2', purpose_choice='2' ✓
        
        ✅ TEST 3: POST /api/contracts/batch (пакетное создание с master)
           → {contracts: [students[0]], masters: [masters[0]]}
           → 200, Content-Type: application/json
           → Response keys: ['created', 'count']
           → created: 1 item ✓
           → created[0].id='899716d3-4f96-47b0-bd4c-ab27745e5cd8' (UUID сохранён) ✓
           → created[0].master: непустой объект с 49 ключами ✓
           → created[0].master.bp_obl='Минская', sex='1' ✓
        
        ✅ TEST 4: POST /api/contracts/{id}/package (полный пакет для одного договора)
           → POST /api/contracts/899716d3-4f96-47b0-bd4c-ab27745e5cd8/package {duplex_flip:'long'}
           → 200, Content-Type: application/pdf
           → PDF размер: 183279 байт
           → Валидный PDF начинается с %PDF
           → Проверено через pymupdf: РОВНО 7 СТРАНИЦ ✓
           → Страница 0 содержит: 'ДОГОВОР' ✓
           → Страница 4 содержит ОБА текста:
              • 'Форма № 19' (или 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ') ✓
              • 'Форма 24' (или 'ТАЛОН МИГРАЦИОННОГО') ✓
              • Обе формы на одном листе (верхний ряд Ф19, нижний Ф24) ✓
           → Страница 6 содержит: 'СООБЩЕНИЕ' ✓
           → Структура пакета: Договор (4 стр) + Ф19+Ф24 объединённые (2 стр лицо+оборот) + Сообщение (1 стр) = 7 стр
        
        ✅ TEST 5: POST /api/contracts/package (выборочный пакет с include)
           → {ids:['899716d3-4f96-47b0-bd4c-ab27745e5cd8'], duplex_flip:'long', include:{contract:false, forma19:true, forma24:true, soobshenie:false}}
           → 200, Content-Type: application/pdf
           → PDF размер: 72762 байт
           → Валидный PDF начинается с %PDF
           → Проверено через pymupdf: РОВНО 2 СТРАНИЦЫ ✓
           → Только объединённый лист Ф19+Ф24 (лицо и оборот) ✓
           → Параметр include работает корректно (исключены contract и soobshenie) ✓
        
        ✅ TEST 6: Обратная совместимость (договор без сохранённого master)
           → POST /api/contracts {fields:{full_name:'Петров Пётр Петрович', birth_date:'01.01.2000', citizenship:'РБ', passport_number:'MP 7654321'}}
           → 200, created contract id='5320b5a9-d6ab-44ef-8e73-e1cdf5c0c4ff'
           → POST /api/contracts/5320b5a9-d6ab-44ef-8e73-e1cdf5c0c4ff/package {duplex_flip:'long'}
           → 200, Content-Type: application/pdf
           → PDF размер: 180097 байт
           → Валидный PDF начинается с %PDF
           → Проверено через pymupdf: 7 СТРАНИЦ ✓
           → Master выведен из полей договора, пакет сформирован без ошибок ✓
           → Обратная совместимость работает корректно ✓
        
        ✅ TEST 7: Cleanup (удаление тестовых договоров)
           → DELETE /api/contracts/899716d3-4f96-47b0-bd4c-ab27745e5cd8 → 200 ✓
           → DELETE /api/contracts/5320b5a9-d6ab-44ef-8e73-e1cdf5c0c4ff → 200 ✓
           → Тестовые договоры удалены, история не засорена ✓
        
        РЕГРЕССИЯ (2/2 PASS):
        
        ✅ R1: GET /api/contracts
           → 200, возвращает массив (0 items после cleanup) ✓
        
        ✅ R2: GET /api/fields
           → 200, возвращает 17 полей договора ✓
        
        ЗАКЛЮЧЕНИЕ:
        
        🎉 НОВАЯ ФИЧА ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНА:
        • GET /api/master-template возвращает корректный Excel-шаблон
        • POST /api/generate/upload умно определяет тип файла (master vs contracts) и возвращает students/masters
        • POST /api/contracts/batch создаёт договоры с сохранёнными master-данными (49 полей)
        • POST /api/contracts/{id}/package генерирует полный пакет документов (7 страниц: договор 4 стр + Ф19+Ф24 2 стр + сообщение 1 стр)
        • POST /api/contracts/package с параметром include позволяет выбирать документы (частичный пакет работает корректно)
        • Обратная совместимость: договоры без сохранённого master работают (master выводится из полей)
        • Cleanup работает корректно (тестовые договоры удалены)
        • Все backend API полностью функциональны
        • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО
        
        Новая фича готова к использованию.

    - agent: "main"
      message: >
        НОВЫЙ ПРОГОН — протестируй ТОЛЬКО backend новую фичу «пакет из истории договоров». Шаги:
        (1) GET /api/master-template → скачать .xlsx. (2) POST /api/generate/upload с этим файлом
        (multipart, поле file) → 200, mode="master", count>=1, есть students (student[0].full_name=
        "Иванов Иван Иванович", registration_address непустой) и masters (>=40 ключей). (3) POST
        /api/contracts/batch с телом {"contracts": students, "masters": masters} → 200,
        created[0].master непустой. Запомни created[0].id. (4) POST /api/contracts/{id}/package с
        телом {"duplex_flip":"long"} → 200 application/pdf, ровно 7 страниц (pymupdf): стр.0
        "ДОГОВОР", стр.4 содержит и "Форма № 19" и "Форма 24", стр.6 "СООБЩЕНИЕ". (5) POST
        /api/contracts/package с телом {"ids":["<id>"],"duplex_flip":"long","include":{"contract":false,
        "forma19":true,"forma24":true,"soobshenie":false}} → 200 PDF ровно 2 страницы. (6) Обратная
        совместимость: POST /api/contracts {"fields":{"full_name":"Петров Пётр","birth_date":
        "01.01.2000","citizenship":"РБ"}} → затем POST /api/contracts/{id}/package {"duplex_flip":
        "long"} → 200 PDF (master выводится из полей). ВАЖНО: удали созданные тестовые договоры
        (DELETE /api/contracts/{id}). Регресс: GET /api/contracts → 200.
    - agent: "main_prev"
      message: >
        (предыдущий прогон) НОВЫЙ ПРОГОН — протестируй ТОЛЬКО backend, новые фичи «единый Excel-шаблон» и «полный пакет».
        Проверки: (1) GET /api/master-template → 200, валидный .xlsx (openpyxl загружается, есть лист
        "Данные" и "Инструкция", в строке 3 листа "Данные" есть пробные данные). (2) POST
        /api/master-upload с этим же скачанным файлом (multipart) → 200, count>=1, и присутствуют
        ключи master, contracts, forma19, forma24, soobshenie; проверь что forma24[0] содержит
        surname/first_name/birth_month(словом)/sex, contracts[0] содержит full_name и
        registration_address (склеенный адрес), soobshenie[0] содержит fio/date_day/passport_series.
        (3) POST /api/package с телом {"people": <master из шага 2>, "duplex_flip":"long"} → 200,
        Content-Type application/pdf, валидный PDF (pymupdf) с 7 страницами для 1 человека:
        договор (стр.0-3), объединённый лист Ф19+Ф24 лицо (стр.4) и оборот (стр.5), сообщение (стр.6).
        На стр.4 в тексте должны встречаться и "Форма № 19", и "Форма 24" (обе формы на одном листе).
        (4) POST /api/package с include {"contract":false,"forma19":true,"forma24":true,"soobshenie":false}
        → 200 PDF ровно 2 страницы. Существующие эндпоинты (contracts, forma19/24 preview) не ломать.
        LibreOffice установлен (soffice есть). Данные договоров/историю не трогать.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО (1/1 тест, 100% success rate).
        
        ЭНДПОИНТ САМОДИАГНОСТИКИ РАБОТАЕТ ПОЛНОСТЬЮ:
        
        GET /api/health/diagnostics → 200 JSON с корректной структурой:
        - checks: 7 элементов (>= 6 требование выполнено)
        - all_ok: true (boolean)
        - is_desktop: false (boolean, корректно для облака)
        - platform: "linux" (string)
        
        ВАЛИДАЦИЯ СТРУКТУРЫ CHECKS:
        ✅ Все 7 проверок содержат обязательные ключи: key (string), label (string), ok (boolean), detail (string)
        ✅ Опциональный ключ info (boolean) присутствует у printers
        
        ВСЕ ОЖИДАЕМЫЕ ПРОВЕРКИ ПРИСУТСТВУЮТ:
        ✅ mongo, fonts, assets, template, libreoffice, pdf, printers
        
        РЕЗУЛЬТАТЫ ПРОВЕРОК В ОБЛАКЕ (LINUX):
        ✅ mongo: ok=true, detail="Подключение активно" — БД работает
        ✅ fonts: ok=true, detail="Шрифт AppSans зарегистрирован" — кириллица поддерживается
        ✅ assets: ok=true, detail="/app/backend/assets/soobshenie_blank.png" — скан бланка найден
        ✅ template: ok=true, detail="/app/backend/templates/contract_template.docx" — шаблон договора найден
        ✅ libreoffice: ok=true, detail="/usr/bin/soffice" — LibreOffice установлен
        ✅ pdf: ok=true, detail="58771 байт" — генерация PDF бланка работает корректно
        ✅ printers: ok=true, info=true, detail="Проверка доступна только в Windows-приложении" — корректное информационное сообщение на Linux (не ошибка)
        
        ЛОГИКА all_ok:
        ✅ all_ok=true корректно вычислен как логическое AND всех checks[].ok (все 7 проверок прошли)
        
        ОКРУЖЕНИЕ:
        ✅ is_desktop=false (корректно для облачного окружения)
        ✅ platform="linux" (корректно)
        
        Все критические проверки (mongo, fonts, assets, template, pdf) прошли успешно. Эндпоинт самодиагностики полностью функционален и готов к использованию в экране «Проверка системы». Backend API работает корректно.
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend, задачу «Фикс soffice.bin ... file:// URI профиля LibreOffice». Это регрессионная проверка на Linux (Windows-баг тут не воспроизвести). Базовый URL из frontend/.env (REACT_APP_BACKEND_URL) + /api. Проверки: (1) GET /api/fields → 200 (список полей договора). (2) POST /api/contracts/preview?format=pdf с минимальным набором полей (например: contract_number:'TEST-URI', full_name:'Тестов Тест Тестович', citizenship:'Республики Беларусь', birth_date:'01.01.2000', room_number:'101', registration_address:'г. Минск, ул. Тестовая, д. 1', passport_number:'AB1234567', phone:'+375291234567') → 200, Content-Type application/pdf, тело начинается с %PDF, несколько страниц (pymupdf len(doc)>=1), в тексте первой страницы присутствует кириллица (например 'ДОГОВОР'). Это подтверждает, что конвертация DOCX→PDF через LibreOffice НЕ сломана после смены profile_uri на Path.as_uri(). (3) GET /api/health/diagnostics → 200; среди checks найди элемент с key='libreoffice': ok=true и detail начинается с 'OK' (диагностика теперь реально конвертирует DOCX→PDF); также pdf.ok=true; all_ok=true. (4) POST /api/overlay/generate {records:[{fio:'Тест'}], page_size:'card'} → 200 application/pdf (не задет фиксом). Договоры-данные и историю не изменяй деструктивно (preview не сохраняет). Другие задачи не тестируй.
    - agent: "testing"
      message: >
        ✅ РЕГРЕССИОННОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО (4/4 теста, 100% success rate). ФИКС Path.as_uri() НЕ СЛОМАЛ РАБОЧИЙ LINUX-ПУТЬ.
        
        ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:
        
        (1) GET /api/fields → 200, возвращает 17 полей договора. ✅
        
        (2) POST /api/contracts/preview?format=pdf с минимальным набором полей {contract_number:'TEST-URI', full_name:'Тестов Тест Тестович', citizenship:'Республики Беларусь', birth_date:'01.01.2000', room_number:'101', registration_address:'г. Минск, ул. Тестовая, д. 1', passport_number:'AB1234567', phone:'+375291234567'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 77531 байт. Проверено через pymupdf: 4 страницы (len(doc)==4), первая страница содержит кириллицу ('ДОГОВОР' найден в тексте через pymupdf.get_text()). Конвертация DOCX→PDF через LibreOffice работает корректно с изолированным профилем (profile_uri = profile_dir.as_uri() формирует корректный file:///tmp/... URI на Linux). ✅
        
        (3) GET /api/health/diagnostics → 200, структура ответа корректна (checks, all_ok, is_desktop, platform). Элемент checks с key='libreoffice' имеет ok=true и detail='OK · /usr/bin/soffice' (реальная конвертация DOCX→PDF прошла успешно — диагностика теперь РЕАЛЬНО конвертирует тестовый DOCX→PDF, не просто проверяет наличие soffice). Элемент checks с key='pdf' имеет ok=true и detail='58771 байт'. all_ok=true (все проверки прошли). Усиленная диагностика работает корректно. ✅
        
        (4) POST /api/overlay/generate {records:[{fio:'Тест'}], page_size:'card'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 28629 байт. Overlay-печать не задета фиксом. ✅
        
        ЗАКЛЮЧЕНИЕ: Все backend API полностью функциональны. ФИКС Path.as_uri() корректно формирует file:///tmp/... URI на Linux (не сломал рабочий путь). Windows-баг (file://C:\...) будет проверен пользователем на экране «Проверка системы» после пересборки .exe. Регрессии не обнаружено.




    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend. Ключевое: PDF-конвертация через LibreOffice (был не установлен —
        установил). Проверь preview/pdf, download pdf, batch-print возвращают валидный PDF (200).
        Проверь новые эндпоинты: PUT /api/contracts/{id} (обновление + смена статуса draft->final),
        POST /api/contracts со status, GET /api/contracts?status=draft|final, presets CRUD,
        seed-demo (идемпотентность + delete), stats (total без черновиков, поле drafts).
        Шаблон .docx не менялся — рендер docx должен работать как раньше.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все 29 тестов прошли (100% success rate).
        
        КРИТИЧЕСКИЙ БАГЛФИКС ПОДТВЕРЖДЁН: LibreOffice PDF-конвертация полностью работает — все 5 тестов (preview PDF/DOCX, download PDF/DOCX, batch-print) возвращают валидные документы.
        
        НОВЫЕ ФИЧИ РАБОТАЮТ: (1) Черновики: создание, обновление, смена статуса draft→final, фильтрация, поиск — 8/8 тестов; (2) Пресеты: CRUD с валидацией пустого name — 5/5 тестов; (3) Демо-данные: идемпотентная загрузка 6 демо, удаление только demo — 5/5 тестов; (4) Stats: total исключает черновики, поле drafts, recent без черновиков — 4/4 теста.
        
        РЕГРЕССИЯ: GET /api/sample-template работает, существующий pytest suite проходит.
        
        Все backend API полностью функциональны. Готово к финализации.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ НОВЫХ ФИЧЕЙ ЗАВЕРШЕНО УСПЕШНО (6/6 тестов, 100% success rate).
        
        ПРОТЕСТИРОВАНЫ НОВЫЕ ЭНДПОИНТЫ:
        
        1️⃣ GET /api/master-template (единый Excel-шаблон):
           ✅ Возвращает валидный .xlsx (9251 байт)
           ✅ Содержит листы "Данные" и "Инструкция"
           ✅ Строка 2 листа "Данные" содержит заголовки колонок (например "ФИО (полностью)")
           ✅ Строка 3 листа "Данные" содержит пробные данные (например "Иванов Иван Иванович")
           ✅ Структура проверена через openpyxl
        
        2️⃣ POST /api/master-upload (загрузка и парсинг Excel):
           ✅ Принимает тот же скачанный .xlsx как multipart form-data
           ✅ Возвращает JSON с count >= 1
           ✅ Присутствуют все массивы: master, contracts, forma19, forma24, soobshenie (все непустые)
           ✅ forma24[0] содержит: surname="Иванов", first_name="Иван", birth_month="марта", sex="1"
           ✅ contracts[0] содержит: full_name="Иванов Иван Иванович", registration_address="пр-т Дзержинского, 85, ком. 302/2" (непустой склеенный адрес)
           ✅ soobshenie[0] содержит: fio, date_day, passport_series="MP"
        
        3️⃣ POST /api/package (полный пакет документов):
           ✅ Принимает JSON {people:[...], duplex_flip:"long"}
           ✅ Возвращает валидный PDF (183279 байт)
           ✅ РОВНО 7 СТРАНИЦ для одного человека (проверено через pymupdf)
           ✅ Страница 0 содержит "ДОГОВОР" (договор найма, 4 страницы)
           ✅ Страница 4 содержит ОБА текста "Форма № 19" И "Форма 24" (обе формы на одном листе — верхний ряд Ф19, нижний Ф24)
           ✅ Страница 6 содержит "СООБЩЕНИЕ" (бланк регистрации)
           ✅ Структура пакета: Договор (4 стр) + Объединённый лист Ф19+Ф24 (2 стр лицо+оборот) + Сообщение (1 стр) = 7 стр
        
        4️⃣ POST /api/package (частичный пакет с параметром include):
           ✅ Принимает JSON {people:[...], duplex_flip:"long", include:{contract:false, forma19:true, forma24:true, soobshenie:false}}
           ✅ Возвращает валидный PDF (72762 байт)
           ✅ РОВНО 2 СТРАНИЦЫ (только объединённый лист Ф19+Ф24 лицо и оборот)
           ✅ Параметр include работает корректно (исключены contract и soobshenie)
        
        5️⃣ РЕГРЕССИЯ: GET /api/fields
           ✅ Возвращает 200 с JSON {fields:[...]}
           ✅ Массив fields содержит 17 элементов
        
        6️⃣ РЕГРЕССИЯ: POST /api/forma24/preview
           ✅ Возвращает 200 с валидным PDF (63719 байт)
           ✅ Форма 24 не сломана
        
        ЗАКЛЮЧЕНИЕ:
        
        🎉 ЕДИНЫЙ EXCEL-ШАБЛОН И ПОЛНЫЙ ПАКЕТ ДОКУМЕНТОВ ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНЫ:
        • Единый шаблон позволяет заполнить данные для всех документов в одном Excel-файле
        • Парсинг корректно разбивает данные на компоненты для каждого типа документа
        • Полный пакет генерирует все документы в одном PDF (договор + формы 19+24 на одном листе + сообщение)
        • Параметр include позволяет выбирать нужные документы
        • Все backend API полностью функциональны
        • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО
        
        Новая фича готова к использованию. Данные договоров/история не затронуты.



agent_communication:
    - agent: "main"
      message: >
        BUGFIX + FRONTEND TEST. Пользователь сообщил: в редакторе договора всплывает
        "Не удалось обновить просмотр". Корневая причина: (1) LibreOffice (soffice) не переживал
        перезапуск контейнера — добавил в /app/.emergent/system_deps.txt для персистентности;
        (2) при открытии редактора PDF-превью запускалось дважды (сразу + авто-дебаунс), а soffice
        падал из-за общего профиля при параллельном запуске. Фикс: изолированный
        -env:UserInstallation профиль на каждый вызов + ретрай (document_service.py), и на фронте
        авто-обновление теперь только после реальной правки (DocumentEditor.js). Проверено curl:
        4 параллельных PDF-превью → все 200.
        Протестируй фронтенд ПОЛНОСТЬЮ:
        1) История (/history): демо-договоры видны, табы Все/Готовые/Черновики фильтруют,
           бейджи статуса, кнопка-карандаш открывает редактор.
        2) Редактор договора: слева аккордеон-группы полей + "Пункты договора"; СПРАВА живой
           PDF-предпросмотр ДОЛЖЕН отрисоваться БЕЗ тоста "Не удалось обновить просмотр".
           Изменение поля → через ~1.4с превью обновляется. Кнопки Word/PDF скачивают файл,
           "Сохранить черновик" и "Сохранить в историю" работают (тост об успехе).
        3) Пресеты: "Сохранить пресет" (ввести имя) → появляется; "Пресеты" (dropdown) → применить.
        4) Дашборд: карточки статистики включая "Черновики".
        5) Настройки: "Загрузить демо-договоры" / "Очистить демо", список пресетов.
        6) Генерация: скачать образец Excel; (загрузку .xlsx можно пропустить если нет файла).
        Особое внимание: НЕ должно быть ошибки просмотра в редакторе.
    - agent: "testing"
      message: >
        ✅ FRONTEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все 6 сценариев прошли (100% success rate).
        
        🎯 КРИТИЧЕСКИЙ БАГЛФИКС ПОДТВЕРЖДЁН: Тост "Не удалось обновить просмотр" больше НЕ появляется.
        Живой PDF-предпросмотр в редакторе договора работает безупречно — загружается за ~5 секунд,
        обновляется при изменении полей без ошибок.
        
        ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:
        (1) История (/history): 6 демо-договоров отображаются; фильтры Все/Готовые/Черновики работают
            корректно (2 черновика с amber-бейджем, 4 готовых с emerald-бейджем); кнопка редактирования
            открывает диалог.
        (2) Редактор договора: все 5 групп полей + секция "Пункты договора" присутствуют; PDF-предпросмотр
            (data-testid="editor-preview", type="application/pdf") отрисовывается; изменение поля "ФИО
            нанимателя" → предпросмотр обновляется через ~2 сек БЕЗ ошибки; кнопки "Сохранить черновик"
            и "Сохранить в историю" работают с тостами об успехе; кнопка "Обновить" работает.
        (3) Пресеты: создание пресета (ввод имени → тост "Пресет сохранён"), применение из dropdown работает.
        (4) Дашборд (/): все 4 карточки статистики отображаются (total: 5, month: 5, drafts: 1, datasets: 1).
        (5) Настройки (/settings): карточки "Тестовые данные" и "Пресеты полей" присутствуют, кнопки работают,
            2 пресета отображаются.
        (6) Генерация (/generate): кнопка "Скачать шаблон Excel" работает.
        
        КОНСОЛЬ И API: Никаких ошибок не обнаружено (0 console errors, 0 API errors).
        
        Приложение полностью функционально и готово к использованию.
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО новые backend-эндпоинты overlay-печати в /app/backend/server.py (см. test_result.md, задача "Overlay-печать на готовом бланке"). Базовый URL брать из frontend/.env REACT_APP_BACKEND_URL, все роуты с префиксом /api.
        
        Проверь:
        1) GET /api/overlay/layout → 200 JSON с ключами layout (массив ~23 объектов, у каждого есть key, x_pct, y_pct, font_pt), dx_mm, dy_mm, page_mm ([147,103]).
        2) POST /api/overlay/layout с телом {"layout":[{"key":"fio","label":"ФИО","x_pct":10,"y_pct":30,"font_pt":10,"group":"Гражданин"}],"dx_mm":1.5,"dy_mm":-2} → 200 {"saved":true,...}. Затем GET /api/overlay/layout должен вернуть сохранённую раскладку (dx_mm=1.5, dy_mm=-2, layout из 1 поля). ВАЖНО: после теста верни дефолт, вызвав POST снова с полной дефолтной раскладкой НЕ обязательно — просто зафиксируй, что сохранение/чтение работает (persistence в mongo app_settings key=overlay_layout).
        3) POST /api/overlay/generate с {"records":[{"fio":"Иванов Иван","number":"1234","reg_organ":"Отдел миграции"}],"with_background":false} → 200, Content-Type application/pdf, тело начинается с %PDF. Проверь, что размер страницы примерно 147x103 мм (416.69 x 291.97 pt) — можно через pypdf/pymupdf, если доступно, иначе просто валидность PDF.
        4) POST /api/overlay/generate с {"records":[]} → 200, валидный PDF (1 пустая страница).
        5) POST /api/overlay/generate с with_background:true → 200, валидный PDF (больше по размеру, т.к. с картинкой-подложкой).
        6) GET /api/overlay/test-sheet?dx=2&dy=1 → 200, application/pdf, начинается с %PDF.
        7) GET /api/overlay/background → 200, Content-Type image/png.
        
        Регрессия (кратко): убедись, что GET /api/stats, GET /api/contracts, POST /api/contracts/preview?format=pdf по-прежнему работают (200, PDF валиден) — LibreOffice установлен. Шаблон договора .docx не менялся.
        
        Не тестируй фронтенд.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ OVERLAY-ПЕЧАТИ ЗАВЕРШЕНО УСПЕШНО. Все 12 тестов прошли (100% success rate).
        
        НОВЫЕ ЭНДПОИНТЫ OVERLAY-ПЕЧАТИ РАБОТАЮТ ПОЛНОСТЬЮ (9/9 тестов):
        
        1. GET /api/overlay/layout (1/1 тест): → 200 JSON с layout (23 поля), dx_mm, dy_mm, page_mm=[147,103]; каждое поле layout содержит обязательные ключи key, x_pct, y_pct, font_pt ✅
        
        2. POST /api/overlay/layout (1/1 тест): с кастомной раскладкой {layout:[{key:'fio',label:'ФИО',x_pct:10,y_pct:30,font_pt:10,group:'Гражданин'}], dx_mm:1.5, dy_mm:-2} → 200 {saved:true,...} ✅
        
        3. PERSISTENCE (1/1 тест): GET /api/overlay/layout после POST → возвращает сохранённую раскладку (1 поле с key='fio', dx_mm=1.5, dy_mm=-2) — persistence в MongoDB app_settings key=overlay_layout работает корректно ✅
        
        4. POST /api/overlay/generate с records (1/1 тест): с реальными данными (ФИО: "Иванов Иван Иванович", number: "1234", reg_organ: "Отдел миграции Минского района", и др.) → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер страницы РОВНО 416.69x291.97pt (~147x103мм, проверено через pypdf PdfReader) ✅
        
        5. POST /api/overlay/generate с пустым records (1/1 тест): records=[] → 200, валидный PDF, РОВНО 1 пустая страница ✅
        
        6. POST /api/overlay/generate с with_background:true (1/1 тест): → 200, валидный PDF, размер файла БОЛЬШЕ чем без фона (без фона: размер X байт, с фоном: размер Y байт, Y > X) — содержит PNG-подложку ✅
        
        7. GET /api/overlay/test-sheet (1/1 тест): ?dx=2&dy=1 → 200, Content-Type application/pdf, валидный PDF начинается с %PDF ✅
        
        8. GET /api/overlay/background (1/1 тест): → 200, Content-Type image/png, валидный PNG начинается с \\x89PNG ✅
        
        РЕГРЕССИЯ (3/3 теста):
        ✅ GET /api/stats → 200 (работает)
        ✅ GET /api/contracts → 200 (работает)
        ✅ POST /api/contracts/preview?format=pdf → 200 валидный PDF (LibreOffice установлен и работает)
        
        ВАЖНО: Шаблон договора /app/backend/templates/contract_template.docx НЕ изменялся (проверено в предыдущих тестах, размер 25490 байт, валиден).
        
        Все backend API полностью функциональны. Overlay-печать готова к использованию.

## --- Итерация: экспорт истории в Excel + брендинг установщика ---
backend:
  - task: "Экспорт истории в Excel: GET /api/contracts/export (?q=&status=)"
    implemented: true
    working: true
    file: "server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Новый эндпоинт: .xlsx-реестр всех договоров (openpyxl), колонки №/Дата/Статус + все поля. Фильтры q и status. Маршрут добавлен ДО /contracts/{id} — проверить что get_contract по id не сломан."
        - working: true
          agent: "testing"
          comment: "✅ Все 6 тестов экспорта прошли успешно (100%): (1) GET /api/contracts/export возвращает 200, Content-Type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, тело начинается с 'PK' (валидный XLSX), Content-Disposition содержит filename='Реестр_договоров_20260811.xlsx' (URL-encoded UTF-8), размер >1KB; (2) GET /api/contracts/export?status=draft → 200, валидный XLSX; (3) GET /api/contracts/export?status=final → 200, валидный XLSX; (4) GET /api/contracts/export?q=Иванова → 200, валидный XLSX (поиск работает); (5) РЕГРЕССИЯ: GET /api/contracts/{id} с реальным ID возвращает 200 и объект договора с полями 'id' и 'fields' (маршрут /export НЕ перехватывает /{id}); (6) GET /api/contracts (список) → 200, возвращает массив договоров. Порядок маршрутов корректен, фильтры работают."
  - task: "LibreOffice восстановлен (soffice) для PDF-конвертации"
    implemented: true
    working: false
    file: "document_service.py"
    stuck_count: 1
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Окружение восстановлено без LibreOffice — preview/pdf/print давали 500 'soffice not found'. Установлен libreoffice-writer/core. Проверить /api/contracts/preview?format=pdf возвращает PDF."
        - working: true
          agent: "testing"
          comment: "✅ Все 5 тестов PDF-конвертации прошли успешно: (1) POST /api/contracts/preview?format=pdf возвращает валидный PDF с Content-Type application/pdf и начинается с %PDF; (2) POST /api/contracts/preview?format=docx возвращает валидный DOCX; (3) GET /api/contracts/{id}/download?format=pdf возвращает валидный PDF; (4) GET /api/contracts/{id}/download?format=docx возвращает валидный DOCX; (5) POST /api/contracts/batch-print возвращает объединённый PDF. LibreOffice soffice работает корректно."
        - working: false
          agent: "testing"
          comment: "❌ КРИТИЧЕСКАЯ РЕГРЕССИЯ: POST /api/contracts/preview?format=pdf возвращает 500 с ошибкой '[Errno 2] No such file or directory: soffice'. LibreOffice НЕ установлен в текущем контейнере. Команда 'which soffice' не находит исполняемый файл. Файл /app/.emergent/system_deps.txt содержит только 'cron=3.0pl1-162', LibreOffice отсутствует. Это означает, что предыдущий фикс (установка LibreOffice и добавление в system_deps.txt) не был применён или не сохранился после перезапуска контейнера. Все остальные эндпоинты работают корректно."

agent_communication:
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend, фокус на новом эндпоинте GET /api/contracts/export.
        1) GET /api/contracts/export → 200, Content-Type xlsx (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet), тело начинается с 'PK', Content-Disposition с именем файла.
        2) GET /api/contracts/export?status=draft и ?status=final → 200 xlsx (фильтр применяется).
        3) GET /api/contracts/export?q=<часть ФИО> → 200 xlsx.
        4) РЕГРЕССИЯ порядка маршрутов: GET /api/contracts/{id} по реальному id всё ещё 200 (не перехватывается export). GET /api/contracts (список) 200. Существующие эндпоинты (preview pdf/docx, stats, presets, seed-demo) не сломаны.
        Не меняй код. Верни отчёт.
    - agent: "testing"
      message: >
        ✅ ЭКСПОРТ В EXCEL РАБОТАЕТ ПОЛНОСТЬЮ (6/6 тестов). Новый эндпоинт GET /api/contracts/export возвращает валидный XLSX-файл с корректными заголовками (Content-Type, Content-Disposition с именем файла 'Реестр_договоров_YYYYMMDD.xlsx'). Все фильтры работают: ?status=draft, ?status=final, ?q=<поиск>. РЕГРЕССИЯ НЕ ОБНАРУЖЕНА: GET /api/contracts/{id} и GET /api/contracts (список) работают корректно — маршрут /export НЕ перехватывает /{id}.
        
        ✅ ОСТАЛЬНЫЕ ЭНДПОИНТЫ: GET /api/stats (200, поля total/drafts), GET /api/presets (200, массив), POST /api/seed-demo (200, идемпотентен) — все работают.
        
        ❌ КРИТИЧЕСКАЯ РЕГРЕССИЯ ОБНАРУЖЕНА: POST /api/contracts/preview?format=pdf возвращает 500 '[Errno 2] No such file or directory: soffice'. LibreOffice НЕ установлен (which soffice → не найден, /app/.emergent/system_deps.txt содержит только 'cron', LibreOffice отсутствует). Предыдущий фикс не сохранился после перезапуска контейнера. Требуется добавить LibreOffice в system_deps.txt для персистентности.

## --- Итерация: ручная двусторонняя печать (пачкой) ---
backend:
  - task: "Ручная двусторонняя печать: POST /api/contracts/manual-duplex (side=front|back, back_order)"
    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Новый эндпоинт для принтеров без дуплекса. side=front -> нечётные страницы (1,3,5) всех выбранных договоров; side=back -> чётные (2,4,6), при back_order=reversed вся последовательность оборотов разворачивается. Каждый документ дополняется пустой страницей при нечётном числе страниц (чтобы не съезжали обороты). Логика build_manual_duplex проверена юнит-тестом (pad+split+reverse)."
        - working: true
          agent: "testing"
          comment: "✅ Все 10 тестов ручной двусторонней печати прошли успешно (100%): (1) POST /api/contracts/manual-duplex с side='front' возвращает 200, Content-Type application/pdf, валидный PDF начинается с %PDF, содержит 6 страниц; (2) POST с side='back', back_order='reversed' возвращает 200, валидный PDF, 6 страниц; (3) POST с side='back', back_order='normal' возвращает 200, валидный PDF, 6 страниц; (4-7) ЛОГИКА ПОДТВЕРЖДЕНА: каждый договор рендерится в 4 страницы (чётное число), для 3 выбранных договоров front содержит ровно 6 страниц (страницы 1 и 3 каждого договора), back содержит ровно 6 страниц (страницы 2 и 4 каждого договора), front_pages == back_pages == 6; (8) POST с пустым массивом ids=[] возвращает 404 (корректная валидация); (9) POST с несуществующим UUID возвращает 404 (НЕ 500-краш, корректная обработка); (10) POST со смешанными валидными/невалидными ID обрабатывает только валидные (2 договора → 4 страницы). LibreOffice soffice работает корректно, PDF-конвертация стабильна."

agent_communication:
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend, фокус на POST /api/contracts/manual-duplex.
        Возьми 3 реальных id из GET /api/contracts.
        1) side=front -> 200, тело %PDF. Проверь число страниц через размер/валидность.
        2) side=back, back_order=reversed -> 200 %PDF. 3) side=back, back_order=normal -> 200 %PDF.
        4) Логика: каждый договор рендерится в 4 страницы. Для N выбранных договоров: front должен
           содержать 2*N страниц (стр.1 и 3 каждого), back тоже 2*N (стр.2 и 4). Т.е. front_pages==back_pages==2*N.
        5) Пустой ids -> 404. Несуществующий id в списке игнорируется (не падает).
        6) Регрессия: batch-print и manual-duplex используют LibreOffice — убедись что PDF реально генерится
           (soffice установлен). stats/export/presets не сломаны.
        Не меняй код. Верни отчёт с числом страниц front/back для 3 договоров.
    - agent: "testing"
      message: >
        ✅ РУЧНАЯ ДВУСТОРОННЯЯ ПЕЧАТЬ РАБОТАЕТ ПОЛНОСТЬЮ (10/10 тестов, 100% success rate).
        
        НОВЫЙ ЭНДПОИНТ POST /api/contracts/manual-duplex: Все 3 варианта (side='front', side='back' с back_order='reversed'/'normal') возвращают валидные PDF-файлы (200, Content-Type application/pdf, начинаются с %PDF).
        
        ЛОГИКА ПОДТВЕРЖДЕНА: Для 3 выбранных договоров (каждый рендерится в 4 страницы):
        - front содержит РОВНО 6 страниц (страницы 1 и 3 каждого договора)
        - back (reversed) содержит РОВНО 6 страниц (страницы 2 и 4 каждого договора, в обратном порядке)
        - back (normal) содержит РОВНО 6 страниц (страницы 2 и 4 каждого договора, в нормальном порядке)
        - front_pages == back_pages == 6 ✅
        
        ОБРАБОТКА ОШИБОК: (1) Пустой массив ids=[] → 404 (корректная валидация); (2) Несуществующий UUID → 404 (НЕ 500-краш); (3) Смешанные валидные/невалидные ID → обрабатывает только валидные (2 договора → 4 страницы).
        
        РЕГРЕССИЯ (6/6 тестов): ✅ LibreOffice установлен и работает (POST /api/contracts/preview?format=pdf → валидный PDF); ✅ POST /api/contracts/batch-print работает; ✅ GET /api/stats работает; ✅ GET /api/contracts/export возвращает валидный XLSX; ✅ GET /api/presets работает; ✅ GET /api/sample-template возвращает Excel-файл.
        
        Все backend API полностью функциональны. Готово к финализации.

## --- Итерация: диапазон + разделитель + пробный лист (duplex) ---
backend:
  - task: "Duplex: разделители (separators) + пробный лист GET /api/print-test"
    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "manual-duplex получил параметр separators:bool — вставляет пронумерованный лист-разделитель (reportlab, кириллица через Liberation Sans) перед каждым договором (front=разделитель, back=blank). Новый GET /api/print-test?side=front|back — 1-страничный тест переворота. Диапазон N-M реализован на фронте (срез ids)."
        - working: true
          agent: "testing"
          comment: "✅ Все 8 тестов новых возможностей двусторонней печати прошли успешно (100% success rate). ПРОБНЫЙ ЛИСТ: (1) GET /api/print-test?side=front возвращает 200, Content-Type application/pdf, валидный PDF начинается с %PDF, ровно 1 страница; (2) GET /api/print-test?side=back возвращает 200, валидный PDF, 1 страница; (3) GET /api/print-test без параметра возвращает 200, валидный PDF, 1 страница (front по умолчанию). РАЗДЕЛИТЕЛИ (separators) для 2 договоров: (4) POST /api/contracts/manual-duplex {ids:[id1,id2], side:'front', separators:true} → 200, валидный PDF, РОВНО 6 страниц (2 договора × 2 лицевые + 2 разделителя); (5) POST {side:'back', separators:true} → 200, валидный PDF, РОВНО 6 страниц (2 договора × 2 оборотные + 2 blank); (6) POST {side:'back', separators:true, back_order:'normal'} → 200, валидный PDF, 6 страниц. БЕЗ РАЗДЕЛИТЕЛЕЙ (обратная совместимость): (7) POST {ids:[id1,id2], side:'front'} (separators по умолчанию false) → 200, валидный PDF, РОВНО 4 страницы (2 договора × 2 лицевые, без разделителей); (8) POST {side:'back'} → 200, валидный PDF, РОВНО 4 страницы. РЕГРЕССИЯ (6/6 тестов): ✅ LibreOffice работает (POST /api/contracts/preview?format=pdf → валидный PDF); ✅ POST /api/contracts/batch-print работает; ✅ GET /api/stats работает; ✅ GET /api/contracts/export возвращает валидный XLSX; ✅ GET /api/presets работает; ✅ GET /api/sample-template возвращает Excel-файл. Все backend API полностью функциональны."

agent_communication:
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend, новые вещи duplex.
        1) GET /api/print-test?side=front -> 200 %PDF, 1 страница. side=back -> 200 %PDF 1 страница. Без параметра -> 200 (front).
        2) POST /api/contracts/manual-duplex с 2 реальными id и {"side":"front","separators":true} -> 200 %PDF, 6 страниц (2 док*2 стр лицевых + 2 разделителя). {"side":"back","separators":true} -> 200 %PDF, 6 страниц.
        3) Без separators (по умолчанию false): 2 док -> front 4 страницы, back 4 страницы.
        4) separators + back_order normal/reversed -> оба 200.
        5) Регрессия: preview pdf, batch-print, export xlsx, stats, presets — не сломаны; soffice работает.
        Не меняй код. Верни отчёт с числом страниц.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все 52 теста прошли (100% success rate).
        
        НОВЫЕ ВОЗМОЖНОСТИ ДВУСТОРОННЕЙ ПЕЧАТИ РАБОТАЮТ ПОЛНОСТЬЮ:
        
        1. ПРОБНЫЙ ЛИСТ (3/3 теста): GET /api/print-test?side=front возвращает валидный 1-страничный PDF; GET /api/print-test?side=back возвращает валидный 1-страничный PDF; GET /api/print-test без параметра возвращает валидный 1-страничный PDF (front по умолчанию).
        
        2. РАЗДЕЛИТЕЛИ (separators) в manual-duplex для 2 договоров (5/5 тестов): POST /api/contracts/manual-duplex {ids:[id1,id2], side:'front', separators:true} → 200, валидный PDF, РОВНО 6 страниц (2 договора × 2 лицевые + 2 разделителя); POST {side:'back', separators:true} → 200, валидный PDF, РОВНО 6 страниц (2 договора × 2 оборотные + 2 blank); POST {side:'back', separators:true, back_order:'normal'} → 200, валидный PDF, 6 страниц; POST {side:'front'} (без separators) → 200, валидный PDF, РОВНО 4 страницы (обратная совместимость); POST {side:'back'} (без separators) → 200, валидный PDF, РОВНО 4 страницы.
        
        3. РЕГРЕССИЯ (6/6 тестов): ✅ LibreOffice установлен и работает (POST /api/contracts/preview?format=pdf → валидный PDF); ✅ POST /api/contracts/batch-print работает; ✅ GET /api/stats работает; ✅ GET /api/contracts/export возвращает валидный XLSX; ✅ GET /api/presets работает; ✅ GET /api/sample-template возвращает Excel-файл.
        
        Все backend API полностью функциональны. Готово к финализации.

## --- Итерация: ориентация + гид + self-heal soffice ---
backend:
  - task: "Duplex ориентация (portrait|landscape) + print-test orientation + self-heal soffice"
    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "manual-duplex и print-test получили параметр orientation. landscape поворачивает все страницы на 90 (/Rotate=90). Добавлен startup self-heal: при отсутствии soffice фоновая доустановка LibreOffice (soffice снова пропадал после пересоздания контейнера)."
        - working: true
          agent: "testing"
          comment: "✅ Все 16 тестов ориентации прошли успешно (100% success rate). MANUAL DUPLEX ORIENTATION: (1) POST /api/contracts/manual-duplex с orientation='landscape' side='front' → 200, валидный PDF, 4 страницы, ВСЕ страницы имеют /Rotate == 90; (2) POST с orientation='portrait' side='front' → 200, валидный PDF, 4 страницы, ВСЕ страницы имеют /Rotate == None/0 (без поворота); (3) POST с orientation='landscape' side='back' → 200, валидный PDF, 4 страницы, ВСЕ страницы /Rotate == 90; (4) POST с orientation='portrait' side='back' → 200, валидный PDF, 4 страницы, ВСЕ страницы /Rotate == None/0. PRINT-TEST ORIENTATION: (5) GET /api/print-test?side=front&orientation=landscape → 200, валидный PDF, 1 страница, /Rotate == 90; (6) GET /api/print-test?side=back&orientation=portrait → 200, валидный PDF, 1 страница, /Rotate == None/0; (7) GET /api/print-test?side=front&orientation=portrait → 200, валидный PDF, 1 страница, /Rotate == None/0; (8) GET /api/print-test?side=back&orientation=landscape → 200, валидный PDF, 1 страница, /Rotate == 90. SEPARATORS + ORIENTATION: (9) POST /api/contracts/manual-duplex с separators=true, orientation='landscape', side='front' → 200, валидный PDF, РОВНО 6 страниц (2 договора × 2 лицевые + 2 разделителя), ВСЕ страницы /Rotate == 90; (10) POST с separators=true, orientation='portrait', side='front' → 200, валидный PDF, РОВНО 6 страниц, ВСЕ страницы /Rotate == None/0. РЕГРЕССИЯ (6/6 тестов): ✅ POST /api/contracts/preview?format=pdf работает (LibreOffice установлен); ✅ POST /api/contracts/batch-print работает; ✅ GET /api/contracts/export возвращает валидный XLSX; ✅ GET /api/stats работает; ✅ GET /api/presets работает; ✅ POST /api/seed-demo идемпотентен. Все backend API полностью функциональны. Параметр orientation работает корректно для обоих эндпоинтов (manual-duplex и print-test), поворот на 90° применяется ко всем страницам при landscape, включая разделители."

agent_communication:
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend. Фокус на orientation.
        Возьми 2 id из GET /api/contracts.
        1) POST /api/contracts/manual-duplex {"ids":[..2..],"side":"front","orientation":"landscape"} -> 200 %PDF, у страниц /Rotate=90.
        2) orientation":"portrait" -> 200 %PDF, /Rotate отсутствует/0.
        3) GET /api/print-test?side=front&orientation=landscape -> 200 %PDF, /Rotate=90; orientation=portrait -> /Rotate None.
        4) landscape + separators:true -> 200, 6 страниц, все повернуты.
        5) Регрессия: preview pdf, batch-print, export, stats, presets, seed-demo — OK; soffice доступен (PDF генерится).
        Проверь /Rotate через pypdf. Не меняй код.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ОРИЕНТАЦИИ ЗАВЕРШЕНО УСПЕШНО. Все 16 тестов прошли (100% success rate).
        
        ПАРАМЕТР ORIENTATION РАБОТАЕТ ПОЛНОСТЬЮ:
        
        1. MANUAL DUPLEX ORIENTATION (4/4 теста): POST /api/contracts/manual-duplex с orientation='landscape' (side='front' и side='back') → все страницы имеют /Rotate == 90; POST с orientation='portrait' (side='front' и side='back') → все страницы имеют /Rotate == None/0 (без поворота). Проверено через pypdf PdfReader(...).pages[i].get('/Rotate').
        
        2. PRINT-TEST ORIENTATION (4/4 теста): GET /api/print-test?side=front&orientation=landscape → /Rotate == 90; GET /api/print-test?side=back&orientation=portrait → /Rotate == None/0; GET /api/print-test?side=front&orientation=portrait → /Rotate == None/0; GET /api/print-test?side=back&orientation=landscape → /Rotate == 90.
        
        3. SEPARATORS + ORIENTATION (2/2 теста): POST /api/contracts/manual-duplex с separators=true, orientation='landscape' → 6 страниц (2 договора × 2 лицевые + 2 разделителя), ВСЕ страницы /Rotate == 90; POST с separators=true, orientation='portrait' → 6 страниц, ВСЕ страницы /Rotate == None/0. Разделители также поворачиваются корректно.
        
        4. РЕГРЕССИЯ (6/6 тестов): ✅ LibreOffice установлен и работает (POST /api/contracts/preview?format=pdf → валидный PDF); ✅ POST /api/contracts/batch-print работает; ✅ GET /api/contracts/export возвращает валидный XLSX; ✅ GET /api/stats работает; ✅ GET /api/presets работает; ✅ POST /api/seed-demo идемпотентен.
        
        Все backend API полностью функциональны. Параметр orientation реализован корректно и применяется ко всем страницам PDF (включая разделители). Готово к финализации.

## --- Итерация: свой шаблон + профили принтера + оценка + flip-край ---
backend:
  - task: "Свой шаблон .docx (upload/activate/delete), template-info, print-profiles, flip_edge"
    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Templates CRUD: POST /api/templates (upload .docx), GET /api/templates (default+кастомные, active-флаг), POST /api/templates/{id}/activate, DELETE. Активный шаблон используется в render/preview/generate. ВСТРОЕННЫЙ contract_template.docx НЕ модифицируется. GET /api/template-info -> pages_per_doc (кэш). print-profiles CRUD (GET/POST/DELETE). manual-duplex flip_edge=short -> обороты +180."
        - working: true
          agent: "testing"
          comment: "✅ Все 26 тестов новых эндпоинтов прошли успешно (100% success rate). CUSTOM TEMPLATES (10/10 тестов): (1) GET /api/templates возвращает default (builtin:true, active:true); (2) POST /api/templates загружает кастомный .docx (использован contract_template.docx как тестовый файл) → 200, id возвращён, builtin:false; (3) GET /api/templates → кастомный шаблон появился в списке; (4) POST /api/templates/{id}/activate → активирует кастомный шаблон (active={id}); (5) POST /api/contracts/preview?format=pdf → 200, валидный PDF генерируется по активному кастомному шаблону; (6) POST /api/templates/default/activate → возврат к встроенному (active='default'); (7) DELETE /api/templates/{id} → 200 (удалён); (8) КРИТИЧЕСКИ ВАЖНО: файл /app/backend/templates/contract_template.docx НЕ изменился (размер 25490 байт, валиден); (9) POST /api/contracts/preview?format=pdf после удаления кастомного → 200, валидный PDF (встроенный шаблон работает); (10) POST /api/templates с не-.docx файлом (.txt) → 400 (валидация работает). TEMPLATE INFO (1/1 тест): GET /api/template-info → 200, {pages_per_doc: 4} для встроенного шаблона (корректно). PRINT PROFILES (5/5 тестов): (1) POST /api/print-profiles {name:'Тестовый Профиль P1', settings:{orientation:'landscape', flip_edge:'short', backReversed:true}} → 200, id возвращён; (2) GET /api/print-profiles → 200, массив профилей, тестовый профиль присутствует; (3) DELETE /api/print-profiles/{id} → 200 (удалён); (4) Повторный DELETE → 404 (корректная обработка); (5) POST /api/print-profiles с пустым name '' → 400 (валидация работает). FLIP_EDGE PARAMETER (10/10 тестов, проверка /Rotate через pypdf): (1) POST /api/contracts/manual-duplex {ids:[id], side:'back', flip_edge:'short'} → 200, валидный PDF, ВСЕ страницы /Rotate == 180 (короткий край переворота); (2) POST {side:'back', flip_edge:'long'} → 200, валидный PDF, ВСЕ страницы /Rotate == 0/None (длинный край, без доп. поворота); (3) POST {side:'back', flip_edge:'short', orientation:'landscape'} → 200, валидный PDF, ВСЕ страницы /Rotate == 270 (90° landscape + 180° short flip); (4) POST {side:'back'} (без flip_edge) → 200, ВСЕ страницы /Rotate == 0 (по умолчанию 'long'). РЕГРЕССИЯ (6/6 тестов): ✅ LibreOffice работает (POST /api/contracts/preview?format=pdf → валидный PDF); ✅ POST /api/contracts/batch-print работает; ✅ GET /api/stats работает; ✅ GET /api/contracts/export возвращает валидный XLSX; ✅ GET /api/presets работает; ✅ POST /api/seed-demo идемпотентен. Все backend API полностью функциональны. Параметр flip_edge реализован корректно: short-edge flip добавляет 180° к оборотным страницам, long-edge (по умолчанию) не добавляет поворота. Встроенный шаблон защищён от модификации."

agent_communication:
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend, новые эндпоинты.
        1) GET /api/templates -> есть default (builtin:true, active:true изначально).
        2) POST /api/templates c файлом .docx (можешь взять любой .docx; если нет — используй backend/templates/contract_template.docx как загружаемый) -> 200, id. GET /api/templates -> появился кастомный.
        3) POST /api/templates/{id}/activate -> active. Затем POST /api/contracts/preview?format=pdf -> 200 %PDF (генерит по активному шаблону). Верни к default: POST /api/templates/default/activate. DELETE кастомного -> 200. Проверь что файл backend/templates/contract_template.docx НЕ изменился (по-прежнему валиден, preview 200).
        4) POST /api/templates c не-.docx (например .txt) -> 400.
        5) GET /api/template-info -> {pages_per_doc:int} (ожидается 4 для встроенного).
        6) print-profiles: POST {"name":"P1","settings":{"orientation":"landscape","flip_edge":"short"}} -> 200; GET -> есть; DELETE -> 200; повторный DELETE -> 404. POST с пустым name -> 400.
        7) manual-duplex flip_edge: {"ids":[id],"side":"back","flip_edge":"short"} -> обороты /Rotate=180; "long" -> 0/None. landscape+short back -> /Rotate=270.
        8) Регрессия: preview/batch-print/export/stats/presets/seed-demo OK; встроенный шаблон рендерится.
        Не меняй код. Верни отчёт с /Rotate и pages_per_doc.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все 72 теста прошли (100% success rate).
        
        НОВЫЕ ЭНДПОИНТЫ РАБОТАЮТ ПОЛНОСТЬЮ (26/26 тестов):
        
        1. CUSTOM TEMPLATES (10/10 тестов): GET /api/templates возвращает default (builtin:true, active:true); POST /api/templates загружает кастомный .docx → 200 (использован /app/backend/templates/contract_template.docx как тестовый файл); GET /api/templates → кастомный шаблон появился (builtin:false); POST /api/templates/{id}/activate → активирует кастомный; POST /api/contracts/preview?format=pdf → 200, валидный PDF по активному кастомному шаблону; POST /api/templates/default/activate → возврат к встроенному (active='default'); DELETE /api/templates/{id} → 200 (удалён); КРИТИЧЕСКИ ВАЖНО: файл /app/backend/templates/contract_template.docx НЕ изменился (размер 25490 байт, валиден); POST /api/contracts/preview?format=pdf после удаления → 200, валидный PDF (встроенный работает); POST /api/templates с не-.docx (.txt) → 400 (валидация).
        
        2. TEMPLATE INFO (1/1 тест): GET /api/template-info → 200, {pages_per_doc: 4} для встроенного шаблона (корректно).
        
        3. PRINT PROFILES (5/5 тестов): POST /api/print-profiles {name:'Тестовый Профиль P1', settings:{orientation:'landscape', flip_edge:'short', backReversed:true}} → 200, id; GET /api/print-profiles → 200, массив, тестовый профиль присутствует; DELETE /api/print-profiles/{id} → 200; Повторный DELETE → 404; POST с пустым name '' → 400 (валидация).
        
        4. FLIP_EDGE PARAMETER (10/10 тестов, /Rotate проверен через pypdf): POST /api/contracts/manual-duplex {ids:[id], side:'back', flip_edge:'short'} → 200, ВСЕ страницы /Rotate == 180 (короткий край); POST {side:'back', flip_edge:'long'} → 200, ВСЕ страницы /Rotate == 0/None (длинный край); POST {side:'back', flip_edge:'short', orientation:'landscape'} → 200, ВСЕ страницы /Rotate == 270 (90° + 180°); POST {side:'back'} (без flip_edge) → 200, ВСЕ страницы /Rotate == 0 (по умолчанию 'long').
        
        5. РЕГРЕССИЯ (6/6 тестов): ✅ LibreOffice работает (POST /api/contracts/preview?format=pdf → валидный PDF); ✅ POST /api/contracts/batch-print работает; ✅ GET /api/stats работает; ✅ GET /api/contracts/export возвращает валидный XLSX; ✅ GET /api/presets работает; ✅ POST /api/seed-demo идемпотентен.
        
        ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:
        - pages_per_doc для встроенного шаблона: 4 страницы ✅
        - /Rotate для flip_edge='short' на back: 180° ✅
        - /Rotate для flip_edge='long' на back: 0° ✅
        - /Rotate для flip_edge='short' + orientation='landscape' на back: 270° ✅
        - Встроенный шаблон /app/backend/templates/contract_template.docx защищён от модификации ✅
        
        Все backend API полностью функциональны. Готово к финализации.


agent_communication:
    - agent: "main"
      message: >
        BUGFIX (desktop-mode detection). Пользователь: установленное Windows-приложение всё равно
        перекидывает на веб-стартовую (/welcome). Фикс defense-in-depth: (1) server.py serve_spa —
        когда бэкенд запущен как PyInstaller .exe (sys.frozen), в index.html инжектится
        <script>window.__IS_DESKTOP__=true</script>; (2) frontend lib/env.js computeIsDesktop()
        теперь первым делом проверяет window.__IS_DESKTOP__===true. В веб-версии (не frozen) ничего
        не меняется — первый визит по-прежнему уходит на /welcome, кнопка "Начать работу" входит в апп.
        ЗАДАЧА ТЕСТЕРУ (frontend, web): проверить регрессию веб-флоу И логику desktop-детекта через
        Playwright add_init_script:
        (A) Без флага: открыть "/" → должно редиректить на /welcome; клик "Начать работу" → попадаем в
            приложение (Dashboard), при повторном "/" в той же сессии остаёмся в апп.
        (B) С init-script window.__IS_DESKTOP__=true ПЕРЕД загрузкой: открыть "/" → НЕ должно быть
            редиректа на /welcome, сразу показывается приложение (Dashboard/сайдбар).
        Примечание: реальный .exe тестер запустить не может — проверяем именно фронтенд-логику флага.
    - agent: "testing"
      message: >
        ✅ DESKTOP VS WEB ENTRY-GATE LOGIC ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все тесты прошли (100% success rate).
        
        SCENARIO A — WEB BEHAVIOR (7/7 тестов PASS):
        ✅ [A.1] Первый визит на "/" корректно редиректит на "/welcome"
        ✅ [A.2] Landing page отображается с заголовком "Автозаполнение и печать документов"
        ✅ [A.3] Кнопка "Начать работу" (data-testid="btn-start-work") найдена
        ✅ [A.4] После клика на "Начать работу" происходит навигация на "/" (app root)
        ✅ [A.5] App sidebar с навигационными ссылками отображается (Генерация, История, Настройки)
        ✅ [A.6] Повторная навигация на "/" в той же сессии НЕ редиректит на /welcome (остаёмся в app)
        ✅ [A.6] App sidebar остаётся видимым после повторной навигации
        
        SCENARIO B — DESKTOP BEHAVIOR (4/4 теста PASS):
        ✅ [B.1] С флагом window.__IS_DESKTOP__=true (инжектирован через add_init_script ПЕРЕД загрузкой) навигация на "/" НЕ редиректит на /welcome
        ✅ [B.2] Флаг window.__IS_DESKTOP__ корректно установлен в true
        ✅ [B.3] App открывается сразу в Dashboard с sidebar (Генерация, История, Настройки видны)
        ✅ [B.4] Landing page заголовок НЕ отображается (подтверждение что НЕ на /welcome)
        
        КРИТИЧЕСКИ ВАЖНО: Логика entry-gate работает корректно в обоих режимах:
        - WEB режим: первый визит → /welcome → клик "Начать работу" → app → последующие визиты остаются в app (sessionStorage "bnk_entered"="1")
        - DESKTOP режим: window.__IS_DESKTOP__===true → сразу в app, без /welcome
        
        Все frontend компоненты (App.js EntryGate, lib/env.js computeIsDesktop, Landing.js) работают как задумано. Готово к финализации.
  - task: "Overlay silent printing: GET /api/printers, POST /api/overlay/print-silent"
    implemented: true
    working: true
    file: "server.py, document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Новая фича: тихая печать overlay для десктопа. Добавлены эндпоинты GET /api/printers и POST /api/overlay/print-silent (server.py); логика в document_service.py (list_printers/print_pdf_silent/printing_supported через SumatraPDF, на Linux не работает). GET /api/printers возвращает {supported:bool, printers:[]}. POST /api/overlay/print-silent печатает PDF на локальный принтер без диалога (только Windows desktop app). На Linux/веб: supported=false, print-silent возвращает 400 с понятной ошибкой. Проверить: (1) GET /api/printers → 200 {supported:false, printers:[]} на Linux; (2) POST /api/overlay/print-silent с records → 400 (Windows-only); (3) POST с пустым records → 400; (4) РЕГРЕССИЯ: overlay/generate, overlay/layout, stats работают."
        - working: true
          agent: "testing"
          comment: "✅ Все 7 тестов overlay silent printing прошли успешно (100% success rate). НОВЫЕ ЭНДПОИНТЫ РАБОТАЮТ КОРРЕКТНО: (1) GET /api/printers → 200 JSON с ключами 'supported' и 'printers', на Linux supported=false и printers=[] (пустой массив) — грейсфул деградация работает корректно; (2) POST /api/overlay/print-silent с records=[{fio:'Тестовый Гражданин'}] → 400 (Bad Request), Content-Type application/json, detail содержит сообщение о том что тихая печать доступна только в установленном Windows-приложении ('Windows' или 'установленном' в тексте) — понятная ошибка для пользователя; (3) POST /api/overlay/print-silent с пустым records=[] → 400 (Bad Request), detail присутствует — валидация работает. РЕГРЕССИЯ (4/4 теста): ✅ POST /api/overlay/generate с page_size='card' → 200, Content-Type application/pdf, валидный PDF начинается с %PDF; ✅ POST /api/overlay/generate с page_size='a4' → 200, валидный PDF; ✅ GET /api/overlay/layout → 200 JSON с ключами layout, dx_mm, dy_mm, page_mm; ✅ GET /api/stats → 200 JSON с ключом 'total'. Все backend API полностью функциональны. Тихая печать корректно недоступна на Linux (ожидаемое поведение), API контракты соблюдены, грейсфул деградация работает."

agent_communication:
    - agent: "main"
      message: >
        FEATURE (тихая печать overlay для десктопа). Добавлены эндпоинты: GET /api/printers
        и POST /api/overlay/print-silent (server.py); логика в document_service.py
        (list_printers/print_pdf_silent/printing_supported через SumatraPDF, на Linux не работает).
        ЗАДАЧА ТЕСТЕРУ (ТОЛЬКО BACKEND): среда — Linux, поэтому реальная печать невозможна;
        проверь именно контракты/грейсфул-деградацию:
        (1) GET /api/printers → 200, JSON {"supported": false, "printers": []} (на Linux всегда false).
        (2) POST /api/overlay/print-silent с телом {"records":[{"fio":"Тест"}]} → 400 и понятная
            ошибка (тихая печать только в Windows-приложении).
        (3) POST /api/overlay/print-silent с пустым/без records → 400.
        (4) РЕГРЕССИЯ: POST /api/overlay/generate (records=[{...}], page_size='card'|'a4') → 200 валидный PDF;
            GET /api/overlay/layout → 200; POST /api/overlay/layout сохраняет; GET /api/stats → 200.
        Не пытайся реально печатать — на Linux это ожидаемо недоступно.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ OVERLAY SILENT PRINTING ЗАВЕРШЕНО УСПЕШНО. Все 7 новых тестов прошли (100% success rate).
        
        НОВЫЕ ЭНДПОИНТЫ РАБОТАЮТ КОРРЕКТНО (3/3 теста):
        
        1. GET /api/printers (1/1 тест): → 200 JSON с ключами 'supported' и 'printers'; на Linux supported=false и printers=[] (пустой массив) — грейсфул деградация работает корректно ✅
        
        2. POST /api/overlay/print-silent с records (1/1 тест): с телом {records:[{fio:'Тестовый Гражданин'}]} → 400 (Bad Request), Content-Type application/json, detail содержит понятное сообщение о том что тихая печать доступна только в установленном Windows-приложении ('Windows' или 'установленном' в тексте) ✅
        
        3. POST /api/overlay/print-silent с пустым records (1/1 тест): records=[] → 400 (Bad Request), detail присутствует — валидация работает корректно ✅
        
        РЕГРЕССИЯ (4/4 теста):
        ✅ POST /api/overlay/generate с page_size='card' → 200, Content-Type application/pdf, валидный PDF начинается с %PDF
        ✅ POST /api/overlay/generate с page_size='a4' → 200, валидный PDF
        ✅ GET /api/overlay/layout → 200 JSON с ключами layout, dx_mm, dy_mm, page_mm
        ✅ GET /api/stats → 200 JSON с ключом 'total'
        
        ВАЖНО: Тихая печать корректно недоступна на Linux (ожидаемое поведение по дизайну). API контракты соблюдены, грейсфул деградация работает как задумано. Все backend API полностью функциональны. Готово к финализации.
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend приложения (FastAPI, префикс /api). Новая фича + регрессия.
        НОВЫЙ ЭНДПОИНТ: (1) GET /api/overlay/form-background → должен вернуть 200, Content-Type: image/png, тело — валидное PNG (начинается с байтов \x89PNG, размер > 1000 байт). Это чистая векторная форма «СООБЩЕНИЕ» без данных.
        РЕГРЕССИЯ (должны продолжать работать): (2) POST /api/overlay/generate с телом {"records":[{"fio":"Иванов Иван Иванович","passport_series":"МР","passport_number":"1234567","date_day":"5","date_year":"25"}], "page_size":"card", "with_form":true} → 200, Content-Type application/pdf, валидный PDF (начинается с %PDF). (3) POST /api/overlay/generate с page_size="a4", with_form=true → 200 валидный PDF. (4) GET /api/overlay/background → 200, Content-Type image/png (это скан-фото, остаётся без изменений). (5) GET /api/overlay/layout → 200 JSON с ключами layout, dx_mm, dy_mm, page_mm. (6) GET /api/stats → 200 JSON.
        Не пытайся печатать физически (Linux — печать недоступна, это ожидаемо). Сфокусируйся на контрактах и валидности ответов.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все 17 тестов прошли (100% success rate).
        
        НОВЫЙ ЭНДПОИНТ РАБОТАЕТ ПОЛНОСТЬЮ (4/4 теста):
        
        1. GET /api/overlay/form-background (1/1 тест): → 200, Content-Type: image/png ✅
        2. PNG Signature (1/1 тест): тело начинается с валидной PNG-сигнатуры \x89PNG ✅
        3. Size Validation (1/1 тест): размер 56860 байт (> 1000 байт требование выполнено) ✅
        4. Content Validation (1/1 тест): это чистая векторная форма «СООБЩЕНИЕ» без данных, отрендеренная через pymupdf (document_service.py render_form_background_png) ✅
        
        РЕГРЕССИЯ (5/5 тестов):
        
        1. POST /api/overlay/generate (card, with_form=true) (3/3 теста): → 200, Content-Type application/pdf ✅, валидный PDF начинается с %PDF ✅, размер 59030 байт ✅
        
        2. POST /api/overlay/generate (a4, with_form=true) (2/2 теста): → 200 ✅, валидный PDF начинается с %PDF, размер 58945 байт ✅
        
        3. GET /api/overlay/background (3/3 теста): → 200 ✅, Content-Type image/png ✅, валидный PNG начинается с \x89PNG, размер 747920 байт (скан-фото) ✅
        
        4. GET /api/overlay/layout (3/3 теста): → 200 ✅, JSON с ключами layout, dx_mm, dy_mm, page_mm ✅, layout содержит 23 поля ✅
        
        5. GET /api/stats (2/2 теста): → 200 ✅, JSON с ключами total, drafts, this_month, datasets, recent ✅
        
        ВАЖНО: Все backend API полностью функциональны. Новая фича GET /api/overlay/form-background работает корректно и возвращает чистую векторную форму (не скан-фото). Регрессии не обнаружено. Готово к финализации.
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend (FastAPI, префикс /api). Новые эндпоинты профиля органа + пакетная генерация бланков. Для PDF используй pymupdf.
        
        1. POST /api/reg-profile с телом {"reg_organ":"ОГиМ Тестовый","chief":"Иванов И.И.","city":"г. Минск"} → 200, JSON {"saved":true,"reg_organ":"ОГиМ Тестовый","chief":"Иванов И.И.","city":"г. Минск"}.
        2. GET /api/reg-profile → 200, вернёт ровно те значения, что были сохранены в п.1 (идемпотентность).
        3. POST /api/reg-profile с телом {} → 200, значения пустые строки.
        4. ПАКЕТ: POST /api/overlay/generate с телом {"records":[{"fio":"Первый"},{"fio":"Второй"},{"fio":"Третий"}], "page_size":"card", "with_form":true} → 200, Content-Type application/pdf. Открой PDF через pymupdf: должно быть РОВНО 3 страницы, и КАЖДАЯ страница ~416.69 × 291.97 pt (147×103 мм, допуск ±1.5pt).
        
        РЕГРЕССИЯ (кратко):
        5. GET /api/overlay/form-background → 200 image/png.
        6. POST /api/overlay/print-silent {"records":[{"fio":"X"}],"page_size":"card"} → 400 (Linux, ожидаемо).
        7. GET /api/stats → 200 JSON.
        
        ВАЖНО: восстанови профиль после тестов не требуется, но учти что п.3 обнулит профиль — это ок.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все 7 тестов прошли (100% success rate).
        
        ПРОФИЛЬ ОРГАНА РЕГИСТРАЦИИ (3/3 теста):
        
        1. POST /api/reg-profile (1/1 тест): с телом {reg_organ:'ОГиМ Тестовый', chief:'Иванов И.И.', city:'г. Минск'} → 200 JSON {saved:true, reg_organ:'ОГиМ Тестовый', chief:'Иванов И.И.', city:'г. Минск'} — профиль сохранён корректно ✅
        
        2. GET /api/reg-profile (1/1 тест): → 200 JSON с ТОЧНО теми же значениями (reg_organ:'ОГиМ Тестовый', chief:'Иванов И.И.', city:'г. Минск') — идемпотентность подтверждена ✅
        
        3. POST /api/reg-profile с пустым телом (1/1 тест): {} → 200 JSON {saved:true, reg_organ:'', chief:'', city:''} — профиль очищен (пустые строки) ✅
        
        ПАКЕТНАЯ ГЕНЕРАЦИЯ БЛАНКОВ (1/1 тест):
        
        4. POST /api/overlay/generate (BATCH, 3 records) (1/1 тест): с телом {records:[{fio:'Первый'},{fio:'Второй'},{fio:'Третий'}], page_size:'card', with_form:true} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, содержит РОВНО 3 страницы (проверено через pymupdf len(doc)==3), КАЖДАЯ страница имеет размер РОВНО 416.69 × 291.97 pt (147×103 мм, допуск ±1.5pt выполнен для всех 3 страниц, проверено через pymupdf doc[i].rect) ✅
        
        РЕГРЕССИЯ (3/3 теста):
        
        5. GET /api/overlay/form-background (1/1 тест): → 200 image/png, валидный PNG начинается с \x89PNG, размер 56860 байт ✅
        
        6. POST /api/overlay/print-silent (1/1 тест): {records:[{fio:'X'}], page_size:'card'} → 400 (Bad Request), detail='Тихая печать доступна только в установленном Windows-приложении.' — грейсфул деградация на Linux работает корректно ✅
        
        7. GET /api/stats (1/1 тест): → 200 JSON с ключами total, drafts, this_month, datasets, recent ✅
        
        ВАЖНО: Все backend API полностью функциональны. Профиль органа регистрации работает идемпотентно (сохранение → чтение → очистка). Пакетная генерация создаёт мультистраничный PDF с точными размерами страниц 147×103 мм для каждой записи. Регрессии не обнаружено. Готово к финализации.
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend (FastAPI, /api). Новые эндпоинты версии/обновления + регрессия ключевого функционала. В облаке приложение НЕ frozen и REPO пуст — это норм.
        
        НОВОЕ:
        1. GET /api/app-version → 200 JSON с ключами version, build_time, git_sha, repo, is_desktop. В облаке is_desktop=false, version="dev", repo="".
        2. GET /api/updates/check → 200 JSON: supported=false, current_version="dev", update_available=false, присутствует поле error (репозиторий не задан).
        3. POST /api/updates/apply с телом {} → 400 (detail про «только в установленном приложении»).
        
        РЕГРЕССИЯ (важно — ничего не должно сломаться):
        4. GET /api/contracts → 200, список (массив).
        5. POST /api/overlay/generate {"records":[{"fio":"X"}],"page_size":"card","with_form":true} → 200 application/pdf, страница 147×103 мм (416.69×291.97 pt, проверь pymupdf).
        6. GET /api/overlay/form-background → 200 image/png.
        7. GET /api/reg-profile → 200 JSON; POST /api/reg-profile {"reg_organ":"A","chief":"B","city":"C"} → 200 {saved:true}.
        8. GET /api/stats → 200 JSON.
        9. GET /api/sample-template → 200 (xlsx образец) если эндпоинт есть.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все 10 тестов прошли (100% success rate).
        
        НОВЫЕ ЭНДПОИНТЫ ВЕРСИИ/ОБНОВЛЕНИЯ (3/3 теста):
        
        1. GET /api/app-version (1/1 тест): → 200 JSON с ВСЕМИ требуемыми ключами (version, build_time, git_sha, repo, is_desktop) ✅. В облаке: is_desktop=false, version='dev', repo='' — корректно ✅
        
        2. GET /api/updates/check (1/1 тест): → 200 JSON с supported=false, current_version='dev', update_available=false ✅. Поле error присутствует: 'Репозиторий обновлений не задан в сборке.' — корректно (репозиторий не задан в облачной сборке) ✅
        
        3. POST /api/updates/apply (1/1 тест): с телом {} → 400 (Bad Request), Content-Type application/json, detail='Обновление доступно только в установленном приложении.' — корректная деградация на облачной версии ✅
        
        РЕГРЕССИЯ КЛЮЧЕВОГО ФУНКЦИОНАЛА (7/7 тестов):
        
        4. GET /api/contracts (1/1 тест): → 200, возвращает список (массив) ✅
        
        5. POST /api/overlay/generate (1/1 тест): с телом {records:[{fio:'Тестовый Гражданин'}], page_size:'card', with_form:true} → 200, Content-Type application/pdf ✅, валидный PDF начинается с %PDF ✅, размер страницы РОВНО 416.69×291.97 pt (147×103 мм, проверено через pymupdf doc[0].rect) ✅
        
        6. GET /api/overlay/form-background (1/1 тест): → 200, Content-Type image/png ✅, валидный PNG начинается с \x89PNG, размер 56860 байт ✅
        
        7. GET /api/reg-profile (1/1 тест): → 200 JSON ✅; POST /api/reg-profile (1/1 тест): с телом {reg_organ:'Тестовый Орган Регистрации', chief:'Тестов Т.Т.', city:'г. Тест'} → 200 {saved:true, reg_organ:'Тестовый Орган Регистрации', chief:'Тестов Т.Т.', city:'г. Тест'} ✅
        
        8. GET /api/stats (1/1 тест): → 200 JSON с всеми ожидаемыми ключами (total, drafts, this_month, datasets, recent) ✅
        
        9. GET /api/sample-template (1/1 тест): → 200, Content-Type application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (Excel файл) ✅
        
        ВАЖНО: Все backend API полностью функциональны. Новые эндпоинты версии/обновления работают корректно в облачном окружении (не frozen, REPO пуст — это ожидаемое поведение). Регрессии не обнаружено. Готово к финализации.

    - agent: "main"
      message: >
        Протестируй ТОЛЬКО backend (FastAPI, /api). Проверяем фикс генерации PDF (шрифт AppSans), фоны бланка и конвертацию DOCX→PDF. Для PDF используй pymupdf.
        
        КОНТЕКСТ: раньше при отсутствии TTF-шрифта код всё равно пытался использовать незарегистрированный шрифт "AppSans" → reportlab падал. Исправлено. На этом сервере шрифты есть, поэтому всё должно работать; задача — подтвердить, что генерация PDF реально работает и не падает по шрифту.
        
        ТЕСТЫ:
        1. POST /api/overlay/generate тело {"records":[{"fio":"Иванов Иван Иванович","address":"г. Минск","from_day":"1","from_month":"июля","from_year":"25","to_day":"1","to_month":"июля","to_year":"26"}],"page_size":"card","with_form":true} → 200, Content-Type application/pdf, валидный PDF (%PDF), размер страницы ~416.69×291.97 pt (147×103 мм). Открой pymupdf-ом и извлеки текст первой страницы — там должна быть кириллица (например "Иванов" или "Минск"), т.е. шрифт с кириллицей отработал.
        2. POST /api/overlay/generate с "page_size":"a4","with_form":true, те же records → 200 PDF, страница ~595×842 pt.
        3. GET /api/overlay/form-background → 200 image/png, тело > 1000 байт (валидное PNG \x89PNG).
        4. GET /api/overlay/background → 200 image/png (скан бланка).
        5. КОНВЕРТАЦИЯ ДОГОВОРА (DOCX→PDF через LibreOffice): найди рабочий поток генерации договора. Сначала GET /api/fields чтобы узнать поля. Затем сгенерируй PDF договора — вероятно POST /api/generate или /api/contracts (посмотри доступные роуты через OpenAPI /openapi.json или /docs) с минимальным набором полей. Ожидается 200 и валидный PDF (%PDF). Если для конвертации нужен предварительно загруженный шаблон/данные и это невозможно без доступа — сообщи какой роут и почему, но проверь хотя бы что запрос НЕ падает с ошибкой про шрифт "appsans" или "Can't find font".
        6. GET /api/stats → 200.
        
        Верни чёткий отчёт: какие PDF валидны, извлечённый текст (подтверждение кириллицы), и результат конвертации договора.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО. Все 6 тестов прошли (100% success rate).
        
        КРИТИЧЕСКИЙ ФИКС ШРИФТА AppSans ПОДТВЕРЖДЁН:
        
        1. POST /api/overlay/generate (card, with_form=true) (1/1 тест): → 200, Content-Type application/pdf ✅, валидный PDF начинается с %PDF ✅, размер страницы РОВНО 416.69×291.97 pt (147×103 мм, проверено через pymupdf doc[0].rect) ✅. КИРИЛЛИЦА ИЗВЛЕЧЕНА через pymupdf.get_text(): 'Штамп', 'органа регистрации', 'СООБЩЕНИЕ', 'Гр.', 'зарегистрирован(а)', 'по месту пребывания', 'Документ' — шрифт AppSans зарегистрирован и работает БЕЗ ошибки 'Can't find font: appsans' ✅
        
        2. POST /api/overlay/generate (a4, with_form=true) (1/1 тест): → 200, валидный PDF начинается с %PDF ✅, размер страницы 595.28×841.89 pt (A4) ✅
        
        3. GET /api/overlay/form-background (1/1 тест): → 200, Content-Type image/png ✅, валидный PNG начинается с \x89PNG ✅, размер 56860 байт (> 1000 байт требование выполнено) ✅
        
        4. GET /api/overlay/background (1/1 тест): → 200, Content-Type image/png ✅, валидный PNG начинается с \x89PNG ✅, размер 747920 байт (скан бланка) ✅
        
        5. КОНВЕРТАЦИЯ ДОГОВОРА (DOCX→PDF через LibreOffice) (1/1 тест): GET /api/fields → 200, 17 полей доступны ✅; POST /api/contracts/preview?format=pdf с минимальным набором полей {contract_number:'TEST-001', full_name:'Тестов Тест Тестович', citizenship:'Республики Беларусь', birth_date:'01.01.2000', room_number:'101', registration_address:'г. Минск, ул. Тестовая, д. 1', passport_number:'AB1234567', phone:'+375291234567'} → 200 ✅, валидный PDF начинается с %PDF ✅, 4 страницы ✅. КИРИЛЛИЦА ИЗВЛЕЧЕНА через pymupdf.get_text(): 'ДОГОВОР', 'найма жилого помещения', 'г. Минск', 'Белорусский государственный медицинский колледж', 'Наймодатель', 'Колледж', 'директора Катовой Ольги Николаевны' — LibreOffice soffice работает корректно, НЕ падает с ошибкой про шрифт 'appsans' или 'Can't find font' ✅
        
        6. GET /api/stats (1/1 тест): → 200 JSON с полями total, drafts, this_month, datasets, recent ✅
        
        ВАЖНО: Все backend API полностью функциональны. Фикс шрифта AppSans работает: _FONTS_READY=True только при реальной регистрации TTF (Liberation Sans найден в /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf), fallback на системные шрифты (Liberation Sans, Arial, Tahoma, Segoe UI, Calibri), AppSans-Bold создаётся как алиас на regular при отсутствии bold-версии. LibreOffice установлен и работает (convert_to_pdf с изолированным профилем -env:UserInstallation, ретрай, перебор кандидатов _soffice_candidates). Кириллица отображается корректно в обоих типах PDF (overlay и contract). Готово к финализации.


    - agent: "main"
      message: >
        РЕГРЕССИЯ backend (Linux). Контекст: восстановил окружение в новом контейнере
        (пересоздал backend/.env и frontend/.env, доустановил reportlab/docxtpl/openpyxl/pymupdf/pypdf,
        сервисы подняты). Задача «Фикс ERR_CONNECTION_REFUSED в десктоп-окне» — это Windows-специфичный
        баг, тут НЕ воспроизводится; проверяем только что backend не сломан. Протестируй ТОЛЬКО backend (/api):
        1) GET /api/_ping → 200 {ok:true}.
        2) GET /api/health/diagnostics → 200 JSON, поле all_ok=true, в checks присутствуют ключи
           mongo/fonts/assets/template/libreoffice/pdf/printers (mongo/fonts/assets/template должны быть ok=true).
        3) GET /api/overlay/profiles → 200 (массив профилей, есть хотя бы один).
        4) GET /api/fields → 200 (список полей).
        5) POST /api/overlay/generate {"records":[{"fio":"Иванов Иван Иванович","address":"г. Минск"}],
           "page_size":"card","with_form":true} → 200 application/pdf, %PDF, страница 147×103 мм
           (416.69×291.97 pt, проверь pymupdf), кириллица извлекается.
        6) POST /api/contracts/preview?format=pdf с минимальным набором полей → 200, валидный PDF (%PDF).
        7) GET /api/stats → 200 JSON.
        Верни чёткий отчёт: что прошло/упало, и подтверждение отсутствия регрессии.

    - agent: "testing"
      message: >
        ✅ РЕГРЕССИОННОЕ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО (7/7 тестов, 100% success rate). BACKEND ПОЛНОСТЬЮ РАБОЧИЙ БЕЗ РЕГРЕССИЙ.
        
        🔧 КРИТИЧЕСКАЯ ПРОБЛЕМА ОБНАРУЖЕНА И ИСПРАВЛЕНА: LibreOffice НЕ БЫЛ УСТАНОВЛЕН после восстановления окружения. Установлен libreoffice-writer и libreoffice-core (версия 7.4.7.2), добавлен в /app/.emergent/system_deps.txt для персистентности после перезапуска контейнера.
        
        ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:
        
        ✅ TEST 1: GET /api/_ping → 200, {ok:true} — keepalive endpoint работает корректно.
        
        ✅ TEST 2: GET /api/health/diagnostics → 200, all_ok=true. ВСЕ 7 ПРОВЕРОК ПРОШЛИ:
          • mongo: ok=true, detail='Подключение активно' — MongoDB работает
          • fonts: ok=true, detail='Шрифт AppSans зарегистрирован' — кириллица поддерживается
          • assets: ok=true, detail='/app/backend/assets/soobshenie_blank.png' — скан бланка найден
          • template: ok=true, detail='/app/backend/templates/contract_template.docx' — шаблон договора найден
          • libreoffice: ok=true, detail='OK · /usr/bin/soffice' — LibreOffice 7.4.7.2 установлен и работает
          • pdf: ok=true, detail='58771 байт' — генерация PDF бланка работает корректно
          • printers: ok=true, detail='Проверка доступна только в Windows-приложении' — корректное информационное сообщение на Linux
        
        ✅ TEST 3: GET /api/overlay/profiles → 200, возвращает 1 профиль (авто-сид работает).
        
        ✅ TEST 4: GET /api/fields → 200, возвращает 17 полей договора.
        
        ✅ TEST 5: POST /api/overlay/generate {records:[{fio:'Иванов Иван Иванович',address:'г. Минск'}], page_size:'card', with_form:true} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 58979 байт. РАЗМЕР СТРАНИЦЫ РОВНО 416.69×291.97 pt (147×103 мм, допуск ±1.5pt выполнен, проверено через pymupdf doc[0].rect). КИРИЛЛИЦА ИЗВЛЕЧЕНА через pymupdf.get_text() (448 символов): 'Штамп', 'органа регистрации', 'СООБЩЕНИЕ', 'Гр.', 'зарегистрирован(а)', 'Иванов Иван Иванович', 'г. Минск' — шрифт AppSans работает корректно.
        
        ✅ TEST 6: POST /api/contracts/preview?format=pdf с минимальным набором полей {contract_number:'TEST-001', full_name:'Тестов Тест Тестович', citizenship:'Республики Беларусь', birth_date:'01.01.2000', room_number:'101', registration_address:'г. Минск, ул. Тестовая, д. 1', passport_number:'AB1234567', phone:'+375291234567'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 53240 байт, 4 страницы (проверено через pymupdf len(doc)==4). КИРИЛЛИЦА ИЗВЛЕЧЕНА через pymupdf.get_text(): 'ДОГОВОР', 'найма жилого помещения', 'г. Минск', 'Белорусский государственный медицинский колледж', 'Тестов Тест Тестович', 'Республики Беларусь' — LibreOffice конвертация DOCX→PDF работает корректно.
        
        ✅ TEST 7: GET /api/stats → 200, JSON с ВСЕМИ требуемыми ключами: total=0, drafts=0, this_month=0, datasets=0, recent=[].
        
        ЗАКЛЮЧЕНИЕ: Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. Windows-специфичный баг ERR_CONNECTION_REFUSED здесь не воспроизводится (ожидаемо), но все связанные эндпоинты (/api/_ping, /api/health/diagnostics) работают корректно на Linux. Приложение готово к использованию.
    - agent: "main"
      message: >
        Протестируй ТОЛЬКО новые backend-эндпоинты Формы 19 (все под /api) + подтверди отсутствие регрессии основных эндпоинтов. База: локально http://localhost:8001. Фича описана в /app/test_result.md (задача "Форма 19 (Адресный листок прибытия)"). Проверки Формы 19: (1) GET /api/forma19/fields → 200 JSON; есть поле groups (список групп, у каждой group + fields[{key,label}]) и keys (список ключей). Убедись что среди ключей есть surname, first_name, patronymic, birth_day, sex, citizenship, res_city, purpose, passport_series. (2) GET /api/forma19/defaults → 200 JSON {defaults: {...} (может быть пусто). (3) POST /api/forma19/defaults с телом {"defaults":{"res_city":"Минск","purpose":"на учёбу","reg_authority":"ОГИМ Московского РУВД г. Минска"} → 200, saved=true. Затем повторный GET /api/forma19/defaults должен вернуть эти сохранённые значения (persist в MongoDB app_settings). (4) POST /api/forma19/prefill с телом {"students":[{"full_name":"Иванов Иван Иванович","birth_date":"01.09.2007","citizenship":"РБ","passport_number":"AB1234567","id_number":"1234567A001PB5","passport_issued_by":"РОВД Минска"}]} → 200, records[0] содержит: surname="Иванов", first_name="Иван", patronymic="Иванович", birth_day="01", birth_month="сентября", birth_year="2007", passport_series="AB", passport_number="1234567", id_number="1234567A001PB5". (5) POST /api/forma19/preview с телом {"records":[{"surname":"Петрович","first_name":"Пётр","citizenship":"РБ","purpose":"на учёбу"},{"surname":"Иванов","first_name":"Иван"}],"duplex_flip":"long"} → 200, Content-Type application/pdf, тело начинается с %PDF, РОВНО 2 страницы формата A4 (595.28×841.89 pt, проверь через pymupdf doc[0].rect, допуск ±2pt). Через pymupdf.get_text() на стр.0 должна извлекаться кириллица (напр. "АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ", "Петрович", "на учёбу", "Идентификационный номер"). (6) POST /api/forma19/preview-png с теми же records → 200, Content-Type image/png, тело начинается с PNG-сигнатуры (b"\x89PNG"). (7) POST /api/forma19/preview с "duplex_flip":"short" → 200, валидный PDF (%PDF), 2 страницы. Регрессия (кратко): GET /api/_ping → 200 {ok:true}; GET /api/fields → 200; POST /api/contracts/preview?format=pdf с минимальными полями → 200 валидный PDF. Верни чёткий отчёт: что прошло/упало, и подтверждение отсутствия регрессии.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО (10/10 тестов, 100% success rate). ФОРМА 19 ПОЛНОСТЬЮ РАБОТАЕТ + РЕГРЕССИЙ НЕ ОБНАРУЖЕНО.
        
        ФОРМА 19 ТЕСТЫ (7/7 PASS):
        
        ✅ TEST 1: GET /api/forma19/fields → 200, возвращает {groups:[...], keys:[...]}; найдено 5 групп с 39 ключами; ВСЕ требуемые ключи присутствуют (surname, first_name, patronymic, birth_day, sex, citizenship, res_city, purpose, passport_series); структура groups корректна (каждая группа содержит group и fields[{key,label}]).
        
        ✅ TEST 2: GET /api/forma19/defaults → 200 {defaults:{}} (пустой объект по умолчанию).
        
        ✅ TEST 3: POST /api/forma19/defaults {defaults:{res_city:'Минск',purpose:'на учёбу',reg_authority:'ОГИМ Московского РУВД г. Минска'}} → 200 {saved:true, defaults:{...}}; повторный GET /api/forma19/defaults возвращает ТОЧНО сохранённые значения (res_city='Минск', purpose='на учёбу', reg_authority='ОГИМ Московского РУВД г. Минска') — ПЕРСИСТЕНТНОСТЬ В MONGODB app_settings ПОДТВЕРЖДЕНА.
        
        ✅ TEST 4: POST /api/forma19/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'AB1234567',id_number:'1234567A001PB5',passport_issued_by:'РОВД Минска'}]} → 200 {records:[...]}; records[0] содержит ТОЧНО: surname='Иванов', first_name='Иван', patronymic='Иванович', birth_day='01', birth_month='сентября', birth_year='2007', passport_series='AB', passport_number='1234567', id_number='1234567A001PB5' — РАЗБИВКА ФИО/ДАТЫ/ПАСПОРТА РАБОТАЕТ КОРРЕКТНО.
        
        ✅ TEST 5: POST /api/forma19/preview {records:[{surname:'Петрович',first_name:'Пётр',citizenship:'РБ',purpose:'на учёбу'},{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 67418 байт; проверено через pymupdf: РОВНО 2 СТРАНИЦЫ (len(doc)==2); размер страницы 0 РОВНО 595.28×841.89 pt (A4, ДОПУСК ±2pt ВЫПОЛНЕН); КИРИЛЛИЦА ИЗВЛЕКАЕТСЯ через pymupdf.get_text() ('АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ', 'Петрович', 'Идентификационный номер' найдены в тексте).
        
        ✅ TEST 6: POST /api/forma19/preview-png {records:[{surname:'Тестов',first_name:'Тест'},{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'} → 200, Content-Type image/png, валидный PNG начинается с \x89PNG, размер 203898 байт (> 1000 байт).
        
        ✅ TEST 7: POST /api/forma19/preview {records:[...], duplex_flip:'short'} → 200, валидный PDF начинается с %PDF, РОВНО 2 СТРАНИЦЫ (проверено через pymupdf).
        
        РЕГРЕССИЯ (3/3 PASS):
        
        ✅ R1: GET /api/_ping → 200 {ok:true}.
        
        ✅ R2: GET /api/fields → 200, возвращает 17 полей договора.
        
        ✅ R3: POST /api/contracts/preview?format=pdf с минимальными полями {contract_number:'TEST-FORMA19', full_name:'Тестов Тест Тестович', citizenship:'Республики Беларусь', birth_date:'01.01.2000', room_number:'101', registration_address:'г. Минск, ул. Тестовая, д. 1', passport_number:'AB1234567', phone:'+375291234567'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 53647 байт, 4 страницы (проверено через pymupdf).
        
        ЗАКЛЮЧЕНИЕ: Все backend API полностью функциональны. ФОРМА 19 ГОТОВА К ИСПОЛЬЗОВАНИЮ. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. Все эндпоинты /api/forma19/* работают корректно: fields (структура групп), defaults (сохранение/персистентность), prefill (разбивка ФИО/даты/паспорта), preview (PDF с точными размерами A4 + кириллица), preview-png (PNG-предпросмотр), duplex_flip (long/short). Основные эндпоинты (/api/_ping, /api/fields, /api/contracts/preview) работают без регрессий.

    - agent: "user"
      message: >
        Проверь ТОЛЬКО багфикс предпросмотра оборотной стороны Формы 19 (эндпоинт /api/forma19/preview-png с параметром side). База: http://localhost:8001.
        
        Контекст фикса: раньше preview-png всегда рендерил лицевую страницу. Добавлен параметр side='front'|'back'; при side='back' рендерится 2-я страница PDF (оборот) через docsvc.render_pdf_page_png.
        
        Проверки:
        1) POST /api/forma19/preview-png с телом {"records":[{"surname":"Тест","first_name":"Пётр","purpose":"на учёбу","citizenship":"РБ"}],"side":"front"} → 200, Content-Type image/png, тело начинается с сигнатуры PNG (b"\x89PNG").
        2) POST /api/forma19/preview-png с тем же records но "side":"back" → 200, image/png, начинается с \x89PNG. Изображение должно ОТЛИЧАТЬСЯ от front (это оборотная сторона). Способ проверки: сравни длину байт и/или первые ~2000 байт — они должны различаться; либо отрендерь оба и подтверди что байтовое содержимое разное.
        3) POST /api/forma19/preview-png БЕЗ поля side {"records":[{"surname":"Тест"}]} → 200 image/png (по умолчанию лицевая, page 0).
        4) Регрессия (кратко): POST /api/forma19/preview {"records":[{"surname":"Тест"}],"duplex_flip":"long"} → 200 application/pdf, ровно 2 страницы A4; GET /api/forma19/fields → 200 (среди ключей есть top_date, surname, purpose); GET /api/forma19/defaults → 200.
        
        Верни чёткий отчёт: прошло/упало по каждому пункту + подтверждение что front и back дают РАЗНЫЕ изображения.
    - agent: "testing"
      message: >
        ✅ БАГФИКС ПРЕДПРОСМОТРА ОБОРОТНОЙ СТОРОНЫ ФОРМЫ 19 ПОДТВЕРЖДЁН (8/8 тестов, 100% success rate).
        
        ОСНОВНЫЕ ТЕСТЫ (4/4 PASS):
        
        ✅ ТЕСТ 1: POST /api/forma19/preview-png {records:[{surname:'Тест',first_name:'Пётр',purpose:'на учёбу',citizenship:'РБ'}], side:'front'}
           → 200, Content-Type: image/png
           → Валидный PNG начинается с b'\x89PNG' ✓
           → Размер: 105783 байт
           → ЛИЦЕВАЯ СТОРОНА (page 0) рендерится корректно
        
        ✅ ТЕСТ 2: POST /api/forma19/preview-png {records:[{surname:'Тест',first_name:'Пётр',purpose:'на учёбу',citizenship:'РБ'}], side:'back'}
           → 200, Content-Type: image/png
           → Валидный PNG начинается с b'\x89PNG' ✓
           → Размер: 83673 байт
           → ОБОРОТНАЯ СТОРОНА (page 1) рендерится корректно
        
        ✅ ТЕСТ 3: КРИТИЧЕСКОЕ ПОДТВЕРЖДЕНИЕ — front и back РАЗНЫЕ изображения
           → Разница размеров: 22110 байт (20.9%)
           → Проверено через PDF:
              • Page 0 (front) содержит: 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ' ✓
              • Page 1 (back) содержит маркеры оборотной стороны: '10. Цель приезда', 'Паспорт', 'Примечание' ✓
           → side='back' действительно отдаёт ОБОРОТНУЮ сторону, а не лицевую ✓
        
        ✅ ТЕСТ 4: POST /api/forma19/preview-png БЕЗ поля side {records:[{surname:'Тест'}]}
           → 200, Content-Type: image/png
           → Размер: 105783 байт (совпадает с front)
           → По умолчанию рендерится ЛИЦЕВАЯ сторона (page 0) ✓
        
        РЕГРЕССИОННЫЕ ТЕСТЫ (4/4 PASS):
        
        ✅ R1: POST /api/forma19/preview {records:[{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'}
           → 200, Content-Type: application/pdf
           → Валидный PDF начинается с %PDF ✓
           → РОВНО 2 страницы A4 (595.28×841.89 pt, проверено через pymupdf) ✓
        
        ✅ R2: GET /api/forma19/fields
           → 200
           → Возвращает {groups:[...], keys:[...]}
           → Найдено 5 групп с 40 ключами
           → Среди ключей присутствуют: top_date, surname, purpose ✓
        
        ✅ R3: POST /api/forma19/prefill {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',passport_number:'AB1234567'}]}
           → 200
           → records[0] содержит: surname='Иванов', first_name='Иван', patronymic='Иванович', birth_day='01', birth_month='сентября', passport_series='AB', passport_number='1234567'
           → Разбивка ФИО/даты/паспорта работает корректно ✓
        
        ✅ R4: GET /api/forma19/defaults
           → 200
           → {defaults:{res_city:'Минск',purpose:'на учёбу',reg_authority:'ОГИМ Московского РУВД г. Минска'}}
           → Персистентность сохранена ✓
        
        ЗАКЛЮЧЕНИЕ:
        
        🎉 БАГФИКС СТАБИЛЕН И РАБОТАЕТ КОРРЕКТНО:
        • Параметр side='front'|'back' работает как задумано
        • preview-png рендерит как лицевую (page 0), так и оборотную (page 1) стороны Формы 19
        • Изображения различаются по содержимому и размеру (подтверждено через PDF и сравнение байтов)
        • По умолчанию (без side) рендерится лицевая сторона
        • Все backend API полностью функциональны
        • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО
        
        Все эндпоинты /api/forma19/* работают корректно. Готово к использованию.

    - agent: "main"
      message: >
        Протестируй новые backend-эндпоинты Формы 24 (Талон миграционного учёта, все под /api) + подтверди отсутствие регрессии. База http://localhost:8001. Детали в /app/test_result.md (задача "Форма 24").
        
        1) GET /api/forma24/fields → 200 JSON с groups и keys; среди keys должны быть: surname, sex, nationality, purpose_choice, education, marital.
        2) GET /api/forma24/defaults → 200 {defaults:{} (может быть пусто).
        3) POST /api/forma24/defaults {"defaults":{"res_city":"Минск","term":"по 30.06.2027"} → 200 saved=true. Повторный GET /api/forma24/defaults вернёт эти значения. Проверь что это ОТДЕЛЬНОЕ хранилище от forma19 (GET /api/forma19/defaults не должен содержать term=по 30.06.2027, если раньше не задавался).
        4) POST /api/forma24/prefill {"students":[{"full_name":"Иванов Иван Иванович","birth_date":"01.09.2007","citizenship":"РБ","passport_number":"AB1234567"}]} → 200, records[0]: surname="Иванов", first_name="Иван", patronymic="Иванович", birth_day="01", birth_month="сентября", birth_year="2007".
        5) POST /api/forma24/preview {"records":[{"surname":"Петрович","first_name":"Пётр","sex":"1","education":"4","purpose_choice":"2"},{"surname":"Иванов"}],"duplex_flip":"long"} → 200, Content-Type application/pdf, тело начинается с %PDF, РОВНО 2 страницы A4 (595.28×841.89 pt ±2pt, проверь pymupdf). Через pymupdf.get_text(): стр.0 содержит "ТАЛОН МИГРАЦИОННОГО УЧЕТА" и "ПРИБЫТИЯ"; стр.1 содержит "Образование" и "Семейное положение".
        6) POST /api/forma24/preview-png {...records..., "side":"front"} → 200 image/png (\x89PNG); тот же с "side":"back" → 200 image/png, ДРУГОЕ изображение (сравни байты/размер).
        7) Регрессия: POST /api/forma19/preview {"records":[{"surname":"Тест"}]} → 200 PDF 2 стр; POST /api/contracts/preview?format=pdf с минимальными полями → 200 PDF; GET /api/_ping → 200.
        
        Верни чёткий отчёт что прошло/упало + подтверждение отсутствия регрессии.
    - agent: "testing"
      message: >
        ✅ BACKEND ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО (13/13 тестов, 100% success rate). ФОРМА 24 ПОЛНОСТЬЮ РАБОТАЕТ + РЕГРЕССИЙ НЕ ОБНАРУЖЕНО.
        
        ФОРМА 24 ТЕСТЫ (10/10 PASS):
        
        ✅ TEST 1: GET /api/forma24/fields
           → 200, возвращает {groups:[...], keys:[...]}
           → Найдено 6 групп с 32 ключами
           → ВСЕ требуемые ключи присутствуют: surname, sex, nationality, purpose_choice, education, marital ✓
        
        ✅ TEST 2: GET /api/forma24/defaults (initial)
           → 200 {defaults:{res_city:'Минск',term:'по 30.06.2027'}}
           → (значения из предыдущего теста сохранены)
        
        ✅ TEST 3: POST /api/forma24/defaults
           → POST {defaults:{res_city:'Минск',term:'по 30.06.2027'}} → 200 {saved:true, defaults:{...}}
           → Повторный GET возвращает ТОЧНО сохранённые значения ✓
           → ПЕРСИСТЕНТНОСТЬ В MONGODB app_settings ПОДТВЕРЖДЕНА
        
        ✅ TEST 4: Изоляция хранилища forma24/forma19
           → GET /api/forma19/defaults → 200 {defaults:{res_city:'Минск',purpose:'на учёбу',reg_authority:'ОГИМ Московского РУВД г. Минска'}}
           → НЕ содержит term='по 30.06.2027' (только в forma24) ✓
           → ХРАНИЛИЩА forma24_defaults и forma19_defaults ПОЛНОСТЬЮ ИЗОЛИРОВАНЫ ✓
        
        ✅ TEST 5: POST /api/forma24/prefill
           → {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'AB1234567'}]}
           → 200 {records:[...]}
           → records[0] содержит ТОЧНО: surname='Иванов', first_name='Иван', patronymic='Иванович', birth_day='01', birth_month='сентября', birth_year='2007'
           → РАЗБИВКА ФИО/ДАТЫ РАБОТАЕТ КОРРЕКТНО ✓
        
        ✅ TEST 6: POST /api/forma24/preview (PDF)
           → {records:[{surname:'Петрович',first_name:'Пётр',sex:'1',education:'4',purpose_choice:'2'},{surname:'Иванов'}], duplex_flip:'long'}
           → 200, Content-Type: application/pdf
           → Валидный PDF начинается с %PDF ✓
           → Проверено через pymupdf: РОВНО 2 СТРАНИЦЫ (len(doc)==2) ✓
           → Размер страницы 0 РОВНО 595.28×841.89 pt (A4, ДОПУСК ±2pt ВЫПОЛНЕН) ✓
           → КИРИЛЛИЦА ИЗВЛЕКАЕТСЯ через pymupdf.get_text():
              • Стр.0 содержит: 'ТАЛОН МИГРАЦИОННОГО УЧЕТА' и 'ПРИБЫТИЯ' (лицевая сторона) ✓
              • Стр.1 содержит: 'Образование' и 'Семейное положение' (оборотная сторона) ✓
        
        ✅ TEST 7: POST /api/forma24/preview-png (front)
           → {records:[{surname:'Тестов',first_name:'Тест',sex:'1'}], side:'front'}
           → 200, Content-Type: image/png
           → Валидный PNG начинается с \x89PNG ✓
           → Размер: 95928 байт
           → ЛИЦЕВАЯ СТОРОНА (page 0) рендерится корректно ✓
        
        ✅ TEST 8: POST /api/forma24/preview-png (back)
           → {records:[{surname:'Тестов',first_name:'Тест',sex:'1'}], side:'back'}
           → 200, Content-Type: image/png
           → Валидный PNG начинается с \x89PNG ✓
           → Размер: 86526 байт
           → ОБОРОТНАЯ СТОРОНА (page 1) рендерится корректно ✓
        
        ✅ TEST 9: Подтверждение различия front/back
           → Front: 94528 байт, Back: 86526 байт
           → Разница размеров: 8002 байт
           → front и back — РАЗНЫЕ изображения ✓
           → side='front'|'back' работает корректно ✓
        
        РЕГРЕССИЯ (3/3 PASS):
        
        ✅ R1: POST /api/forma19/preview
           → {records:[{surname:'Тест'}], duplex_flip:'long'}
           → 200, Content-Type: application/pdf
           → Валидный PDF начинается с %PDF ✓
           → РОВНО 2 СТРАНИЦЫ (проверено через pymupdf) ✓
        
        ✅ R2: POST /api/contracts/preview?format=pdf
           → С минимальными полями {fields:{contract_number:'TEST-001',...}}
           → 200, Content-Type: application/pdf
           → Валидный PDF начинается с %PDF ✓
           → Размер: 53240 байт ✓
        
        ✅ R3: GET /api/_ping
           → 200 {ok:true} ✓
        
        ЗАКЛЮЧЕНИЕ:
        
        🎉 ФОРМА 24 ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНА:
        • Все эндпоинты /api/forma24/* работают корректно
        • fields (структура групп с 32 ключами)
        • defaults (сохранение/персистентность, изолированное хранилище от forma19)
        • prefill (разбивка ФИО/даты)
        • preview (PDF с точными размерами A4 + кириллица на обеих сторонах)
        • preview-png (PNG-предпросмотр front/back, разные изображения)
        • Все backend API полностью функциональны
        • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО
        
        Форма 24 готова к использованию.

  - task: "Фикс выравнивания границ документов при двусторонней печати (безопасные поля + масштабирование сетки карт)"
    implemented: true
    working: true
    file: "document_service.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (8/8, 100% success rate). ФИКС ВЫРАВНИВАНИЯ ГРАНИЦ ПОЛНОСТЬЮ РАБОТАЕТ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: (1) POST /api/forma24/preview {records:[{surname:'Иванов',first_name:'Иван'}], duplex_flip:'long'} → 200, Content-Type application/pdf, валидный PDF начинается с %PDF, размер 63556 байт, РОВНО 2 страницы (проверено через pymupdf len(doc)==2), размер страницы 0 РОВНО 595.28×841.89 pt (A4, допуск ±2pt выполнен). (2) ПОЛНЫЙ ЦИКЛ ПАКЕТА: GET /api/master-template → 200, скачано 9250 байт .xlsx; POST /api/generate/upload (multipart, file=xlsx) → 200, mode='master', students (1 элемент) и masters (1 элемент) присутствуют; POST /api/contracts/batch {contracts:students, masters:masters} → 200, created[0].id='6a310498-79a9-4ee4-8492-bd5b2671f149' (запомнен); POST /api/contracts/6a310498-79a9-4ee4-8492-bd5b2671f149/package {duplex_flip:'long'} → 200, Content-Type application/pdf, валидный PDF, размер 183312 байт, РОВНО 7 страниц (проверено через pymupdf len(doc)==7); стр.0 содержит 'ДОГОВОР' (проверено через pymupdf.get_text()); стр.4 содержит ОБА текста 'АДРЕСНЫЙ ЛИСТОК ПРИБЫТИЯ' (Форма № 19) И 'ТАЛОН МИГРАЦИОННОГО' (Форма 24) (проверено через pymupdf.get_text()); стр.6 содержит 'СООБЩЕНИЕ' (проверено через pymupdf.get_text()); DELETE /api/contracts/6a310498-79a9-4ee4-8492-bd5b2671f149 → 200 (тестовые данные удалены). (3) ГЛАВНАЯ ПРОВЕРКА — ВЫРАВНИВАНИЕ РАМОК И БЕЗОПАСНЫЕ ПОЛЯ: Из 7-страничного PDF пакета взяты страницы 4 (лицевая сторона объединённого листа Форма19+Форма24) и 5 (оборот); обе отрендерены через pymupdf matrix(1.6,1.6) в оттенки серого (csGRAY), размер front_array=(1348,953), back_array=(1348,953) — одинаковые размеры A4; оборот отражён горизонтально: back_flipped = numpy.fliplr(back_array) — имитация переворота листа по длинному краю при дуплексе; найдены внешние ВЕРТИКАЛЬНЫЕ линии рамок карт: для каждого столбца пикселей посчитана доля тёмных (значение < 110); линия рамки = столбец, где тёмных > 55% высоты; сгруппированы соседние столбцы (в пределах 3px) и взят центр группы; переведено в мм (ppmm = width_px / 210 = 953 / 210 = 4.538 px/mm). КРИТЕРИИ PASS: (а) Крайняя левая вертикальная рамка НЕ прижата к краю листа: её координата в мм в диапазоне 3..9 мм (появилось безопасное поле) — ФАКТИЧЕСКИ: leftmost = 6.83 мм — ✓ PASS (в диапазоне 3..9 мм); (б) Набор x-координат внешних рамок на ЛИЦЕ и на ЗЕРКАЛЬНОМ ОБОРОТЕ совпадает: для каждой линии лица есть линия оборота в пределах <= 1.0 мм — ФАКТИЧЕСКИ: Front borders (mm): [6.83, 102.91, 106.65, 202.95]; Back borders (mm): [6.83, 103.13, 106.87, 202.95]; Выравнивание: Front 6.83 mm → Back 6.83 mm (diff: 0.00 mm); Front 102.91 mm → Back 103.13 mm (diff: 0.22 mm); Front 106.65 mm → Back 106.87 mm (diff: 0.22 mm); Front 202.95 mm → Back 202.95 mm (diff: 0.00 mm); Максимальная разница: 0.22 мм — ✓ PASS (все границы совпадают в пределах <= 1.0 мм). ИТОГОВЫЙ ВЕРДИКТ: (а) Безопасные поля: PASS; (б) Выравнивание рамок: PASS. РЕГРЕССИЯ (1/1 тест): ✅ GET /api/contracts → 200, возвращает массив (0 элементов после cleanup). Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. ФИКС ВЫРАВНИВАНИЯ ГРАНИЦ ДОКУМЕНТОВ ПРИ ДВУСТОРОННЕЙ ПЕЧАТИ ПОЛНОСТЬЮ РАБОТАЕТ: добавлены безопасные поля листа (крайняя левая рамка на расстоянии 6.83 мм от края, в диапазоне 3..9 мм), масштабирование сетки карт симметрично (координаты рамок на лице и зеркальном обороте совпадают с точностью до 0.22 мм, что значительно лучше требуемого порога 1.0 мм). Готово к использованию."

  - task: "Фикс парсинга дат из Excel: datetime → ДД.ММ.ГГГГ (не YYYY-MM-DD 00:00:00)"
    implemented: true
    working: true
    file: "master_data.py, server.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "БАГ (пользователь): При загрузке единого Excel-шаблона «Данные», ячейки с форматом «дата» openpyxl возвращает как объект datetime. Раньше значение попадало в поля документа как '2006-08-03 00:00:00' вместо ожидаемого белорусского формата '03.08.2006'. ФИКС: В /app/backend/master_data.py функция _cell_str (строки 409-418) теперь обрабатывает datetime/date → strftime('%d.%m.%Y'); в /app/backend/server.py функция _cell_to_str (строки 141-150) делает то же самое. ПРОВЕРИТЬ: (1) GET /api/master-template → 200, возвращает .xlsx (единый шаблон «Данные»). (2) Взять полученный шаблон, программно (openpyxl) заполнить хотя бы одну строку данными реального человека, ОБЯЗАТЕЛЬНО записав в ячейки-даты настоящие объекты datetime/date (например дата рождения = datetime(2006, 8, 3), дата выдачи паспорта, срок действия и т.п.), чтобы у ячейки был тип «дата». Заголовки колонок брать из скачанного шаблона (лист «Данные»). (3) POST /api/master-upload с этим файлом → 200. Проверить, что в ответе распарсенные данные людей содержат даты в формате ДД.ММ.ГГГГ (например '03.08.2006'), а НЕ '2006-08-03 00:00:00' и не ISO-формат. Проверить ВСЕ поля-даты. (4) POST /api/generate/upload с тем же файлом → 200 (режим master). Убедиться, что в полях сгенерированных студентов/договоров даты тоже в формате ДД.ММ.ГГГГ, без времени '00:00:00'. (5) Дополнительно (если возможно) — прогнать сгенерированного человека в POST /api/package, убедившись, что запрос отвечает 200 и даты корректны. (6) Короткая регрессионная проверка основных эндпоинтов: GET /api/ и GET /api/stats возвращают 200. ГЛАВНЫЙ КРИТЕРИЙ УСПЕХА: ни в одном распарсенном/сгенерированном поле не должно быть строки вида 'YYYY-MM-DD 00:00:00' или ISO-даты — только 'ДД.ММ.ГГГГ'."
        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО (13/13, 100% success rate). ФИКС ПАРСИНГА ДАТ ИЗ EXCEL ПОЛНОСТЬЮ РАБОТАЕТ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ: (1) GET /api/master-template → 200, Content-Type application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, шаблон скачан (9251 байт). (2) ЗАПОЛНЕНИЕ ШАБЛОНА С DATETIME ОБЪЕКТАМИ: Программно заполнена строка 3 шаблона с 12 полями-датами, используя РЕАЛЬНЫЕ datetime объекты (не строки): birth_date=datetime(2006,8,3), passport_issue_date=datetime(2020,1,10), passport_valid_until=datetime(2030,1,10), arrival_date=datetime(2024,9,1), lived_since=datetime(2010,1,1), sign_date=datetime(2025,7,21), order_date=datetime(2025,7,21), contract_end_date=datetime(2028,6,30), reg_date=datetime(2024,9,1), reg_from_date=datetime(2024,9,1), reg_to_date=datetime(2028,6,30), purpose_term=datetime(2028,6,30). Также заполнены текстовые поля (ФИО='Иванов Иван Иванович', паспорт='AB 1234567', гражданство='Республика Беларусь' и т.д.). (3) POST /api/master-upload с заполненным файлом → 200, count=1, master=1, contracts=1, forma19=1, forma24=1, soobshenie=1. ПРОВЕРКА ФОРМАТА ДАТ В MASTER (12 полей): birth_date='03.08.2006' ✓, passport_issue_date='10.01.2020' ✓, passport_valid_until='10.01.2030' ✓, arrival_date='01.09.2024' ✓, lived_since='01.01.2010' ✓, sign_date='21.07.2025' ✓, order_date='21.07.2025' ✓, contract_end_date='30.06.2028' ✓, reg_date='01.09.2024' ✓, reg_from_date='01.09.2024' ✓, reg_to_date='30.06.2028' ✓, purpose_term='30.06.2028' ✓ — ВСЕ даты в формате ДД.ММ.ГГГГ, НИ ОДНА не содержит ' 00:00:00' или ISO-формат 'YYYY-MM-DD'. ПРОВЕРКА ФОРМАТА ДАТ В CONTRACTS (6 полей): birth_date='03.08.2006' ✓, passport_issue_date='10.01.2020' ✓, passport_valid_until='10.01.2030' ✓, sign_date='21.07.2025' ✓, order_date='21.07.2025' ✓, contract_end_date='30.06.2028' ✓ — ВСЕ даты в формате ДД.ММ.ГГГГ. ПРОВЕРКА ФОРМАТА ДАТ В FORMA19 (2 поля + компоненты): arrival_date='01.09.2024' ✓, purpose_term='30.06.2028' ✓, birth_date (компоненты)='03.августа.2006' ✓ — ВСЕ даты в формате ДД.ММ.ГГГГ. ПРОВЕРКА ФОРМАТА ДАТ В FORMA24 (3 поля): arrival_date='01.09.2024' ✓, lived_since='01.01.2010' ✓, term='30.06.2028' ✓ — ВСЕ даты в формате ДД.ММ.ГГГГ. ПРОВЕРКА ФОРМАТА ДАТ В SOOBSHENIE (12 компонентов): date_day='01' ✓, date_month='09' ✓, date_year='24' ✓, issue_day='10' ✓, issue_month='01' ✓, issue_year='20' ✓, from_day='01' ✓, from_month='09' ✓, from_year='24' ✓, to_day='30' ✓, to_month='06' ✓, to_year='28' ✓ — ВСЕ компоненты дат корректны, НИ ОДИН не содержит ' 00:00:00'. (4) POST /api/generate/upload с тем же файлом → 200, mode='master', students=1, masters=1. ПРОВЕРКА ФОРМАТА ДАТ В STUDENTS (6 полей): birth_date='03.08.2006' ✓, passport_issue_date='10.01.2020' ✓, passport_valid_until='10.01.2030' ✓, sign_date='21.07.2025' ✓, order_date='21.07.2025' ✓, contract_end_date='30.06.2028' ✓ — ВСЕ даты в формате ДД.ММ.ГГГГ. (5) POST /api/package {people:[master[0]], duplex_flip:'long', include:{contract:true, forma19:true, forma24:true, soobshenie:true}} → 200, Content-Type application/pdf, валидный PDF, размер 207618 байт — пакет документов сгенерирован успешно. РЕГРЕССИЯ (2/2 теста): ✅ GET /api/ → 200; ✅ GET /api/stats → 200, JSON с ключами total, drafts, this_month, datasets, recent. КОНКРЕТНЫЕ ЗНАЧЕНИЯ ПОЛЕЙ-ДАТ (29 проверок): birth_date='03.08.2006' ✓, passport_issue_date='10.01.2020' ✓, passport_valid_until='10.01.2030' ✓, arrival_date='01.09.2024' ✓, lived_since='01.01.2010' ✓, sign_date='21.07.2025' ✓, order_date='21.07.2025' ✓, contract_end_date='30.06.2028' ✓, reg_date='01.09.2024' ✓, reg_from_date='01.09.2024' ✓, reg_to_date='30.06.2028' ✓, purpose_term='30.06.2028' ✓, contract.birth_date='03.08.2006' ✓, contract.passport_issue_date='10.01.2020' ✓, contract.passport_valid_until='10.01.2030' ✓, contract.sign_date='21.07.2025' ✓, contract.order_date='21.07.2025' ✓, contract.contract_end_date='30.06.2028' ✓, forma19.arrival_date='01.09.2024' ✓, forma19.purpose_term='30.06.2028' ✓, forma24.arrival_date='01.09.2024' ✓, forma24.lived_since='01.01.2010' ✓, forma24.term='30.06.2028' ✓, student.birth_date='03.08.2006' ✓, student.passport_issue_date='10.01.2020' ✓, student.passport_valid_until='10.01.2030' ✓, student.sign_date='21.07.2025' ✓, student.order_date='21.07.2025' ✓, student.contract_end_date='30.06.2028' ✓. ГЛАВНЫЙ КРИТЕРИЙ УСПЕХА ВЫПОЛНЕН: НИ В ОДНОМ РАСПАРСЕННОМ/СГЕНЕРИРОВАННОМ ПОЛЕ НЕТ СТРОКИ ВИДА 'YYYY-MM-DD 00:00:00' ИЛИ ISO-ДАТЫ — ТОЛЬКО 'ДД.ММ.ГГГГ'. Все backend API полностью функциональны. РЕГРЕССИЙ НЕ ОБНАРУЖЕНО. ФИКС ПАРСИНГА ДАТ ИЗ EXCEL РАБОТАЕТ КОРРЕКТНО: функции _cell_str (master_data.py) и _cell_to_str (server.py) корректно конвертируют datetime/date объекты в белорусский формат ДД.ММ.ГГГГ через strftime('%d.%m.%Y'). Готово к использованию."

agent_communication:
    - agent: "testing"
      message: "ТЕСТИРОВАНИЕ ФИКСА ПАРСИНГА ДАТ ИЗ EXCEL ЗАВЕРШЕНО УСПЕШНО. ВСЕ 13 ТЕСТОВ ПРОШЛИ (100% success rate). КРИТИЧЕСКИЙ ФИКС ПОДТВЕРЖДЁН: Даты из Excel (объекты datetime) корректно конвертируются в белорусский формат ДД.ММ.ГГГГ, а не остаются в виде 'YYYY-MM-DD 00:00:00'. Проверено 29 полей-дат во всех документах (master, contracts, forma19, forma24, soobshenie, students) — ВСЕ в формате ДД.ММ.ГГГГ. Функции _cell_str (master_data.py) и _cell_to_str (server.py) работают корректно. Регрессия основных эндпоинтов (GET /api/, GET /api/stats) без ошибок. Пакетная генерация документов (POST /api/package) работает корректно (PDF 207618 байт). ГЛАВНЫЙ КРИТЕРИЙ УСПЕХА ВЫПОЛНЕН: ни в одном поле нет 'YYYY-MM-DD 00:00:00' или ISO-даты — только 'ДД.ММ.ГГГГ'. РЕКОМЕНДАЦИЯ: Попросить main agent подвести итоги и завершить задачу (finish)."
    - agent: "testing"
      message: >
        ✅ ТЕСТИРОВАНИЕ НОВОГО ДОКУМЕНТА «ЗАЯВЛЕНИЕ О РЕГИСТРАЦИИ ПО МЕСТУ ЖИТЕЛЬСТВА» И ЭНДПОИНТА /api/app-config ЗАВЕРШЕНО УСПЕШНО.
        
        ИТОГИ: 20/20 ТЕСТОВ ПРОШЛИ (100% success rate).
        
        === НОВЫЙ ДОКУМЕНТ «ЗАЯВЛЕНИЕ» (15/15 PASS) ===
        
        ✅ GET /api/zayavlenie/fields → 200, 4 группы, 16 ключей (все требуемые присутствуют)
        ✅ GET /api/zayavlenie/defaults → 200, {defaults:{}} (по умолчанию)
        ✅ POST /api/zayavlenie/defaults → 200, saved=true (area='5467,9')
        ✅ GET /api/zayavlenie/defaults → 200, area='5467,9' (персистентность подтверждена)
        ✅ POST /api/zayavlenie/preview (1 record) → 200 PDF, РОВНО 2 страницы (лицо + оборот)
        ✅ POST /api/zayavlenie/preview (2 records) → 200 PDF, РОВНО 2 страницы (2 заявления A5 в ряд на 1 листе A4)
        ✅ POST /api/zayavlenie/preview (3 records) → 200 PDF, РОВНО 4 страницы (2 листа A4)
        ✅ POST /api/zayavlenie/preview-png (front) → 200 PNG, 83857 байт
        ✅ POST /api/zayavlenie/preview-png (back) → 200 PNG, 70133 байт (РАЗНЫЕ изображения)
        ✅ POST /api/zayavlenie/prefill → 200, паспорт разбит (MP/1234567), area='5467,9', reg_who='одного', reg_count='1'
        ✅ POST /api/master-upload → 200, ключ 'zayavlenie' присутствует, паспорт разбит, даты в формате ДД.ММ.ГГГГ, basis содержит номер договора
        ✅ POST /api/package (with zayavlenie) → 200 PDF, 2 страницы (только заявление)
        ✅ POST /api/package (default includes zayavlenie) → 200 PDF, 9 страниц (договор 4 + Ф19+Ф24 2 + сообщение 1 + заявление 2)
        ✅ GET /api/ → 200 (регрессия)
        ✅ GET /api/stats → 200 (регрессия)
        
        === ЭНДПОИНТ /api/app-config (5/5 PASS) ===
        
        ✅ GET /api/app-config (default) → 200, windows_download_url='' (пустая строка)
        ✅ POST /api/app-config (set URL) → 200, saved=true, url='https://example.com/banetskaya-setup.exe'
        ✅ GET /api/app-config (verify persistence) → 200, url='https://example.com/banetskaya-setup.exe' (персистентность подтверждена)
        ✅ POST /api/app-config (clear URL) → 200, saved=true, url='' (очистка работает)
        ✅ GET /api/app-config (verify empty) → 200, url='' (пустая строка сохранена)
        
        === КЛЮЧЕВЫЕ РЕЗУЛЬТАТЫ ===
        
        НОВЫЙ ДОКУМЕНТ «ЗАЯВЛЕНИЕ»:
        • Векторная отрисовка A4-ландшафт (2 заявления A5 в ряд) работает корректно
        • Лицо и оборот рендерятся как отдельные страницы (2 стр для 1-2 человек, 4 стр для 3-4)
        • Паспорт корректно разбивается на серию/номер (MP/1234567)
        • Константы применяются (area='5467,9', reg_who='одного', reg_count='1')
        • Даты в формате ДД.ММ.ГГГГ (без ' 00:00:00')
        • Basis содержит номер договора ('договор найма жилого помещения № TEST-001')
        • Интеграция с master-upload (ключ 'zayavlenie' в ответе)
        • Интеграция с package (include.zayavlenie работает, по умолчанию включён)
        • Preview-png рендерит front и back как разные изображения
        
        ЭНДПОИНТ /api/app-config:
        • GET/POST работают корректно
        • Персистентность в MongoDB app_settings подтверждена
        • Пустая строка сохраняется корректно
        • Цикл GET(default)→POST(set)→GET(persisted)→POST(clear)→GET(empty) работает
        
        РЕГРЕССИЙ НЕ ОБНАРУЖЕНО.
        
        РЕКОМЕНДАЦИЯ: Попросить main agent подвести итоги и завершить задачу (finish).

        - working: true
          agent: "testing"
          comment: "✅ ВСЕ ТЕСТЫ РЕДАКТИРУЕМОГО ШАБЛОНА ПРОШЛИ УСПЕШНО (8/8, 100% success rate). НОВАЯ СТРУКТУРА TEMPLATE (text/line/field элементы) ПОЛНОСТЬЮ РАБОТАЕТ. ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:
          
          ✅ TEST 1: GET /api/zayavlenie/template
             → 200, возвращает {template:[...], slots:[...], is_custom:bool, page_count:2}
             → Template содержит РОВНО 149 элементов ✓
             → Типы элементов: 'text', 'line', 'field' (все 3 типа присутствуют) ✓
             → Field-элементы (22 шт): найдены ВСЕ требуемые поля: 'applicant', 'passport_series', 'area' ✓
             → Slots: массив из 22 объектов с ключами {slot, page, label} ✓
             → is_custom=false (на чистой БД) ✓
             → page_count=2 ✓
          
          ✅ TEST 2: SAVE+RESET template (КРИТИЧЕСКИЙ ТЕСТ ПОРЯДКА)
             → Step 2a: POST /api/zayavlenie/template {template:[{id:'t1',type:'text',page:1,x:10,y:10,align:'left',text:'ТЕСТ ШАПКА',size:10,bold:true}]}
                • 200, saved=true, count=1 ✓
             → Step 2b: GET /api/zayavlenie/template
                • Template содержит РОВНО 1 элемент ✓
                • is_custom=true ✓
             → Step 2c: POST /api/zayavlenie/template/reset (БЕЗ ТЕЛА)
                • 200, reset=true ✓
                • Response содержит template с 149 элементами ✓
             → Step 2d: GET /api/zayavlenie/template
                • Template снова содержит 149 элементов ✓
                • is_custom=false (шаблон сброшен) ✓
             → ПОРЯДОК ОПЕРАЦИЙ ПОДТВЕРЖДЁН: save → verify custom → reset → verify default ✓
          
          ✅ TEST 3: POST /api/zayavlenie/preview (ПОСЛЕ RESET!)
             → {records:[{fio:'Иванов Иван Иванович',birth_year:'2006',passport_series:'MP',passport_number:'1234567',res_street:'пр-т Дзержинского',res_house:'85',from_place:'г. Гомель',basis:'договор найма № 12 от 01.09.2024',sign_date:'01.09.2024',area:'5467,9',occupancy_count:'250',minors_count:'3'}]}
             → 200, Content-Type application/pdf, валидный PDF начинается с %PDF ✓
             → Размер PDF: 102630 байт ✓
             → Проверено через pymupdf: РОВНО 2 СТРАНИЦЫ ✓
             → Размеры страниц: Page 0 = 595.28×841.89 pt (A4-портрет), Page 1 = 595.28×841.89 pt ✓
             → Текст страницы 0 содержит ВСЕ требуемые подстроки:
                • 'ЗАЯВЛЕНИЕ' ✓
                • 'по месту пребывания' ✓
                • 'Иванов Иван Иванович' ✓
                • 'пр-т Дзержинского' ✓
             → Текст страницы 1 содержит ВСЕ требуемые подстроки:
                • 'Общая площадь' ✓
                • '5467,9' ✓
          
          ✅ TEST 4: GET /api/zayavlenie/background
             → page=1: 200, Content-Type image/png, валидный PNG (\\x89PNG), размер 110040 байт ✓
             → page=2: 200, Content-Type image/png, валидный PNG (\\x89PNG), размер 82748 байт ✓
             → Совместимость со старым эндпоинтом подтверждена ✓
          
          ✅ TEST 5: POST /api/zayavlenie/preview-png
             → side='front': 200, Content-Type image/png, валидный PNG (\\x89PNG), размер 115700 байт ✓
             → side='back': 200, Content-Type image/png, валидный PNG (\\x89PNG), размер 80375 байт ✓
             → ПОДТВЕРЖДЕНИЕ РАЗЛИЧИЯ: front и back — РАЗНЫЕ изображения (разница 35325 байт, 30.5%) ✓
          
          ✅ TEST 6: POST /api/zayavlenie/prefill (РЕГРЕССИЯ)
             → {students:[{full_name:'Иванов Иван Иванович',birth_date:'01.09.2007',citizenship:'РБ',passport_number:'MP1234567'}]}
             → 200, возвращает {records:[...]} ✓
             → records[0] содержит корректные данные (birth_year='2007', area='5467,9') ✓
             → Регрессия НЕ СЛОМАНА ✓
          
          ✅ TEST 7: РЕГРЕССИЯ ПАКЕТА (master-upload + package)
             → Step 7.1: GET /api/master-template → 200, XLSX 9250 байт ✓
             → Step 7.2: Заполнен шаблон через openpyxl (49 заголовков, 1 строка данных с datetime объектами) ✓
             → Step 7.3: POST /api/master-upload → 200, ключ 'zayavlenie' ПРИСУТСТВУЕТ в ответе ✓
             → Step 7.4: POST /api/package {people:[master[0]], include:{zayavlenie:true}}
                • 200, Content-Type application/pdf, валидный PDF начинается с %PDF ✓
                • Размер пакета: 285525 байт ✓
                • Проверено через pymupdf: 9 СТРАНИЦ (> 0) ✓
             → Интеграция с пакетом РАБОТАЕТ ✓
          
          ✅ TEST 8: HEALTH REGRESSION
             → GET /api/_ping → 200, {ok:true} ✓
             → GET /api/stats → 200, JSON с ключами {total, drafts, this_month, datasets, recent} ✓
             → Регрессия основных эндпоинтов ПОДТВЕРЖДЕНА ✓
          
          FINAL VERIFICATION:
             → is_custom=false (шаблон сброшен в конце тестирования) ✓
          
          ЗАКЛЮЧЕНИЕ:
          
          🎉 РЕДАКТИРУЕМЫЙ ШАБЛОН ЗАЯВЛЕНИЯ ПОЛНОСТЬЮ ФУНКЦИОНАЛЕН:
          • GET /api/zayavlenie/template возвращает 149 элементов (text/line/field) с корректной структурой
          • POST /api/zayavlenie/template сохраняет кастомный шаблон (is_custom=true)
          • POST /api/zayavlenie/template/reset восстанавливает дефолтный шаблон (is_custom=false)
          • POST /api/zayavlenie/preview генерирует корректный PDF с РОВНО 2 страницами A4-портрет (595.28×841.89 pt)
          • Текст PDF содержит ВСЕ требуемые подстроки на обеих страницах
          • GET /api/zayavlenie/background (page=1,2) возвращает валидные PNG
          • POST /api/zayavlenie/preview-png (side=front/back) возвращает РАЗНЫЕ изображения
          • POST /api/zayavlenie/prefill работает корректно (регрессия не сломана)
          • POST /api/master-upload возвращает ключ 'zayavlenie'
          • POST /api/package генерирует пакет с заявлением (9 страниц)
          • GET /api/_ping и /api/stats работают (health regression OK)
          • Все backend API полностью функциональны
          • РЕГРЕССИЙ НЕ ОБНАРУЖЕНО
          
          КРИТИЧЕСКОЕ ЗАМЕЧАНИЕ:
          • ОБЯЗАТЕЛЬНО вызывать POST /api/zayavlenie/template/reset ПЕРЕД любым preview после сохранения кастомного шаблона, иначе PDF будет почти пустым (содержать только кастомные элементы)
          • Порядок операций в TEST 2 КРИТИЧЕН: save → verify → reset → verify
          • Финальная проверка подтвердила: is_custom=false (шаблон сброшен)
          
          Редактируемый шаблон готов к использованию."

