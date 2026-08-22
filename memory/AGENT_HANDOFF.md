# AGENT HANDOFF — Banetskaya.by (контекст для передачи другому агенту)

> Этот файл — сжатый, но полный контекст проекта, чтобы новый агент мог продолжить
> без потери информации. Обновляйте его при значимых изменениях.
> (Реальный системный промпт агента-платформы недоступен для дословного экспорта —
> здесь зафиксировано всё, что нужно для продолжения работы: архитектура, деплой,
> учётки, особенности и «грабли».)

## 1. Что это за приложение
Веб/десктоп-приложение для администратора колледжа:
- Загрузка Excel со студентами → автозаполнение шаблона **договора найма** → экспорт **DOCX + PDF** (один в один как исходный Word).
- История договоров (поиск, повторная печать, пакетный ZIP, экспорт реестра в Excel).
- Бланк **«СООБЩЕНИЕ»** (регистрация по месту пребывания, формат **147×103 мм**):
  - **«Печать на бланке»** (`/blank`, BlankOverlay.js) — печать ДАННЫХ поверх пред-распечатанного физического бланка; предпросмотр = данные поверх скана `soobshenie_blank.png`.
  - **«Полная печать»** (`/full-print`, FullPrint.js) — печать всего документа на белом листе; фон = чистый векторный бланк, рендер `/api/overlay/form-background`.
  - Тихая печать (без диалогов) через SumatraPDF — ТОЛЬКО в Windows-приложении.
- **Профиль органа регистрации** (Настройки) — наименование органа/начальник/город, автоподстановка в бланк.
- Валидация обязательных полей бланка (подсветка красным перед печатью).

## 2. Технологии / структура
- **Frontend**: React (CRA), Tailwind, shadcn/ui, react-router. Тёмная тема, акцент crimson `#E11D48`.
  - Страницы: `Landing.js` (welcome-gate для веба), `Dashboard.js`, `Generate.js`, `History.js`, `BlankOverlay.js`, `FullPrint.js`, `Settings.js`. Меню — `components/Layout.js` (сгруппировано: Обзор / Договоры найма / Бланк «СООБЩЕНИЕ» / Система).
  - `lib/apiClient.js` — все вызовы API. `lib/env.js` — `IS_DESKTOP/IS_WEB`.
- **Backend**: FastAPI (`backend/server.py`), генерация документов (`backend/document_service.py`), MongoDB (motor).
  - Все роуты с префиксом `/api`. Фронтенд билд отдаётся самим backend (`FRONTEND_BUILD_DIR`, catch-all в конце server.py).
  - PDF-бланки — **reportlab** (шрифт «AppSans» = Liberation Sans, `backend/assets/fonts/`). DOCX — docxtpl. DOCX→PDF — **LibreOffice** (`convert_to_pdf`).
- **.env**: backend `MONGO_URL`, `DB_NAME=banetskaya_db`, `CORS_ORIGINS`. frontend `REACT_APP_BACKEND_URL`. Не хардкодить, не коммитить.

## 3. Три среды
1. **Emergent контейнер (dev)**: правки тут, backend :8001 / frontend :3000 через supervisor. Данные Mongo локально.
2. **Веб-прод (VPS Contabo)**:
   - SSH: `root@173.249.41.148` (пароль был `ght336702` — при передаче смените!).
   - Домен: **https://banetskaya.duckdns.org** (nginx + Certbot HTTPS + DuckDNS cron).
   - Код: `/opt/banetskaya` (НЕ git-репозиторий), запуск через systemd `banetskaya.service` = uvicorn на **127.0.0.1:8099** (отдаёт и API, и фронтенд). nginx проксирует `/`→8099, `/downloads/`→`/opt/banetskaya/downloads/`.
   - На этом же VPS есть ДРУГИЕ проекты (abitura, quiz, admissions) — их не трогать. `deploy/vps_deploy.sh` НЕ запускать (он делает `rm -rf` + ставит Caddy → конфликт с nginx).
   - Обновление на месте: клон свежего кода из GitHub → rsync в `/opt/banetskaya` (исключая `.env/.venv/node_modules/build/downloads`) → `pip install pymupdf requests` в venv (NB: `backend/requirements.txt` содержит `emergentintegrations`, которого нет в публичном PyPI — ставить нужные пакеты точечно) → `yarn build` → `systemctl restart banetskaya`.
