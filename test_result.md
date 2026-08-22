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
  - task: "Фикс ERR_CONNECTION_REFUSED в десктоп-окне: льготный период idle-watchdog + HTTP-readiness перед открытием окна"
    implemented: true
    working: "NA"
    file: "server.py, desktop_main.py"
    stuck_count: 0
    priority: "high"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "БАГ (пользователь): установленный .exe при запуске показывал «отказано в подключении» в окне Edge. startup.log ЗДОРОВЫЙ (Mongo up, server up, окно открыто) — значит сервер стартовал, но соединение отвергалось. RCA: idle-watchdog (start_idle_watchdog(30)) убивал процесс, если за 30с не пришёл keep-alive /api/_ping; при ПЕРВОМ запуске Edge с чистым профилем + медленный холодный старт (в логе даже import server занял ~30с) первый пинг от UI приходил ПОЗЖЕ 30с → сервер уже мёртв → refused. ФИКС: (1) server.start_idle_watchdog(timeout=30, initial_grace=180): пока не пришёл ПЕРВЫЙ пинг — ждём до initial_grace секунд (не убиваем); после первого пинга — обычный timeout 30с (быстрый выход при закрытии окна). Флаг _GOT_FIRST_PING в keepalive_ping. (2) desktop_main вызывает start_idle_watchdog(30, 240). (3) desktop_main: перед открытием окна wait_http_ready('/api/app-config') подтверждает, что HTTP реально отвечает (не только TCP-порт открыт); используется НЕ /_ping, чтобы readiness-проба не засчиталась как первый keep-alive. ПРОВЕРИТЬ (регрессия на Linux, сам Windows-баг тут не воспроизвести): (1) GET /api/_ping → 200 {ok:true} (несколько раз). (2) GET /api/health/diagnostics → 200 all_ok=true. (3) GET /api/overlay/profiles → 200. (4) GET /api/fields → 200 и POST /api/contracts/preview?format=pdf → 200 валидный PDF (не задето). (5) Импорт server.py без ошибок (бэкенд поднят). ПРИМЕЧАНИЕ: idle-watchdog на web/VPS НЕ активируется (arm только из desktop_main), поэтому на облаке поведение не меняется."

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
    working: "NA"
    file: "server.py"
    stuck_count: 0
    priority: "medium"
    needs_retesting: true
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Новый эндпоинт для ссылки на установщик Windows. GET /api/app-config → {windows_download_url:''} по умолчанию. POST /api/app-config {windows_download_url:'https://...'} → {saved:true, windows_download_url:'...'}, сохраняется в app_settings key=app_config (upsert), читается обратно через GET. Пустая строка также сохраняется. Проверить GET(default)→POST(set)→GET(persisted)→POST(clear)→GET(empty)."

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
  version: "2.6"
  test_sequence: 8
  run_ui: false

test_plan:
  current_focus:
    - "Фикс ERR_CONNECTION_REFUSED в десктоп-окне: льготный период idle-watchdog + HTTP-readiness перед открытием окна"
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
    - agent: "main"
      message: >
        НОВЫЙ ПРОГОН. Протестируй ТОЛЬКО backend, задачу «Фикс soffice.bin ... file:// URI профиля
        LibreOffice». Регрессия на Linux (Windows-баг тут не воспроизвести). 4 проверки: (1) GET
        /api/fields 200; (2) POST /api/contracts/preview?format=pdf с минимальными полями → 200
        валидный PDF с кириллицей (pymupdf, несколько страниц); (3) GET /api/health/diagnostics →
        checks[key=libreoffice].ok=true и detail начинается с 'OK', pdf.ok=true, all_ok=true; (4)
        POST /api/overlay/generate page_size=card → 200. Данные договоров/историю не ломать.
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

