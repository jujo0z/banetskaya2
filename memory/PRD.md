# PRD — Автозаполнение договора найма из Excel

## Original problem statement
Веб-приложение для администратора колледжа: загрузка Excel со студентами → автозаполнение шаблона договора найма → экспорт готового документа (Word .docx + PDF), один в один как в исходном Word. Все договоры сохраняются в историю. Функции: импорт .xlsx с авто-распознаванием колонок, просмотр/поиск студентов, автозаполнение, генерация docx+pdf, печать из браузера, пакетное формирование (ZIP), история с поиском и повторной печатью, ручная правка полей.

## User choices
- Шаблон: реальный .docx колледжа предоставлен (Белорусский гос. мед. колледж, г. Минск) — используется как есть с сохранением форматирования.
- Форматы выгрузки: Word (.docx) + PDF.
- Пакетный экспорт (ZIP): да.
- Вход по паролю: нет (один администратор).
- PDF: конвертация через LibreOffice (установлен на сервере).

## Architecture
- Frontend: React (JS), react-router, Shadcn UI, Tailwind, sonner. Swiss/high-contrast деловой UI на русском.
- Backend: FastAPI, все роуты с префиксом /api.
- DB: MongoDB (коллекции datasets, contracts), UUID id, ISO-строки дат.
- Документы: docxtpl рендерит {{jinja}}-плейсхолдеры в реальном .docx-шаблоне (формат сохраняется 1:1); PDF — LibreOffice headless.
- Шаблон: `/app/backend/templates/real_source.docx` (оригинал) → `prepare_template.py` вставляет плейсхолдеры → `contract_template.docx`.

## Contract fields (из Excel)
Номер договора, Дата подписания, Номер приказа, Дата приказа, Гражданство, ФИО, Дата рождения, Номер комнаты, Срок договора до, Адрес регистрации, Паспорт (номер/дата выдачи/срок действия/кем выдан), ИИН, Телефон. Константы (в шаблоне): текст договора, площадь 6.0 кв.м, реквизиты колледжа, директор Катова О.Н., начальник ОКЮР Астафьева О.Д.

## Implemented (2026-06)
- POST /api/upload — парсинг .xlsx (openpyxl), авто-маппинг всех 16 колонок по ключевым словам.
- GET /api/sample-template — скачивание образца Excel с нужными колонками.
- POST /api/contracts, /api/contracts/batch — сохранение в историю.
- GET /api/contracts (+?q=) — список с поиском по ФИО/номеру.
- GET /api/contracts/{id}/download?format=docx|pdf — генерация документа.
- POST /api/contracts/preview — генерация без сохранения.
- POST /api/contracts/batch-download — ZIP (docx/pdf).
- DELETE /api/contracts/{id}.
- Frontend: вкладка Генерация (загрузка, редактор маппинга, таблица студентов, поиск, мультивыбор, пакетное формирование ZIP, диалог ручной правки, печать), вкладка История (поиск, скачивание Word/PDF, печать, удаление, пакетный ZIP).
- Реальный .docx-шаблон колледжа: рендер проверен визуально — форматирование сохранено 1:1, все поля подставляются, лишних плейсхолдеров нет.
- Backend протестирован (13/13 pytest) и frontend e2e (100%).

