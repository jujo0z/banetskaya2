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

## Implemented (2026-08 — ручная двусторонняя печать пачкой)
- Для принтеров без автодуплекса. POST /api/contracts/manual-duplex {ids, side: front|back, back_order: reversed|normal}. side=front -> нечётные страницы (1,3,5) всех выбранных договоров; side=back -> чётные (2,4,6); при reversed вся последовательность оборотов разворачивается (переворот всей стопки). Каждый документ дополняется пустой страницей при нечётном числе страниц (document_service.build_manual_duplex) — обороты не съезжают между документами.
- Фронт: ManualDuplexDialog (2 шага: Печать лицевых -> перевернуть стопку -> Печать оборотов, переключатель обратного порядка). Кнопка «Двусторонняя вручную» в Истории (выбранные) и в Генерации (сохраняет выбранных -> печать пачкой). apiClient.manualDuplexPrint.
- Тесты backend: 10/10 фича + регрессия 44/44 (front=6/back=6 для 3 договоров, ошибки 404, LibreOffice стабилен). Фронт проверен скриншотом (диалог открывается, интегрирован). Печать по своей природе ручная — авто-тест печати не выполняется.

## Implemented (2026-08 — duplex: диапазон, разделитель, пробный лист)
- ДИАПАЗОН N–M: в ManualDuplexDialog поля «Договоры с/по» — печать выбранной партии (срез ids на фронте), показывает «будет напечатано X из N».
- ЛИСТ-РАЗДЕЛИТЕЛЬ: параметр separators в POST /api/contracts/manual-duplex — вставляет пронумерованный лист-разделитель перед каждым договором (front=разделитель с № и данными, back=blank). Генерация reportlab; кириллица через забандленный Liberation Sans (backend/assets/fonts). Переключатель в диалоге.
- ПРОБНЫЙ ЛИСТ: GET /api/print-test?side=front|back — 1-страничный тест переворота с подсказками (ЛИЦЕВАЯ/ОБОРОТ, ВЕРХ ЛИСТА, инструкции). Кнопки «Пробная лицевая»/«Пробный оборот» в диалоге. apiClient.printDuplexTest.
- Зависимость reportlab==5.0.0 добавлена в requirements.txt и windows-package/requirements-windows.txt. Шрифты забандлены (кроссплатформенно для Windows-сборки).
- Тесты backend: 52/52 (print-test 1 стр; separators 6/6 для 2 док; без separators 4/4; регрессия чистая; soffice OK). Фронт проверен скриншотом.

## Implemented (2026-08 — duplex: гид, ориентация, self-heal)
- ПОШАГОВЫЙ ГИД в ManualDuplexDialog: стадии front -> flip -> done. Шаг 1 «Печать лицевых»; после — экран «Переверните стопку» с кнопкой «Шаг 2. Печать оборотов» + «Перепечатать лицевые»; после — «Партия напечатана» с «Следующая партия (t+1..N)» / «Начать заново». Настройки (диапазон/ориентация/разделители/реверс) блокируются после старта печати.
- ОРИЕНТАЦИЯ: параметр orientation (portrait|landscape) в POST /api/contracts/manual-duplex и GET /api/print-test. landscape поворачивает все выходные страницы на 90 (/Rotate=90), включая разделители. Селектор «Книжная (обычная)/Альбомная» в диалоге.
- РАЗДЕЛИТЕЛИ: переключатель (выбор включать/нет) — уже был, оставлен явным.
- SELF-HEAL soffice: @app.on_event('startup') — если на Linux нет soffice, фоновая доустановка LibreOffice (контейнер периодически пересоздаётся и стирает /usr; system_deps.txt восстанавливает не всегда). SOFFICE_BIN конфигурируем; на Windows пропускается.
- apiClient: manualDuplexPrint(ids, side, backReversed, separators, orientation); printDuplexTest(side, orientation).
- Тесты backend 16/16 (ориентация fronts/backs/separators, регрессия чистая). Фронт проверен скриншотами (гид: front->flip; селектор ориентации).

---

## Дополнение: Overlay-печать на готовом бланке (июль 2025)

Новый раздел «Печать на бланке» (сайдбар, роут /blank) — печать данных ПОВЕРХ уже
распечатанного бумажного бланка «СООБЩЕНИЕ» (регистрация по месту пребывания, РБ),
физический размер 147×103 мм (альбомная).

Backend (server.py + document_service.py, reportlab):
- GET /api/overlay/layout — раскладка 23 полей (x_pct/y_pct/font_pt) + калибровка dx_mm/dy_mm + page_mm; хранится в mongo app_settings key=overlay_layout, при отсутствии — дефолт SOOBSHENIE_LAYOUT.
- POST /api/overlay/layout — сохранить раскладку и калибровку (upsert).
- POST /api/overlay/generate — PDF 147×103мм только со значениями полей (with_background=true — с скан-подложкой для предпросмотра). Поддержка пакета (records[] → N страниц).
- GET /api/overlay/test-sheet?dx&dy — пробный лист выравнивания (кресты по углам, линейка 1см, центр-крест).
- GET /api/overlay/background — PNG скан-бланка (подложка редактора).

