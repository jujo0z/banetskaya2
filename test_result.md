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
  version: "2.4"
  test_sequence: 5
  run_ui: false

test_plan:
  current_focus: []
  stuck_tasks: []
  test_all: false
  test_priority: "high_first"

agent_communication:
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