## Implemented (2026-06, продолжение)
- Ребренд **Banetskaya.by** + полный тёмный премиум-редизайн (Cormorant Garamond заголовки, Manrope текст, crimson #E11D48, сайдбар-меню, glassmorphism).
- Дашборд со статистикой (/api/stats), Настройки, скачивание образца Excel (/api/sample-template).
- Просмотр документа в приложении (PDF в модалке + «В новой вкладке»).
- Пакетная печать: /api/contracts/batch-print — объединённый PDF (pypdf).
- Ручное поле «Дополнительно» (note) — условная строка в договоре.
- **Ручная модерация**: вкладка «Модерация пунктов» — 6 доп. полей (extra_subject/tenant/landlord/liability/term/other) вставляются в соответствующие разделы договора условно (пустые не меняют оригинал), сохраняются в истории. Тесты: 22/22 backend, frontend 100% (iteration_3).

## Backlog
- P2: генерация PDF пакета медленнее (LibreOffice per-doc) — можно кэшировать.
- P2: множественные шаблоны договоров / загрузка своего .docx через UI.
- P2: сохранение загруженного датасета между сессиями (сейчас держится в стейте фронта; dataset пишется в Mongo, но не подгружается автоматически).

## Implemented (2026-08, продолжение — редактор, черновики, пресеты, Windows)
- ВОССТАНОВЛЕНИЕ ОКРУЖЕНИЯ: пропали backend/.env и frontend/.env — восстановлены. LibreOffice (soffice) отсутствовал и не переживал перезапуск контейнера → добавлен в /app/.emergent/system_deps.txt (libreoffice-core/writer) для персистентности.
- BUGFIX «Не удалось обновить просмотр»: параллельный запуск soffice падал из-за общего профиля. Фикс — уникальный `-env:UserInstallation` профиль на каждый вызов + ретрай (document_service.py). На фронте авто-обновление превью только после реальной правки (устранён двойной запуск при открытии редактора). SOFFICE_BIN конфигурируется через env.
- НОВЫЙ РЕДАКТОР (components/DocumentEditor.js): двухпанельный — слева поля по группам (аккордеон) + «Пункты договора», справа живой PDF-предпросмотр (авто-дебаунс + «Обновить»). Кнопки Word/PDF/Печать, «Сохранить черновик», «Сохранить в историю». Используется в Генерации (новый) и Истории (правка существующего, PUT).
- ЧЕРНОВИКИ: Contract.status (final|draft) + updated_at. PUT /api/contracts/{id}. GET /api/contracts?status=. stats.total только final + stats.drafts. Фильтр-табы и бейджи в Истории. Карточка «Черновики» на дашборде.
- ПРЕСЕТЫ полей: коллекция presets, GET/POST/DELETE /api/presets. Управление в Настройках, применение/сохранение в редакторе.
- ДЕМО-ДАННЫЕ: POST /api/seed-demo (идемпотентно, флаг demo:true, 6 договоров = 4 final + 2 draft), DELETE /api/seed-demo. Кнопки в Настройках.
- ДИЗАЙН: градиентные акценты фона, свечение логотипа, премиум-карточки статистики, градиентный заголовок.
- WINDOWS-ПАКЕТ (/app/windows-package): setup.bat, start.bat, requirements-windows.txt (без облачных LLM-либ), README_WINDOWS.md, .env-примеры. Бэкенд может раздавать собранный фронтенд одним сервером (FastAPI serve_spa, активно только при наличии frontend/build — в облаке неактивно, ingress на :3000).
- Тесты: backend 29/29, frontend полностью (баг превью подтверждён исправленным). Шаблон .docx НЕ менялся.

## Implemented (2026-08 — Windows .exe установщик)
- Бэкенд адаптирован под PyInstaller frozen-режим: пути к шаблону (document_service._resource_base) и фронтенду (server FRONTEND_BUILD) учитывают sys._MEIPASS. В облаке поведение не изменилось (frozen=False, root=404, /api работает, PDF работает).
- backend/desktop_main.py — десктоп-точка входа: запускает встроенный mongod.exe (dbpath в %LOCALAPPDATA%\Banetskaya\data), авто-детект LibreOffice (soffice.exe), поднимает uvicorn на 127.0.0.1:8001 (FastAPI раздаёт статику фронтенда), открывает браузер.
- windows-package/installer/banetskaya.spec — PyInstaller onedir (datas: templates, frontend/build->frontend_build, resources/mongodb; hiddenimports для motor/uvicorn/docxtpl и т.д.).
- windows-package/installer/installer.iss — Inno Setup: единый BanetskayaSetup.exe, ярлыки, запуск после установки.
- .github/workflows/windows-installer.yml — GitHub Actions (windows-latest): yarn build → скачать mongod.exe → pyinstaller → Inno Setup → artifact BanetskayaSetup.exe. Пользователь скачивает готовый exe (Windows-ПК для сборки не нужен).
- Валидация в Linux: pyinstaller-сборка по спеке успешна; собранный бинарник запущен end-to-end (/api/ 200, раздача фронтенда 200, seed-demo 200) — логика упаковки корректна. Реальный Windows exe собирается на GitHub Actions (не проверялось в Linux — UNVERIFIED для Windows-специфики: mongod.exe/soffice).
- PDF/печать на Windows: требуется бесплатный LibreOffice (авто-детект), Word работает без него. БД — встроенная портативная MongoDB. Шаблон .docx НЕ менялся.

## Implemented (2026-08 — экспорт истории в Excel + брендинг установщика)
- ЭКСПОРТ: GET /api/contracts/export (?q=&status=) — единый .xlsx-реестр всех договоров (openpyxl): колонки №/Дата создания/Статус + все поля FIELDS, шапка с заливкой, автоширина, freeze_panes. Маршрут добавлен ДО /contracts/{id} (регрессия проверена). Фронт: кнопка «Экспорт в Excel» в Истории (учитывает поиск и фильтр статуса), apiClient.exportHistory. Backend протестирован (export + фильтры + порядок маршрутов OK). Фронт проверен скриншотом (кнопка + тост успеха).
- БРЕНДИНГ УСТАНОВЩИКА: windows-package/installer/assets/ (icon.ico мультиразмерный, wizard_large.bmp 164x314, wizard_small.bmp 55x58), генератор make_assets.py (Pillow). Дизайн: crimson-плитка, белый лист договора со сгибом + подпись-росчерк. Подключено: banetskaya.spec (EXE icon=icon.ico), installer.iss (SetupIconFile, WizardImageFile, WizardSmallImageFile, UninstallDisplayIcon, IconFilename ярлыков, копия icon.ico в {app}).
- LIBREOFFICE ПЕРСИСТЕНТНОСТЬ: подтверждено (troubleshoot_agent), что /app/.emergent/system_deps.txt — штатный механизм (init-контейнер восстанавливает пакеты при старте). Записи libreoffice-core/writer присутствуют в манифесте → soffice восстанавливается после перезапуска/деплоя. SOFFICE_BIN конфигурируем.