Frontend (pages/BlankOverlay.js):
- Визуальный редактор: скан-бланк как подложка, поверх — перетаскиваемые поля (drag → x_pct/y_pct), выбор поля, размер шрифта +/-.
- Ввод значений по группам, кнопка «Случайные данные» (тестовое заполнение, без подписи).
- Калибровка X/Y (мм), «Пробный лист», «Предпросмотр» (данные поверх бланка), «Печать» (только данные), «Сохранить» раскладку.

Статус: backend протестирован (83/83). Позиции полей — стартовые, донастраиваются перетаскиванием.
Данные пока вводятся вручную / случайные; интеграция с реальными студентами — следующий шаг (обсуждается).

---

## Дополнение 2: Стартовая страница + десктоп-упаковка (июль 2025)

- Стартовая страница `/welcome` (pages/Landing.js): сверху блок «Приложение для Windows» (кнопка «Скачать для Windows», REACT_APP_WINDOWS_DOWNLOAD_URL), снизу «Начать работу в браузере».
- Показывается ТОЛЬКО в веб-версии: EntryGate в App.js перекидывает `/` → `/welcome` (пока не нажали «Начать работу», флаг sessionStorage bnk_entered). Десктоп-сборка (lib/env.js: IS_DESKTOP по hostname 127.0.0.1/localhost или REACT_APP_IS_DESKTOP=1) стартовую страницу ПРОПУСКАЕТ.
- LibreOffice вшивается в установщик: .github/workflows/windows-installer.yml — admin-extract LibreOffice MSI в dist/Banetskaya/libreoffice (перед Inno); document_service._resolve_soffice() авто-находит вшитый soffice.exe рядом с приложением; frontend build получает REACT_APP_IS_DESKTOP=1.
- Проверка сборки .exe — на GitHub Actions (в облаке Linux Windows-сборку не проверить).

## Багфикс: десктоп всё равно уходил на /welcome (июль 2025)
Причина: детект десктопа полагался на hostname 127.0.0.1, что в собранном .exe срабатывало ненадёжно.
Фикс defense-in-depth: server.py (serve_spa) при sys.frozen инжектит <script>window.__IS_DESKTOP__=true</script> в index.html; frontend lib/env.js читает этот флаг первым. Веб-версия не меняется. Требует ПЕРЕСБОРКИ .exe. Frontend-тест 11/11 PASS.

## Фича: тихая печать бланка (десктоп, июль 2025)
GET /api/printers (список принтеров Windows, supported=false в вебе), POST /api/overlay/print-silent (генерит overlay-PDF и печатает через SumatraPDF -print-to ... -print-settings noscale -silent; fallback soffice --pt). В BlankOverlay.js — блок только для IS_DESKTOP: выбор принтера + кнопка "Печать на бланк (тихо, 100%)". SumatraPDF вшивается в установщик (workflow + installer.iss recursesubdirs). Backend-тест 7/7. Требует ПЕРЕСБОРКИ .exe.

## Фича: Форма 24 «Талон миграционного учёта к адресному листку прибытия» (июль 2025) — ГОТОВО (backend 13/13)
- Меню «Адресный листок» → «Талон учёта (Форма 24)» (роут /forma24, pages/Forma24.js — копия Forma19.js на эндпоинты forma24).
- Векторная отрисовка талона «П» (document_service._draw_forma24_front/_back, build_forma24) — та же геометрия, что Форма 19 (карта 105×145, сетка A4 2×2, 2 чел/лист × 2 копии, лицо+оборот). Одинаковый габарит сторон. Поля 1–17, объединённые блоки 5/9/10, поле даты вверху («Форма 24»).
- АВТО-ПОДЧЁРКИВАНИЕ выбранных вариантов (пол 1/2, цель приезда 1/2, образование 1..7, семейное положение 1..4, супруг 5/6) — по решению 3a пользователя.
- Эндпоинты /api/forma24/{fields,defaults(GET/POST),prefill,preview,preview-png(side)}. Отдельное хранилище forma24_defaults.
- Данные: как Форма 19 (Excel autofill + постоянные значения), предпросмотр лицо/оборот, Открыть/Скачать PDF.

