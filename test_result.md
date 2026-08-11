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

frontend:
  - task: "DocumentEditor — двухпанельный редактор с живым PDF-предпросмотром, черновики, пресеты"
    implemented: true
    working: "NA"
    file: "components/DocumentEditor.js"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Не тестировать фронтенд без разрешения пользователя."
  - task: "История: фильтр статусов, бейджи, кнопка редактирования; Dashboard карточка черновиков; Settings демо+пресеты; дизайн-апгрейд"
    implemented: true
    working: "NA"
    file: "pages/History.js, pages/Dashboard.js, pages/Settings.js, index.css, components/Layout.js"
    stuck_count: 0
    priority: "medium"
    needs_retesting: false
    status_history:
        - working: "NA"
          agent: "main"
          comment: "Не тестировать фронтенд без разрешения пользователя."

metadata:
  created_by: "main_agent"
  version: "2.0"
  test_sequence: 1
  run_ui: false

test_plan:
  current_focus:
    - "LibreOffice восстановлен (soffice) для PDF-конвертации"
    - "Черновики: PUT /api/contracts/{id}, status в POST /api/contracts, фильтр GET /api/contracts?status="
    - "Пресеты полей: GET/POST/DELETE /api/presets"
    - "Демо-данные: POST /api/seed-demo (идемпотентно), DELETE /api/seed-demo"
    - "Stats обновлён: total=final only, +drafts"
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