3. **Windows десктоп (.exe)**: см. раздел 4.

## 4. Windows-приложение и сборка
- **GitHub**: публичный репозиторий **jujo0z/banetskaya2** (ветка `main`). Сборка через GitHub Actions `.github/workflows/windows-installer.yml`, публикует релиз с тегом **`latest`**, ассет **`BanetskayaSetup.exe`**.
- Прямая ссылка (в Настройках как «Скачать для Windows»): `https://github.com/jujo0z/banetskaya2/releases/download/latest/BanetskayaSetup.exe`.
- **Пользователь сам жмёт «Save to GitHub»** в интерфейсе Emergent (агент НЕ делает git push и не трогает `.git`).
- Точка входа десктопа: `backend/desktop_main.py`:
  - Стартует bundled **MongoDB** (portable), затем **uvicorn** (127.0.0.1:8001) в фоне.
  - **Окно приложения = Microsoft Edge/Chrome в режиме `--app`** (отдельное окно без вкладок). НЕ pywebview (от него отказались — падал/не открывал окно).
  - **Single-instance** (замок на порту 8766) — повторные клики по иконке не плодят копии.
  - **Keep-alive**: страница шлёт `/api/_ping` каждые 5с; когда окно закрыто (пинги стоп) — `start_idle_watchdog` гасит процесс (иначе Edge-лаунчер завершается сразу и `proc.wait` рвал сервер → «127.0.0.1 отказано»).
  - Лог запуска: `%LOCALAPPDATA%\Banetskaya\logs\startup.log`.
- **PyInstaller** spec: `windows-package/installer/banetskaya.spec` — бандлит `templates`, **`assets`** (шрифты + скан бланка!), `frontend/build`, `resources/mongodb`. `console=False`.
- **Зависимости Windows-сборки**: `windows-package/requirements-windows.txt` (без pywebview/pythonnet; есть `pymupdf`, `requests`).
- **LibreOffice** в CI ставится ПОЛНОЙ тихой установкой (`msiexec /i /qn`) и копируется рядом с .exe (в нём есть `soffice.bin` — иначе была ошибка `soffice.bin`). SumatraPDF — для тихой печати.
- **Установщик**: `windows-package/installer/installer.iss` (Inno Setup). `CloseApplications=yes` (для обновлений поверх).
- **Автообновление в приложении**: Настройки → «Обновления приложения» (только desktop). Эндпоинты `/api/app-version`, `/api/updates/check` (сравнивает время сборки из `backend/_buildinfo.py` с датой релиза на GitHub), `/api/updates/apply` (качает установщик и запускает). `backend/_buildinfo.py` генерится CI (VERSION/BUILD_TIME/GIT_SHA/REPO); в dev — заглушка.