## Фича: Форма 19 «Адресный листок прибытия» (июль 2025) — ГОТОВО (backend 7/7 + регрессия 3/3)
- Новый раздел меню «Адресный листок» → «Форма 19 (прибытие)» (роут /forma19, pages/Forma19.js).
- ПОЛНАЯ ВЕКТОРНАЯ ОТРИСОВКА обеих сторон бланка (document_service._draw_forma19_front/_back) в зоне 105×145 мм, ОДИНАКОВЫЙ габарит лицевой и оборотной (2..103 × 2..143 мм). Серые заливки label-ячеек, объединения (5/8/9 — merged left cell + sublabel col), 14 ячеек идент. номера — 1:1 с официальным бланком blanki.by. Кириллица через AppSans.
- build_forma19(people, duplex_flip): A4-сетка 2×2 = 2 человека/лист по 2 копии; порядок страниц лист-лицо/лист-оборот (дуплекс), duplex_flip=long|short меняет ряды оборота. Пунктирные линии реза.
- forma19_from_contract(): разбивает ФИО/дату рождения/паспорт студента на компоненты.
- Эндпоинты (/api): GET /forma19/fields, GET/POST /forma19/defaults (постоянные значения-константы в app_settings key=forma19_defaults), POST /forma19/prefill (students→records), POST /forma19/preview (PDF), POST /forma19/preview-png.
- Frontend Forma19.js: загрузка Excel (upload→map→prefill), панель «Постоянные значения» (сохраняются, применяются ко всем), список людей с групповой правкой полей, переключатель дуплекса, живой PNG-предпросмотр, Открыть/Скачать PDF.
- Отрисовка приведена под официальный эталон по фидбеку пользователя (серые ячейки, пропорции колонок, совпадение габаритов сторон).

## Фича: страница «Полная печать» (июль 2025)
Новый раздел в сайдбаре /full-print (pages/FullPrint.js), и в вебе, и в десктопе. Печатает ВЕСЬ документ на белом листе: бланк по скану (with_background=true) + данные, размер 147x103. Переиспользует сохранённую overlay-раскладку и поля. Веб: Предпросмотр/Открыть-Печать PDF/Скачать. Десктоп: выбор принтера + тихая печать (with_background). Backend: print-silent теперь уважает with_background; overlay/generate с фоном отдаёт валидный PDF (~1.1МБ). Overlay-печать (только данные) сохранена. Требует пересборки .exe для десктопа.

## Implemented (2026-08 — Заявление о регистрации по месту жительства)
- НОВЫЙ ДОКУМЕНТ: «Заявление о регистрации по месту жительства» — векторная отрисовка 1:1 (reportlab) по фото бланка (2 стр.). Раскладка: A4-ландшафт, 2 заявления A5 в ряд; лицо листа = стр.1 двух человек, оборот = стр.2 тех же (двусторонняя печать, duplex_flip long/short). Разрезав лист по центру — 2 готовых двусторонних заявления. Несколько человек = по 2 на лист.
- Автозаполнение стр.1 из единого шаблона «Данные» (master_to_zayavlenie): ФИО, паспорт (серия/№ разбиваются через _split_passport), кем/когда выдан, адрес (нас.пункт + ул/дом/корп/кв из res_*), «прибыл из» (from_*), основание (договор найма № … от …), дата; reg_who="одного", reg_count="1" по умолчанию.
- Стр.2 пустая для ручного заполнения, КРОМЕ общей площади = константа "5467,9" (ZAYAV_AREA_DEFAULT).
- Backend: document_service.py — ZAYAVLENIE_FIELDS/KEYS, _draw_zayavlenie_page1/page2, build_zayavlenie(). server.py — /api/zayavlenie/{fields,defaults(GET/POST),prefill,preview,preview-png}; ключ "zayavlenie" в /api/master-upload; ветка zayavlenie в _build_package_pdf (+ чекбокс include, включён по умолчанию).
- Frontend: pages/Zayavlenie.js (по образцу Forma24), lib/apiClient.js (zayavlenie* функции), маршрут /zayavlenie в App.js, пункт меню в Layout.js, чекбокс в Package.js.
- Тесты backend: 20/20 (100%) — эндпоинты, кол-во страниц PDF (2 для 1-2 чел., 4 для 3), разбивка паспорта, даты ДД.ММ.ГГГГ, интеграция master-upload и пакет.
- ДЕПЛОЙ на VPS (banetskaya.duckdns.org): backend-файлы + пересборка фронта (yarn build), systemctl restart banetskaya — проверено (API 200, UI живой). Бэкапы в /opt/banetskaya/_backup_*.

## Updated (2026-08 — Заявление: вариант ПО МЕСТУ ПРЕБЫВАНИЯ + Times New Roman)
- Заявление переделано 1:1 по фото blanki.by, вариант «о регистрации по месту ПРЕБЫВАНИЯ». Шрифт Times New Roman (Liberation Serif, зарегистрирован как AppSerif/-Bold/-Italic; helper _serif()).
- Блок «В орган внутренних дел…» — правое выравнивание; линии ФИО (2 уровня) и паспорта — под ним по ширине; «Прибыл(а) на {срок} из {место}»; «Вместе прибыли» — 5 линий с подписями снизу; основание ВСЕГДА «Договор найма № {номер} от {дата}»; стр.2 как на фото (площадь 5467,9).
- Новые поля: birth_year (год из birth_date), doc_name (по умолч. «паспорт гражданина Республики Беларусь»), stay_term (из колонки «Срок договора до» contract_end_date -> «срок до {дата}»).
- Тесты backend: 7/7 + регрессия 6/6 (100%). Задеплоено на VPS (backend-файлы + restart, фронт не пересобирался — поля динамические).