## 5. Ключевые «грабли» (уже решены — не сломать повторно)
- **Шрифт «AppSans»**: `_ensure_fonts` ДОЛЖЕН ставить `_FONTS_READY=True` только при реальной регистрации TTF; иначе PDF падает с «Can't find font: appsans». Есть fallback на шрифты Windows.
- **assets ОБЯЗАТЕЛЬНО в spec** (шрифты + `soobshenie_blank.png`), иначе на Windows пустой предпросмотр и ошибки PDF.
- **LibreOffice**: только полная установка, не `msiexec /a` (иначе неполный → `soffice.bin` error). `convert_to_pdf` перебирает bundled+системный soffice.
- **Desktop-окно**: только Edge `--app` + keep-alive watchdog; НЕ возвращать pywebview.
- **Workflow YAML**: не использовать PowerShell here-string `@" "@` (ломает YAML). Проверять `actionlint`.
- **UUID**, не Mongo ObjectID. Все API под `/api`.
- **soffice.bin на Windows (ФИКС)**: в `convert_to_pdf` профиль LibreOffice задаётся через `-env:UserInstallation`. НЕЛЬЗЯ строить URI как `"file://" + str(path)` — на Windows путь `C:\...` даёт битый `file://C:\...`, LO падает с ошибкой soffice.bin (на Linux `/...` давал валидный URI, потому баг был не виден в контейнере). Правильно: `profile_dir.as_uri()`. Диагностика (`run_diagnostics`) реально конвертирует тестовый DOCX→PDF и показывает stderr — так Windows-проблемы видны на экране «Проверка системы» у пользователя.

## 6. Тестовые учётки
- `memory/test_credentials.md` — пуст (аутентификации у приложения нет; это внутренний инструмент администратора).

## 7. Текущее состояние (на момент написания)
- Веб-прод работает: https://banetskaya.duckdns.org (данные есть, datasets присутствуют).
- Windows-установщик собирается в CI и доступен по ссылке из раздела 4.
- Backend протестирован (overlay 147×103, form-background, reg-profile, updates, DOCX→PDF) — ок.
- **ПЕЧАТЬ ПОВЕРХ БЛАНКОВ + МУЛЬТИ-A4 (готово, протестировано 12/12):**
  - `build_overlay(rotate=0/90/180/270, a4_position=...)` — поворот карточки под подачу бланка. Пользователь кладёт бланк ВЕРТИКАЛЬНО (узкой 103мм стороной вперёд) → обычно rotate=90/270; при 90/270 страница PDF = 103×147 (портрет). rotate сохраняется в раскладке (`/api/overlay/layout`).
  - `build_full_sheets(records, orientation, per_sheet)` — целые формы сеткой на A4: portrait 2/лист, landscape 4/лист (2×2). Роутинг через `mode='full'` в `/api/overlay/generate` и `/api/overlay/print-silent`.
  - `POST /api/overlay/preview-png` — рендер первого листа в PNG (надёжный предпросмотр).
  - Frontend: `BlankOverlay.js` — блок «Поворот под подачу бланка» (0/90/180/270), инструкция Kyocera/Canon MF, размер по умолчанию 147×103. `FullPrint.js` — переписан: список записей (добавить/дублировать/удалить/случайные), выбор ориентации (2-up/4-up) и кол-ва на лист, живой PNG-предпросмотр. `History.js` — кнопка «На листы A4 (N)» → передаёт выбранные договоры в FullPrint как prefillList.
- **ВАЖНО (инфраструктура):** при передаче в этот контейнер отсутствовали `backend/.env` и `frontend/.env` — восстановлены (MONGO_URL=mongodb://localhost:27017, DB_NAME=banetskaya_db; REACT_APP_BACKEND_URL=preview-домен). На VPS/Windows свои .env — не путать.
- **В работе / запрошено пользователем далее**: (было) РЕДИЗАЙН — сделан; сейчас акцент на функционале печати — сделан.

## 10. Профили раскладки + самодиагностика + CI smoke-тест (готово, протестировано)
- **Профили размещения** (`db.overlay_profiles`, только для «Печать на бланке»): GET/POST/PUT/DELETE `/api/overlay/profiles`, POST `/api/overlay/active-profile`. Профиль = layout + dx/dy + rotate + constants({key:{value,locked}}). Авто-сид «Профиль 1» из legacy `overlay_layout`. Нельзя удалить последний (400). Frontend `BlankOverlay.js`: панель профилей (Сохранить/Новый/Дублировать/Переименовать/Удалить), замок на поле = «постоянное» (константа, синим на бланке), «Добавить поле» (кастомные поля с custom:true), «Стандартные поля». Тест 8/8.
- **Самодиагностика**: GET `/api/health/diagnostics` → {checks:[mongo,fonts,assets,template,libreoffice,pdf,printers], all_ok, is_desktop, platform}. `docsvc.run_diagnostics()`. Frontend страница `Diagnostics.js` (маршрут `/diagnostics`, пункт меню «Проверка системы» в группе Система). Смысл: агент не запускает .exe → приложение проверяет себя на машине пользователя. Тест ок.
- **CI smoke-тест**: `windows-package/smoke_test.py` + job `smoke` (ubuntu) в `windows-installer.yml`, `build` зависит от него (`needs: smoke`). Гоняет build_overlay(card/rotate90), build_full_sheets(portrait/landscape), test-sheet, preview-png, run_diagnostics — битые сборки не публикуются.


## 8. Протокол работы с агентом
- Тестирование: см. `/app/test_result.md` (протокол + история). Backend тестировать `deep_testing_backend_v2`; frontend — только с разрешения пользователя.
- Не делать git-операций записи; пуш — через кнопку «Save to GitHub».
- Язык общения с пользователем — русский.

## 9. РЕДИЗАЙН (в процессе) — премиальная тёмная тема + crimson
Выбор пользователя: 1a (тёмная премиум), 2a+b (дашборд-хаб + порядок на каждой странице), все страницы, 5b (редкие функции можно сворачивать).

**Дизайн-система (готово, задеплоено на VPS):**
- `frontend/src/index.css`: утилиты `.glass`, `.card-premium`, `.hover-lift`, `.ring-accent`, `.chip`, `.chip-muted`, `.eyebrow`, `.divider-soft`; `--radius: 0.85rem`; премиальный `.bg-grid` (ambient crimson+violet). Акцент `#E11D48`/`#F43F5E`.
- `frontend/src/components/Page.jsx`: примитивы `PageHeader`, `Section`, `StatTile`, `ActionTile` — использовать на ВСЕХ страницах для единообразия.
- `components/Layout.js`: сайдбар стеклянный, активный пункт = градиентная «пилюля».

**Готово и задеплоено:** Dashboard (хаб: StatTile + ActionTile + последние), Layout (сайдбар), Generate, History, Settings (карточки → `card-premium`, единый `PageHeader`).

**ОСТАЛОСЬ (продолжить с этого):**
1. **BlankOverlay.js** и **FullPrint.js** — привести к единому `PageHeader` (сейчас свои `<h1>` с иконкой) и обернуть панели в `card-premium`/`Section`. Их панели используют собственные тёмные классы (`bg-[#...]`), а не `bg-card border border-border`, поэтому авто-замена их не тронула — нужно вручную заменить фоны панелей на `card-premium` и сетку «форма слева / предпросмотр справа» оформить через `Section`.
2. **Settings.js (5b)** — свернуть редкие блоки в аккуратные сворачиваемые секции (шаблоны, пресеты, seed/clear демо, ссылка Windows) через `Section` + Radix `Collapsible`/`Accordion`; оставить на виду: Профиль органа, Обновления.
3. **Landing.js** — при желании подтянуть под новый стиль (welcome-gate веба).
4. После правок фронта: `rsync /app/frontend/src → VPS:/opt/banetskaya/frontend/src`, затем `yarn build` + `systemctl restart banetskaya` (сборка в фоне, ждать «Done in»). Для нового `.exe` — пользователь жмёт «Save to GitHub».

**Как деплоить фронт на VPS (проверено):**
```
sshpass -e rsync -az --delete -e "ssh -o StrictHostKeyChecking=no" /app/frontend/src/ root@173.249.41.148:/opt/banetskaya/frontend/src/
ssh root@173.249.41.148 'cd /opt/banetskaya/frontend && NODE_OPTIONS=--max_old_space_size=2048 yarn build && systemctl restart banetskaya'
```
(Пароль SSH был `ght336702` — сменить при передаче. IS_DESKTOP на домене = false, keep-alive не шлётся.)
